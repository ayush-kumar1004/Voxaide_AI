from typing import Dict, Any, Optional
from app.tools.base import AgentTool, tool_registry
from app.services.appointment_service import appointment_service

class CheckAvailabilityTool(AgentTool):
    """Checks if a requested date and time slot is open for a service."""

    @property
    def name(self) -> str:
        return "check_availability"

    @property
    def description(self) -> str:
        return (
            "Checks if an appointment slot is available for booking. "
            "Use this whenever a customer asks if a time is available or wants to schedule an appointment. "
            "Provide the date (YYYY-MM-DD or 'tomorrow'/'today') and the time (e.g. '16:00', '4:00 PM', or '10:30 AM')."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format, or relative terms like 'today' or 'tomorrow'."
                },
                "time": {
                    "type": "string",
                    "description": "Time in 24h format (e.g. '16:00') or 12h format (e.g. '4:00 PM')."
                },
                "service": {
                    "type": "string",
                    "description": "The name or type of service requested (default: 'General Consultation')."
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Duration of the appointment in minutes (default: 30)."
                }
            },
            "required": ["date", "time"]
        }

    def execute(
        self,
        company_id: str,
        date: str,
        time: str,
        service: str = "General Consultation",
        duration_minutes: int = 30
    ) -> Dict[str, Any]:
        return appointment_service.check_availability(
            company_id=company_id,
            date_str=date,
            time_str=time,
            duration_minutes=duration_minutes,
            service=service
        )

class BookAppointmentTool(AgentTool):
    """Books an appointment for a customer."""

    @property
    def name(self) -> str:
        return "book_appointment"

    @property
    def description(self) -> str:
        return (
            "Books and confirms an appointment for a customer. "
            "Requires customer name, contact phone number, date, time, and service. "
            "The model must ONLY claim an appointment was booked if this tool returns success=True."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "Full name of the customer."
                },
                "customer_phone": {
                    "type": "string",
                    "description": "Phone number of the customer."
                },
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format, 'today', or 'tomorrow'."
                },
                "time": {
                    "type": "string",
                    "description": "Time in 24h format ('16:00') or 12h format ('4:00 PM')."
                },
                "service": {
                    "type": "string",
                    "description": "Name or type of service (default: 'General Consultation')."
                },
                "customer_email": {
                    "type": "string",
                    "description": "Customer email address for confirmation notifications."
                },
                "notes": {
                    "type": "string",
                    "description": "Any additional customer notes, symptoms, or requests."
                }
            },
            "required": ["customer_name", "customer_phone", "date", "time"]
        }

    def execute(
        self,
        company_id: str,
        customer_name: str,
        customer_phone: str,
        date: str,
        time: str,
        service: str = "General Consultation",
        customer_email: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        appt = appointment_service.book_appointment(
            company_id=company_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            date_str=date,
            time_str=time,
            service=service,
            customer_email=customer_email,
            notes=notes
        )
        return {
            "appointment_id": appt.id,
            "company_id": appt.company_id,
            "status": appt.status.value,
            "customer_name": appt.customer_name,
            "service": appt.service,
            "start_time": appt.start_time,
            "end_time": appt.end_time,
            "timezone": appt.timezone,
            "message": f"Appointment successfully scheduled for {appt.customer_name} on {appt.start_time}."
        }

class RescheduleAppointmentTool(AgentTool):
    """Reschedules an existing appointment to a new date and time."""

    @property
    def name(self) -> str:
        return "reschedule_appointment"

    @property
    def description(self) -> str:
        return (
            "Reschedules an existing appointment to a new date and time. "
            "Requires the appointment_id, new_date, and new_time."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "appointment_id": {
                    "type": "string",
                    "description": "The unique appointment ID to reschedule (e.g. 'apt_abc123')."
                },
                "new_date": {
                    "type": "string",
                    "description": "The new date in YYYY-MM-DD format, 'today', or 'tomorrow'."
                },
                "new_time": {
                    "type": "string",
                    "description": "The new time (e.g. '16:00' or '4:00 PM')."
                }
            },
            "required": ["appointment_id", "new_date", "new_time"]
        }

    def execute(
        self,
        company_id: str,
        appointment_id: str,
        new_date: str,
        new_time: str
    ) -> Dict[str, Any]:
        appt = appointment_service.reschedule_appointment(
            company_id=company_id,
            appointment_id=appointment_id,
            new_date_str=new_date,
            new_time_str=new_time
        )
        return {
            "appointment_id": appt.id,
            "status": appt.status.value,
            "new_start_time": appt.start_time,
            "new_end_time": appt.end_time,
            "timezone": appt.timezone,
            "message": f"Appointment {appt.id} successfully moved to {appt.start_time}."
        }

class CancelAppointmentTool(AgentTool):
    """Cancels an existing appointment."""

    @property
    def name(self) -> str:
        return "cancel_appointment"

    @property
    def description(self) -> str:
        return (
            "Cancels an existing appointment and releases its time slot. "
            "Requires the appointment_id and an optional reason."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "appointment_id": {
                    "type": "string",
                    "description": "The unique appointment ID to cancel (e.g. 'apt_abc123')."
                },
                "reason": {
                    "type": "string",
                    "description": "Optional reason for the cancellation."
                }
            },
            "required": ["appointment_id"]
        }

    def execute(
        self,
        company_id: str,
        appointment_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        appt = appointment_service.cancel_appointment(
            company_id=company_id,
            appointment_id=appointment_id,
            reason=reason
        )
        return {
            "appointment_id": appt.id,
            "status": appt.status.value,
            "message": f"Appointment {appt.id} has been cancelled."
        }

# Automatically register all business appointment tools
tool_registry.register(CheckAvailabilityTool())
tool_registry.register(BookAppointmentTool())
tool_registry.register(RescheduleAppointmentTool())
tool_registry.register(CancelAppointmentTool())
