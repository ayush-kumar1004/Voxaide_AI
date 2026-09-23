import os
import sys
import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["APP_ENV"] = "testing"

from app import app
from app.models.appointment import Appointment, AppointmentStatus
from app.services.company_service import company_service
from app.services.appointment_service import appointment_service
from app.services.agent_orchestrator import AgentOrchestrator, AgentRequest
from app.providers.base import LLMProvider, LLMResponse, ToolCallRequest
from app.tools.base import tool_registry

class MockLLM(LLMProvider):
    def __init__(self, content: str = "", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []
        self.last_prompt = ""

    def generate(self, prompt, system_instruction="", tools=None, history=None, temperature=0.3):
        self.last_prompt = prompt
        return LLMResponse(content=self.content, tool_calls=self.tool_calls)

@pytest.fixture(scope="module")
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

@pytest.fixture(scope="module")
def companies():
    """Create two isolated companies for testing."""
    c1 = company_service.create_company(
        name="Apex Dental Clinic",
        owner_user_id="user_apex_owner",
        timezone="UTC",
        business_hours={
            "monday_friday": "09:00 - 17:00",
            "saturday": "10:00 - 14:00",
            "sunday": "Closed"
        }
    )
    c2 = company_service.create_company(
        name="Zenith Auto Repairs",
        owner_user_id="user_zenith_owner",
        timezone="UTC",
        business_hours={
            "monday_friday": "08:00 - 18:00",
            "saturday": "Closed",
            "sunday": "Closed"
        }
    )
    return c1, c2

def get_future_business_day(days_ahead: int = 1, hour: int = 10, minute: int = 0) -> tuple[str, str]:
    """Helper to return a guaranteed weekday date (YYYY-MM-DD) and time string."""
    now = datetime.now(ZoneInfo("UTC"))
    target = now + timedelta(days=days_ahead)
    # Ensure it falls on a Monday-Friday (0-4)
    while target.weekday() >= 5:
        target += timedelta(days=1)
    return target.strftime("%Y-%m-%d"), f"{hour:02d}:{minute:02d}"

# ==============================================================================
# 1. BOOKING WITHIN BUSINESS HOURS
# ==============================================================================
def test_1_booking_within_business_hours(companies):
    c1, _ = companies
    date_str, time_str = get_future_business_day(days_ahead=2, hour=11, minute=0)

    appt = appointment_service.book_appointment(
        company_id=c1.id,
        customer_name="Alice Smith",
        customer_phone="+1234567890",
        date_str=date_str,
        time_str=time_str,
        service="Teeth Cleaning",
        duration_minutes=30
    )

    assert appt.id.startswith("apt_")
    assert appt.company_id == c1.id
    assert appt.customer_name == "Alice Smith"
    assert appt.customer_phone == "+1234567890"
    assert appt.service == "Teeth Cleaning"
    assert appt.status == AppointmentStatus.SCHEDULED
    assert appt.start_time.startswith(date_str)

# ==============================================================================
# 2. CANCELLATION
# ==============================================================================
def test_2_cancellation(companies):
    c1, _ = companies
    date_str, time_str = get_future_business_day(days_ahead=3, hour=14, minute=0)

    appt = appointment_service.book_appointment(
        company_id=c1.id,
        customer_name="Bob Jones",
        customer_phone="+1987654321",
        date_str=date_str,
        time_str=time_str,
        service="Consultation"
    )

    cancelled = appointment_service.cancel_appointment(
        company_id=c1.id,
        appointment_id=appt.id,
        reason="Schedule conflict"
    )

    assert cancelled.status == AppointmentStatus.CANCELLED
    assert "Schedule conflict" in (cancelled.notes or "")

    # Slot should now be available again
    avail = appointment_service.check_availability(
        company_id=c1.id,
        date_str=date_str,
        time_str=time_str
    )
    assert avail["available"] is True

# ==============================================================================
# 3. RESCHEDULING
# ==============================================================================
def test_3_rescheduling(companies):
    c1, _ = companies
    date1, time1 = get_future_business_day(days_ahead=4, hour=10, minute=0)
    date2, time2 = get_future_business_day(days_ahead=5, hour=15, minute=0)

    appt = appointment_service.book_appointment(
        company_id=c1.id,
        customer_name="Charlie Brown",
        customer_phone="+1122334455",
        date_str=date1,
        time_str=time1,
        service="Dental Checkup"
    )

    rescheduled = appointment_service.reschedule_appointment(
        company_id=c1.id,
        appointment_id=appt.id,
        new_date_str=date2,
        new_time_str=time2
    )

    assert rescheduled.status == AppointmentStatus.SCHEDULED
    assert rescheduled.start_time.startswith(date2)

    # Old slot should be free
    old_slot_avail = appointment_service.check_availability(
        company_id=c1.id,
        date_str=date1,
        time_str=time1
    )
    assert old_slot_avail["available"] is True

# ==============================================================================
# 4. UNAVAILABLE SLOTS: BUSINESS HOURS & DOUBLE BOOKING
# ==============================================================================
def test_4_unavailable_slots_outside_hours(companies):
    c1, _ = companies
    # 07:00 is before opening (09:00)
    date_str, _ = get_future_business_day(days_ahead=2)
    avail_early = appointment_service.check_availability(
        company_id=c1.id,
        date_str=date_str,
        time_str="07:00"
    )
    assert avail_early["available"] is False
    assert "before opening hours" in avail_early["reason"]

    # 19:00 is after closing (17:00)
    avail_late = appointment_service.check_availability(
        company_id=c1.id,
        date_str=date_str,
        time_str="19:00"
    )
    assert avail_late["available"] is False
    assert "exceeds closing hours" in avail_late["reason"]

def test_4b_unavailable_slots_closed_day(companies):
    c1, _ = companies
    # Find next Sunday
    now = datetime.now(ZoneInfo("UTC"))
    days_to_sunday = (6 - now.weekday()) % 7
    if days_to_sunday == 0:
        days_to_sunday = 7
    sunday = (now + timedelta(days=days_to_sunday)).strftime("%Y-%m-%d")

    avail_sunday = appointment_service.check_availability(
        company_id=c1.id,
        date_str=sunday,
        time_str="12:00"
    )
    assert avail_sunday["available"] is False
    assert "closed on Sundays" in avail_sunday["reason"]

def test_4c_double_booking_rejected(companies):
    c1, _ = companies
    date_str, time_str = get_future_business_day(days_ahead=6, hour=11, minute=0)

    # Book slot
    appointment_service.book_appointment(
        company_id=c1.id,
        customer_name="Customer 1",
        customer_phone="+1111111111",
        date_str=date_str,
        time_str=time_str
    )

    # Second booking at same slot must fail
    with pytest.raises(ValueError, match="already booked"):
        appointment_service.book_appointment(
            company_id=c1.id,
            customer_name="Customer 2",
            customer_phone="+2222222222",
            date_str=date_str,
            time_str=time_str
        )

# ==============================================================================
# 5. CROSS-TENANT ISOLATION
# ==============================================================================
def test_5_company_isolation(companies):
    c1, c2 = companies
    date_str, time_str = get_future_business_day(days_ahead=7, hour=12, minute=0)

    # Book under Company 1
    appt_c1 = appointment_service.book_appointment(
        company_id=c1.id,
        customer_name="Tenant 1 Client",
        customer_phone="+1000000001",
        date_str=date_str,
        time_str=time_str
    )

    # Company 2 cannot get Company 1's appointment
    assert appointment_service.get_appointment(c2.id, appt_c1.id) is None

    # Company 2 cannot cancel Company 1's appointment
    with pytest.raises(ValueError, match="not found"):
        appointment_service.cancel_appointment(c2.id, appt_c1.id)

    # Company 2 cannot reschedule Company 1's appointment
    with pytest.raises(ValueError, match="not found"):
        appointment_service.reschedule_appointment(c2.id, appt_c1.id, "2026-10-01", "10:00")

    # Company 1 booking does NOT block Company 2's schedule
    avail_c2 = appointment_service.check_availability(
        company_id=c2.id,
        date_str=date_str,
        time_str=time_str
    )
    assert avail_c2["available"] is True

# ==============================================================================
# 6. TOOL AUTHORIZATION & SPOOF DEFENSE
# ==============================================================================
def test_6_tool_authorization_ignores_spoofed_company_id(companies):
    c1, c2 = companies
    date_str, time_str = get_future_business_day(days_ahead=8, hour=10, minute=0)

    # Attacker tries to pass company_id=c2.id inside the tool arguments
    result = tool_registry.execute(
        name="book_appointment",
        company_id=c1.id,  # Authenticated context
        arguments={
            "company_id": c2.id,  # Spoofed argument
            "customer_name": "Spoofer",
            "customer_phone": "+9999999999",
            "date": date_str,
            "time": time_str,
            "service": "Dental"
        }
    )

    assert result["success"] is True
    # The booked appointment must be under c1.id, NOT c2.id
    booked_company = result["result"]["company_id"]
    assert booked_company == c1.id
    assert booked_company != c2.id

# ==============================================================================
# 7. FAILED BOOKING (PAST DATE & MISSING INFO)
# ==============================================================================
def test_7_failed_booking_past_date(companies):
    c1, _ = companies
    with pytest.raises(ValueError, match="Cannot book appointment in the past"):
        appointment_service.book_appointment(
            company_id=c1.id,
            customer_name="Past Client",
            customer_phone="+1112223333",
            date_str="2020-01-01",
            time_str="10:00"
        )

def test_7b_failed_booking_missing_customer_info(companies):
    c1, _ = companies
    date_str, time_str = get_future_business_day(days_ahead=2)
    with pytest.raises(ValueError, match="Customer name is required"):
        appointment_service.book_appointment(
            company_id=c1.id,
            customer_name="",
            customer_phone="+1112223333",
            date_str=date_str,
            time_str=time_str
        )

# ==============================================================================
# 8. AGENT ORCHESTRATOR BOOKS VIA TOOL
# ==============================================================================
def test_8_agent_orchestrator_books_appointment(companies):
    c1, _ = companies
    date_str, time_str = get_future_business_day(days_ahead=9, hour=15, minute=0)

    # Mock LLM calling book_appointment
    mock_llm = MockLLM(
        content="",
        tool_calls=[
            ToolCallRequest(
                name="book_appointment",
                arguments={
                    "customer_name": "Emma Watson",
                    "customer_phone": "+14155552671",
                    "date": date_str,
                    "time": time_str,
                    "service": "Teeth Whitening"
                }
            )
        ]
    )

    orchestrator = AgentOrchestrator(llm_provider=mock_llm)
    req = AgentRequest(
        company_id=c1.id,
        message=f"Please book an appointment for Emma Watson tomorrow at {time_str}"
    )

    res = orchestrator.process(req)

    assert len(res.tool_calls) == 1
    assert res.tool_calls[0]["name"] == "book_appointment"
    assert res.tool_calls[0]["result"]["success"] is True
    assert "apt_" in res.tool_calls[0]["result"]["result"]["appointment_id"]
    assert "successfully scheduled" in res.text

# ==============================================================================
# 9. MODEL CANNOT FABRICATE SUCCESS WHEN TOOL FAILS
# ==============================================================================
def test_9_model_cannot_fabricate_success(companies):
    c1, _ = companies
    # Try booking outside business hours (04:00 AM)
    date_str, _ = get_future_business_day(days_ahead=2)
    
    # Model pretends it booked the appointment even though tool fails
    mock_llm = MockLLM(
        content="I have booked your appointment for tomorrow at 4:00 AM!",
        tool_calls=[
            ToolCallRequest(
                name="book_appointment",
                arguments={
                    "customer_name": "Late Caller",
                    "customer_phone": "+12223334444",
                    "date": date_str,
                    "time": "04:00",
                    "service": "Emergency Dental"
                }
            )
        ]
    )

    orchestrator = AgentOrchestrator(llm_provider=mock_llm)
    req = AgentRequest(
        company_id=c1.id,
        message="Book me at 4 AM"
    )

    res = orchestrator.process(req)

    assert res.tool_calls[0]["result"]["success"] is False
    # Anti-fabrication check must intercept the fake confirmation!
    assert "have booked your appointment" not in res.text
    assert "could not book your appointment" in res.text or "outside business hours" in res.text

# ==============================================================================
# 10. HUMAN ESCALATION
# ==============================================================================
def test_10_human_escalation_trigger(companies):
    c1, _ = companies

    mock_llm = MockLLM(
        content="Connecting you with a representative right away.",
        tool_calls=[
            ToolCallRequest(
                name="escalate_to_human",
                arguments={
                    "reason": "Customer is extremely upset about previous bill",
                    "customer_phone": "+15551234567",
                    "urgency": "high"
                }
            )
        ]
    )

    orchestrator = AgentOrchestrator(llm_provider=mock_llm)
    req = AgentRequest(
        company_id=c1.id,
        message="I want to speak with a human manager immediately!"
    )

    res = orchestrator.process(req)

    assert res.should_escalate is True
    assert len(res.tool_calls) == 1
    assert res.tool_calls[0]["name"] == "escalate_to_human"
    assert res.tool_calls[0]["result"]["success"] is True
    assert "ESC-" in res.tool_calls[0]["result"]["result"]["escalation_ticket_id"]

# ==============================================================================
# 11. REST API ENDPOINTS
# ==============================================================================
def test_11_rest_api_appointments(client, companies):
    c1, _ = companies
    headers = {
        "Authorization": "Bearer mock_token",
        "X-Test-User-Id": c1.owner_user_id,
        "X-Company-ID": c1.id
    }

    date_str, time_str = get_future_business_day(days_ahead=10, hour=14, minute=0)

    # 1. Create via REST
    resp = client.post(
        f"/api/companies/{c1.id}/appointments",
        headers=headers,
        json={
            "customer_name": "API Tester",
            "customer_phone": "+18005551212",
            "date": date_str,
            "time": time_str,
            "service": "Consultation"
        }
    )
    assert resp.status_code == 201
    data = resp.get_json()
    appt_id = data["appointment"]["id"]

    # 2. List via REST
    list_resp = client.get(f"/api/companies/{c1.id}/appointments", headers=headers)
    assert list_resp.status_code == 200
    assert any(a["id"] == appt_id for a in list_resp.get_json()["appointments"])

    # 3. Cancel via REST
    cancel_resp = client.post(
        f"/api/companies/{c1.id}/appointments/{appt_id}/cancel",
        headers=headers,
        json={"reason": "Customer cancelled via app"}
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.get_json()["appointment"]["status"] == "cancelled"
