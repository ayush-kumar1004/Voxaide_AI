from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class Appointment(BaseModel):
    """
    Core Appointment entity scoped strictly to a company tenant.
    """
    id: str
    company_id: str
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    service: str = "General Consultation"
    start_time: str  # ISO 8601 formatted string
    end_time: str    # ISO 8601 formatted string
    timezone: str = "UTC"
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
