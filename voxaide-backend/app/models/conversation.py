from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uuid

class Message(BaseModel):
    """A single turn within a conversation."""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    conversation_id: str
    company_id: str
    role: str  # user, assistant, tool, system
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Conversation(BaseModel):
    """A conversation session associated strictly with one company/tenant."""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    company_id: str
    user_id: Optional[str] = None
    channel: str = "web_text"  # web_text, web_voice, phone
    status: str = "active"  # active, completed, escalated
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    metadata: Dict[str, Any] = Field(default_factory=dict)
