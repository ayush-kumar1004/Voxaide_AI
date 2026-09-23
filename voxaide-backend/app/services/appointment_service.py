import re
import uuid
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.models.appointment import Appointment, AppointmentStatus
from app.models.company import Company
from app.services.company_service import company_service
from app.core.database import get_firestore_client
from app.core.logging import logger

class AppointmentService:
    """
    Manages tenant-isolated appointment booking, business hours validation,
    collision detection, rescheduling, and cancellations.
    """

    def __init__(self, company_svc=None):
        self.company_svc = company_svc or company_service
        # In-memory store for offline/testing and fast lookup: {appointment_id: Appointment}
        self._appointments_mem: Dict[str, Appointment] = {}

    def _get_company(self, company_id: str) -> Company:
        company = self.company_svc.get_company(company_id)
        if not company:
            raise ValueError(f"Company '{company_id}' not found or inactive.")
        return company

    def _parse_time_str(self, time_str: str) -> Tuple[int, int]:
        """Parses times like '16:00', '4:00 PM', '4 PM', '09:30 AM' into (hour, minute)."""
        time_str = time_str.strip()
        
        # Check 12-hour format with AM/PM
        match_12 = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)$", time_str, re.IGNORECASE)
        if match_12:
            hour = int(match_12.group(1))
            minute = int(match_12.group(2) or 0)
            meridiem = match_12.group(3).lower()
            if meridiem == "pm" and hour != 12:
                hour += 12
            elif meridiem == "am" and hour == 12:
                hour = 0
            return hour, minute

        # Check 24-hour format HH:MM
        match_24 = re.match(r"^(\d{1,2}):(\d{2})$", time_str)
        if match_24:
            return int(match_24.group(1)), int(match_24.group(2))

        # Check simple hour '16' or '4'
        match_h = re.match(r"^(\d{1,2})$", time_str)
        if match_h:
            return int(match_h.group(1)), 0

        raise ValueError(f"Invalid time format '{time_str}'. Expected format like '16:00', '4:00 PM', or '10:30'.")

    def parse_datetime(self, date_str: str, time_str: str, tz_name: str = "UTC") -> datetime:
        """
        Parses date_str and time_str into a timezone-aware datetime.
        Supports 'YYYY-MM-DD', 'today', 'tomorrow', 'next monday', etc.
        """
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = ZoneInfo("UTC")

        now_in_tz = datetime.now(tz)
        clean_date = date_str.strip().lower()

        target_date = None
        if clean_date == "today":
            target_date = now_in_tz.date()
        elif clean_date == "tomorrow":
            target_date = (now_in_tz + timedelta(days=1)).date()
        else:
            # Try ISO standard YYYY-MM-DD
            try:
                target_date = datetime.strptime(clean_date, "%Y-%m-%d").date()
            except ValueError:
                # Try MM/DD/YYYY or DD-MM-YYYY
                for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%b %d, %Y", "%d %b %Y"):
                    try:
                        target_date = datetime.strptime(clean_date, fmt).date()
                        break
                    except ValueError:
                        continue

        if not target_date:
            raise ValueError(f"Invalid date format '{date_str}'. Expected 'YYYY-MM-DD', 'today', or 'tomorrow'.")

        hour, minute = self._parse_time_str(time_str)
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise ValueError(f"Invalid time value {hour:02d}:{minute:02d}.")

        return datetime(
            year=target_date.year,
            month=target_date.month,
            day=target_date.day,
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0,
            tzinfo=tz
        )

    def validate_business_hours(
        self,
        company: Company,
        start_dt: datetime,
        duration_minutes: int
    ) -> Tuple[bool, str]:
        """
        Validates whether the requested appointment fits within company business hours.
        """
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        weekday = start_dt.weekday()  # 0=Monday, 6=Sunday
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_name = day_names[weekday]

        hours_map = company.business_hours or {}
        
        # Determine operating hours for the given weekday
        day_key = day_name.lower()
        hours_str = None
        if day_key in hours_map:
            hours_str = hours_map[day_key]
        elif weekday < 5 and "monday_friday" in hours_map:
            hours_str = hours_map["monday_friday"]
        elif weekday == 5 and "saturday" in hours_map:
            hours_str = hours_map["saturday"]
        elif weekday == 6 and "sunday" in hours_map:
            hours_str = hours_map["sunday"]
        else:
            hours_str = hours_map.get("default", "09:00 - 18:00")

        if not hours_str or "closed" in hours_str.lower():
            return False, f"{company.name} is closed on {day_name}s."

        # Parse opening and closing hours, e.g. "09:00 - 18:00"
        match = re.match(r"^(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*-\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)$", hours_str, re.IGNORECASE)
        if not match:
            # If unrecognized format, default to open
            return True, ""

        open_h, open_m = self._parse_time_str(match.group(1))
        close_h, close_m = self._parse_time_str(match.group(2))

        open_dt = start_dt.replace(hour=open_h, minute=open_m, second=0, microsecond=0)
        close_dt = start_dt.replace(hour=close_h, minute=close_m, second=0, microsecond=0)

        if start_dt < open_dt:
            return False, f"Requested time {start_dt.strftime('%H:%M')} is before opening hours ({hours_str}) on {day_name}."

        if end_dt > close_dt:
            return False, f"Appointment ending at {end_dt.strftime('%H:%M')} exceeds closing hours ({hours_str}) on {day_name}."

        return True, ""

    def check_availability(
        self,
        company_id: str,
        date_str: str,
        time_str: str,
        duration_minutes: int = 30,
        service: str = "General Consultation"
    ) -> Dict[str, Any]:
        """
        Validates business hours, past date restrictions, and calendar conflicts for a slot.
        """
        company = self._get_company(company_id)
        tz_name = company.timezone or "UTC"

        try:
            start_dt = self.parse_datetime(date_str, time_str, tz_name)
        except ValueError as e:
            return {
                "available": False,
                "reason": str(e),
                "company_id": company_id
            }

        end_dt = start_dt + timedelta(minutes=duration_minutes)

        # 1. Check past date
        now = datetime.now(start_dt.tzinfo)
        if start_dt < now:
            return {
                "available": False,
                "reason": f"Cannot book appointment in the past. Requested time was {start_dt.isoformat()}, but current time is {now.isoformat()}.",
                "company_id": company_id
            }

        # 2. Check business hours
        is_open, bh_reason = self.validate_business_hours(company, start_dt, duration_minutes)
        if not is_open:
            return {
                "available": False,
                "reason": bh_reason,
                "company_id": company_id,
                "business_hours": company.business_hours
            }

        # 3. Check collision with existing scheduled appointments
        conflict = self._find_conflict(company_id, start_dt, end_dt)
        if conflict:
            alt_slots = self._find_alternative_slots(company, start_dt, duration_minutes)
            return {
                "available": False,
                "reason": f"Slot {start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')} is already booked for {service}.",
                "conflict_appointment_id": conflict.id,
                "suggested_alternatives": alt_slots,
                "company_id": company_id
            }

        return {
            "available": True,
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "timezone": tz_name,
            "service": service,
            "company_id": company_id,
            "message": f"Slot is available on {start_dt.strftime('%A, %B %d, %Y at %I:%M %p')} ({tz_name})."
        }

    def _find_conflict(
        self,
        company_id: str,
        start_dt: datetime,
        end_dt: datetime,
        exclude_id: Optional[str] = None
    ) -> Optional[Appointment]:
        """Finds any scheduled appointment for this company overlapping with [start_dt, end_dt)."""
        start_iso = start_dt.isoformat()
        end_iso = end_dt.isoformat()

        for appt in self._appointments_mem.values():
            if appt.company_id != company_id:
                continue
            if exclude_id and appt.id == exclude_id:
                continue
            if appt.status != AppointmentStatus.SCHEDULED:
                continue

            # Overlap check: appt.start < end_dt and start_dt < appt.end
            appt_start = datetime.fromisoformat(appt.start_time)
            appt_end = datetime.fromisoformat(appt.end_time)

            if appt_start < end_dt and start_dt < appt_end:
                return appt

        return None

    def _find_alternative_slots(
        self,
        company: Company,
        base_dt: datetime,
        duration_minutes: int,
        count: int = 3
    ) -> List[str]:
        """Finds the next available open slots after the conflict."""
        suggestions = []
        candidate = base_dt + timedelta(minutes=duration_minutes)
        attempts = 0

        while len(suggestions) < count and attempts < 12:
            attempts += 1
            cand_end = candidate + timedelta(minutes=duration_minutes)
            is_open, _ = self.validate_business_hours(company, candidate, duration_minutes)
            if is_open:
                conflict = self._find_conflict(company.id, candidate, cand_end)
                if not conflict:
                    suggestions.append(candidate.strftime("%I:%M %p"))
            candidate += timedelta(minutes=duration_minutes)

        return suggestions

    def book_appointment(
        self,
        company_id: str,
        customer_name: str,
        customer_phone: str,
        date_str: str,
        time_str: str,
        duration_minutes: int = 30,
        service: str = "General Consultation",
        customer_email: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Appointment:
        """
        Creates and stores a validated appointment with strict tenant isolation.
        """
        # Validate required fields
        if not customer_name or not customer_name.strip():
            raise ValueError("Customer name is required to book an appointment.")
        if not customer_phone or not customer_phone.strip():
            raise ValueError("Customer phone number is required to book an appointment.")

        company = self._get_company(company_id)
        tz_name = company.timezone or "UTC"

        start_dt = self.parse_datetime(date_str, time_str, tz_name)
        end_dt = start_dt + timedelta(minutes=duration_minutes)

        # Check availability
        avail = self.check_availability(
            company_id=company_id,
            date_str=date_str,
            time_str=time_str,
            duration_minutes=duration_minutes,
            service=service
        )
        if not avail.get("available"):
            raise ValueError(avail.get("reason", "Requested slot is not available."))

        appointment_id = f"apt_{uuid.uuid4().hex[:10]}"
        appointment = Appointment(
            id=appointment_id,
            company_id=company_id,
            customer_name=customer_name.strip(),
            customer_phone=customer_phone.strip(),
            customer_email=customer_email.strip() if customer_email else None,
            service=service.strip() if service else "General Consultation",
            start_time=start_dt.isoformat(),
            end_time=end_dt.isoformat(),
            timezone=tz_name,
            status=AppointmentStatus.SCHEDULED,
            notes=notes.strip() if notes else None,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat()
        )

        self._appointments_mem[appointment_id] = appointment

        # Firestore sync if available
        db = get_firestore_client()
        if db:
            try:
                db.collection("companies").document(company_id).collection("appointments").document(appointment_id).set(appointment.model_dump())
            except Exception as e:
                logger.error("Firestore appointment save failed", error=str(e), appointment_id=appointment_id)

        logger.info(
            "Appointment booked",
            company_id=company_id,
            appointment_id=appointment_id,
            start_time=appointment.start_time,
            customer_name=customer_name
        )

        return appointment

    def reschedule_appointment(
        self,
        company_id: str,
        appointment_id: str,
        new_date_str: str,
        new_time_str: str,
        duration_minutes: Optional[int] = None
    ) -> Appointment:
        """
        Reschedules an existing appointment to a new validated slot.
        Enforces that company_id matches the appointment's tenant.
        """
        appt = self._appointments_mem.get(appointment_id)
        if not appt or appt.company_id != company_id:
            raise ValueError(f"Appointment '{appointment_id}' not found for company '{company_id}'.")

        if appt.status == AppointmentStatus.CANCELLED:
            raise ValueError(f"Cannot reschedule appointment '{appointment_id}' because it was previously cancelled.")

        company = self._get_company(company_id)
        tz_name = appt.timezone or company.timezone or "UTC"

        new_start = self.parse_datetime(new_date_str, new_time_str, tz_name)
        
        # Determine duration
        if duration_minutes is None:
            old_start = datetime.fromisoformat(appt.start_time)
            old_end = datetime.fromisoformat(appt.end_time)
            duration_minutes = max(15, int((old_end - old_start).total_seconds() / 60))

        new_end = new_start + timedelta(minutes=duration_minutes)

        # Check past date
        now = datetime.now(new_start.tzinfo)
        if new_start < now:
            raise ValueError("Cannot reschedule an appointment into the past.")

        # Check business hours
        is_open, bh_reason = self.validate_business_hours(company, new_start, duration_minutes)
        if not is_open:
            raise ValueError(bh_reason)

        # Check conflict (excluding current appointment)
        conflict = self._find_conflict(company_id, new_start, new_end, exclude_id=appointment_id)
        if conflict:
            raise ValueError(f"Cannot reschedule: slot {new_start.strftime('%H:%M')} is already booked.")

        # Update
        appt.start_time = new_start.isoformat()
        appt.end_time = new_end.isoformat()
        appt.updated_at = datetime.now(timezone.utc).isoformat()

        logger.info(
            "Appointment rescheduled",
            company_id=company_id,
            appointment_id=appointment_id,
            new_start=appt.start_time
        )
        return appt

    def cancel_appointment(
        self,
        company_id: str,
        appointment_id: str,
        reason: Optional[str] = None
    ) -> Appointment:
        """
        Cancels an appointment and releases its slot.
        Enforces tenant isolation.
        """
        appt = self._appointments_mem.get(appointment_id)
        if not appt or appt.company_id != company_id:
            raise ValueError(f"Appointment '{appointment_id}' not found for company '{company_id}'.")

        if appt.status == AppointmentStatus.CANCELLED:
            return appt  # Idempotent cancel

        appt.status = AppointmentStatus.CANCELLED
        if reason:
            appt.notes = f"{appt.notes or ''} [Cancelled: {reason}]".strip()
        appt.updated_at = datetime.now(timezone.utc).isoformat()

        logger.info(
            "Appointment cancelled",
            company_id=company_id,
            appointment_id=appointment_id,
            reason=reason
        )
        return appt

    def get_appointment(self, company_id: str, appointment_id: str) -> Optional[Appointment]:
        """Tenant-isolated appointment lookup."""
        appt = self._appointments_mem.get(appointment_id)
        if appt and appt.company_id == company_id:
            return appt
        return None

    def list_appointments(
        self,
        company_id: str,
        date_str: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Appointment]:
        """Lists appointments for a company with optional date and status filters."""
        results = []
        for appt in self._appointments_mem.values():
            if appt.company_id != company_id:
                continue
            if status and appt.status.value != status:
                continue
            if date_str:
                appt_date = appt.start_time.split("T")[0]
                if appt_date != date_str:
                    continue
            results.append(appt)

        # Sort by start_time ascending
        results.sort(key=lambda a: a.start_time)
        return results

# Global appointment service instance
appointment_service = AppointmentService()
