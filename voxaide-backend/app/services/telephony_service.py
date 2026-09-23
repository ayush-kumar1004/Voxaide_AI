import os
import uuid
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.services.company_service import company_service
from app.services.audio_service import audio_service
from app.core.database import get_firestore_client
from app.core.logging import logger

class TelephonyService:
    """
    Manages telephony phone numbers, TwiML generation, and call logging.
    Strictly tenant-scoped by company_id.
    """

    def __init__(self):
        # In-memory storage for phone number routing and call logs
        self._phone_numbers: Dict[str, Dict[str, Any]] = {}  # {phone_number: {company_id, ...}}
        self._call_logs: Dict[str, Dict[str, Any]] = {}       # {call_sid: CallRecord}

    def register_phone_number(
        self,
        company_id: str,
        phone_number: str,
        label: str = "Main Support Line",
        provider: str = "twilio"
    ) -> Dict[str, Any]:
        """Maps a virtual telephone number to a company tenant."""
        clean_number = phone_number.strip().replace(" ", "").replace("-", "")
        record = {
            "id": f"num_{uuid.uuid4().hex[:8]}",
            "company_id": company_id,
            "phone_number": clean_number,
            "label": label,
            "provider": provider,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self._phone_numbers[clean_number] = record

        # Sync with Firestore if available
        db = get_firestore_client()
        if db:
            try:
                db.collection("companies").document(company_id).collection("phone_numbers").document(record["id"]).set(record)
            except Exception as e:
                logger.error("Firestore phone number save failed", error=str(e))

        logger.info("Registered phone number for company", company_id=company_id, phone_number=clean_number)
        return record

    def get_company_for_phone_number(self, phone_number: str) -> Optional[str]:
        """Resolves the company_id assigned to an incoming phone number."""
        clean_number = phone_number.strip().replace(" ", "").replace("-", "")
        record = self._phone_numbers.get(clean_number)
        if record:
            return record.get("company_id")
        return None

    def list_phone_numbers(self, company_id: str) -> List[Dict[str, Any]]:
        """Lists all phone numbers assigned to a company."""
        return [n for n in self._phone_numbers.values() if n.get("company_id") == company_id]

    def record_call_start(
        self,
        call_sid: str,
        company_id: str,
        from_number: str,
        to_number: str,
        direction: str = "inbound"
    ) -> Dict[str, Any]:
        """Records initiation of a voice call."""
        record = {
            "call_sid": call_sid,
            "company_id": company_id,
            "from_number": from_number,
            "to_number": to_number,
            "direction": direction,
            "status": "in-progress",
            "duration_seconds": 0,
            "turns": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        self._call_logs[call_sid] = record
        return record

    def record_call_turn(self, call_sid: str, user_text: str, assistant_text: str):
        """Appends a conversational turn to a call record."""
        record = self._call_logs.get(call_sid)
        if record:
            now_iso = datetime.now(timezone.utc).isoformat()
            record["turns"].append({"role": "user", "text": user_text, "timestamp": now_iso})
            record["turns"].append({"role": "assistant", "text": assistant_text, "timestamp": now_iso})
            record["updated_at"] = now_iso

    def record_call_end(self, call_sid: str, duration_seconds: int = 0, status: str = "completed"):
        """Finalizes a call log upon hangup or status callback."""
        record = self._call_logs.get(call_sid)
        if record:
            record["duration_seconds"] = duration_seconds
            record["status"] = status
            record["updated_at"] = datetime.now(timezone.utc).isoformat()

            db = get_firestore_client()
            if db:
                try:
                    db.collection("companies").document(record["company_id"]).collection("call_logs").document(call_sid).set(record)
                except Exception as e:
                    logger.error("Firestore call log save failed", error=str(e), call_sid=call_sid)

    def list_call_logs(self, company_id: str) -> List[Dict[str, Any]]:
        """Lists call logs for a company."""
        calls = [c for c in self._call_logs.values() if c.get("company_id") == company_id]
        calls.sort(key=lambda c: c.get("created_at", ""), reverse=True)
        return calls

    def generate_twiml_greeting(self, company_id: str, host_url: str) -> str:
        """
        Generates initial TwiML XML for an inbound call.
        Greets the caller and presents a Speech <Gather>.
        """
        company = company_service.get_company(company_id)
        config = company_service.get_agent_config(company_id)

        greeting = config.greeting if config else f"Welcome to {company.name if company else 'VoxAide'}. How may I help you today?"
        gather_action = f"{host_url.rstrip('/')}/api/telephony/voice/gather?company_id={company_id}"

        response = ET.Element("Response")
        gather = ET.SubElement(
            response,
            "Gather",
            input="speech",
            action=gather_action,
            method="POST",
            speechTimeout="auto",
            language="en-US"
        )
        say = ET.SubElement(gather, "Say", voice="Polly.Joanna-Neural")
        say.text = greeting

        # Fallback if no speech detected
        fallback_say = ET.SubElement(response, "Say")
        fallback_say.text = "We did not receive any input. Goodbye!"
        ET.SubElement(response, "Hangup")

        return ET.tostring(response, encoding="utf-8", method="xml").decode("utf-8")

    def generate_twiml_turn(
        self,
        reply_text: str,
        company_id: str,
        host_url: str,
        should_hangup: bool = False
    ) -> str:
        """
        Generates conversational turn TwiML: speaks the agent's reply,
        and if call is continuing, presents the next <Gather>.
        """
        response = ET.Element("Response")
        gather_action = f"{host_url.rstrip('/')}/api/telephony/voice/gather?company_id={company_id}"

        if should_hangup:
            say = ET.SubElement(response, "Say", voice="Polly.Joanna-Neural")
            say.text = reply_text
            ET.SubElement(response, "Hangup")
        else:
            gather = ET.SubElement(
                response,
                "Gather",
                input="speech",
                action=gather_action,
                method="POST",
                speechTimeout="auto",
                language="en-US"
            )
            say = ET.SubElement(gather, "Say", voice="Polly.Joanna-Neural")
            say.text = reply_text

            # If user remains silent after prompt
            retry_say = ET.SubElement(response, "Say", voice="Polly.Joanna-Neural")
            retry_say.text = "Are you still there? If you need more assistance, feel free to speak or call back anytime. Thank you!"
            ET.SubElement(response, "Hangup")

        return ET.tostring(response, encoding="utf-8", method="xml").decode("utf-8")

# Global telephony service instance
telephony_service = TelephonyService()
