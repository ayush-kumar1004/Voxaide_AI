import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.conversation import Conversation, Message
from app.core.database import get_firestore_client
from app.core.logging import logger

class ConversationService:
    """Manages multi-tenant conversation state, turn history, and messages."""

    def __init__(self):
        # Memory storage fallback for fast unit tests and decoupled execution
        self._conversations_mem: Dict[str, Dict[str, Any]] = {}
        self._messages_mem: Dict[str, List[Dict[str, Any]]] = {}

    def get_or_create_conversation(
        self,
        company_id: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        channel: str = "web_text"
    ) -> Conversation:
        if conversation_id:
            conv = self.get_conversation(company_id, conversation_id)
            if conv:
                return conv

        new_id = conversation_id or f"conv_{uuid.uuid4().hex[:10]}"
        conv = Conversation(
            id=new_id,
            company_id=company_id,
            user_id=user_id,
            channel=channel
        )

        db = get_firestore_client()
        if db:
            try:
                db.collection("conversations").document(new_id).set(conv.model_dump())
            except Exception as e:
                logger.error("Error saving conversation to Firestore", error=str(e))

        self._conversations_mem[new_id] = conv.model_dump()
        self._messages_mem[new_id] = []
        return conv

    def get_conversation(self, company_id: str, conversation_id: str) -> Optional[Conversation]:
        """Fetches conversation ensuring strict company_id isolation."""
        db = get_firestore_client()
        if db:
            try:
                doc = db.collection("conversations").document(conversation_id).get()
                if doc.exists:
                    data = doc.to_dict()
                    # Security: Enforce tenant ownership check
                    if data.get("company_id") != company_id:
                        logger.warning(
                            "Cross-tenant conversation access prevented",
                            requested_company_id=company_id,
                            actual_company_id=data.get("company_id")
                        )
                        return None
                    return Conversation(**data)
            except Exception as e:
                logger.error("Error fetching conversation from Firestore", error=str(e))

        if conversation_id in self._conversations_mem:
            data = self._conversations_mem[conversation_id]
            if data.get("company_id") != company_id:
                return None
            return Conversation(**data)

        return None

    def add_message(
        self,
        conversation_id: str,
        company_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            company_id=company_id,
            role=role,
            content=content,
            metadata=metadata or {}
        )

        db = get_firestore_client()
        if db:
            try:
                db.collection("conversations").document(conversation_id)\
                  .collection("messages").document(msg.id).set(msg.model_dump())
            except Exception as e:
                logger.error("Error saving message to Firestore", error=str(e))

        if conversation_id not in self._messages_mem:
            self._messages_mem[conversation_id] = []
        self._messages_mem[conversation_id].append(msg.model_dump())
        return msg

    def get_recent_messages(
        self,
        conversation_id: str,
        company_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieves recent turns formatted for prompt context with tenant validation."""
        # Verify conversation belongs to company
        conv = self.get_conversation(company_id, conversation_id)
        if not conv:
            return []

        db = get_firestore_client()
        if db:
            try:
                docs = db.collection("conversations").document(conversation_id)\
                         .collection("messages")\
                         .order_by("timestamp")\
                         .limit_to_last(limit).get()
                return [d.to_dict() for d in docs]
            except Exception as e:
                logger.error("Error fetching messages from Firestore", error=str(e))

        msgs = self._messages_mem.get(conversation_id, [])
        return msgs[-limit:]

    def list_conversations(self, company_id: str) -> List[Dict[str, Any]]:
        """Lists conversations belonging to a specific company tenant."""
        results = []
        for conv_id, data in self._conversations_mem.items():
            if data.get("company_id") == company_id:
                msgs = self._messages_mem.get(conv_id, [])
                last_msg = msgs[-1]["content"] if msgs else "No messages"
                user_name = data.get("user_id") or f"Guest-{conv_id[-4:]}"
                first_query = msgs[0]["content"] if msgs else "General inquiry"
                results.append({
                    "id": conv_id,
                    "company_id": company_id,
                    "customer": user_name,
                    "channel": data.get("channel", "web_text"),
                    "status": "Resolved" if len(msgs) > 1 else "Active",
                    "query": first_query,
                    "last_message": last_msg,
                    "message_count": len(msgs),
                    "date": (data.get("updated_at") or data.get("created_at") or "")[:10],
                    "duration": f"{max(1, len(msgs))} turns"
                })
        results.sort(key=lambda c: c.get("date", ""), reverse=True)
        return results

conversation_service = ConversationService()
