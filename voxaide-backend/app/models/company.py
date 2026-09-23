from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

class AgentConfig(BaseModel):
    """Configuration for a company's customer-support AI agent."""
    company_id: str
    agent_name: str = "Support Assistant"
    system_instructions: str = (
        "You are a helpful, professional, and knowledgeable AI customer-support assistant. "
        "Answer caller inquiries using only verified company information. If information is unavailable, "
        "politely state that you do not have that information."
    )
    greeting: str = "Hello! How can I assist you today?"
    personality: str = "professional and friendly"
    language: str = "English"
    supported_languages: List[str] = Field(default_factory=lambda: ["English", "Hindi"])
    business_hours: Dict[str, str] = Field(default_factory=lambda: {
        "monday_friday": "09:00 - 18:00",
        "saturday": "10:00 - 14:00",
        "sunday": "Closed"
    })
    escalation_enabled: bool = True
    escalation_message: str = (
        "I'd be glad to connect you with a human representative or schedule a callback for you."
    )
    max_context_turns: int = 10
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CompanyMember(BaseModel):
    """Membership mapping an authenticated user to a company with a role."""
    company_id: str
    user_id: str
    role: str = "owner"  # owner, admin, viewer
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Company(BaseModel):
    """Core multi-tenant company entity."""
    id: str
    name: str
    slug: str
    description: Optional[str] = ""
    industry: Optional[str] = "General"
    logo_url: Optional[str] = None
    timezone: str = "Asia/Kolkata"
    phone_number: Optional[str] = None
    business_hours: Dict[str, str] = Field(default_factory=lambda: {
        "monday_friday": "09:00 - 18:00",
        "saturday": "10:00 - 14:00",
        "sunday": "Closed"
    })
    contact_email: Optional[str] = None
    owner_user_id: str
    status: str = "active"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
