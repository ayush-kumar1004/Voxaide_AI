import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone
from app.tools.base import AgentTool, tool_registry
from app.core.database import get_firestore_client
from app.core.logging import logger

class EscalateToHumanTool(AgentTool):
    """Tool triggered when customer asks for human agent or has an unresolved emergency."""

    def __init__(self):
        # In-memory escalation store for offline execution and fast testing
        self._escalations_mem: Dict[str, Dict[str, Any]] = {}

    @property
    def name(self) -> str:
        return "escalate_to_human"

    @property
    def description(self) -> str:
        return (
            "Escalates the call or conversation to a human support agent or creates an urgent callback request. "
            "Use when customer explicitly asks for a human, when a query cannot be answered, for sensitive complaints, "
            "unsupported requests, or when a tool fails requiring human intervention."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Summary of the customer's issue requiring human escalation"
                },
                "customer_phone": {
                    "type": "string",
                    "description": "Customer contact phone number for callback if provided"
                },
                "urgency": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "description": "Urgency level of the issue"
                }
            },
            "required": ["reason"]
        }

    def execute(self, company_id: str, reason: str, customer_phone: str = "", urgency: str = "medium") -> Dict[str, Any]:
        ticket_id = f"ESC-{company_id[:6].upper()}-{uuid.uuid4().hex[:6].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        record = {
            "escalation_ticket_id": ticket_id,
            "company_id": company_id,
            "status": "queued_for_agent",
            "reason": reason,
            "customer_phone": customer_phone,
            "urgency": urgency,
            "created_at": now_iso,
            "message": f"A human support representative for company '{company_id}' will follow up regarding: {reason}."
        }

        self._escalations_mem[ticket_id] = record

        db = get_firestore_client()
        if db:
            try:
                db.collection("companies").document(company_id).collection("escalations").document(ticket_id).set(record)
            except Exception as e:
                logger.error("Firestore escalation record failed", error=str(e), ticket_id=ticket_id)

        logger.info(
            "Human escalation recorded",
            company_id=company_id,
            ticket_id=ticket_id,
            reason=reason,
            urgency=urgency
        )

        return record

    def list_escalations(self, company_id: str) -> List[Dict[str, Any]]:
        """List escalation tickets for a specific tenant."""
        return [e for e in self._escalations_mem.values() if e.get("company_id") == company_id]

# Register the escalation tool by default
escalate_tool_instance = EscalateToHumanTool()
tool_registry.register(escalate_tool_instance)
