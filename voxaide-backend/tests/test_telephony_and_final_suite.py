import os
import sys
import json
import pytest
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["APP_ENV"] = "testing"

from app import app
from app.services.company_service import company_service
from app.services.telephony_service import telephony_service
from app.services.audio_service import audio_service
from app.services.conversation_service import conversation_service
from app.services.appointment_service import appointment_service
from app.providers.base import LLMProvider, LLMResponse, ToolCallRequest

class TelephonyMockLLM(LLMProvider):
    def __init__(self, content: str = "", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []

    def generate(self, prompt, system_instruction="", tools=None, history=None, temperature=0.3):
        return LLMResponse(content=self.content, tool_calls=self.tool_calls)

@pytest.fixture(scope="module")
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

@pytest.fixture(scope="module")
def telephony_tenants():
    c1 = company_service.create_company(
        name="Beacon Medical",
        owner_user_id="user_beacon_admin",
        phone_number="+14155552671",
        business_hours={"monday_friday": "09:00 - 17:00", "saturday": "Closed", "sunday": "Closed"}
    )
    c2 = company_service.create_company(
        name="Nova Logistics",
        owner_user_id="user_nova_admin",
        phone_number="+14155559999"
    )
    # Register telephone numbers in telephony service
    telephony_service.register_phone_number(c1.id, "+14155552671", label="Beacon Line")
    telephony_service.register_phone_number(c2.id, "+14155559999", label="Nova Line")
    return c1, c2

def test_1_phone_number_lookup(telephony_tenants):
    c1, c2 = telephony_tenants
    assert telephony_service.get_company_for_phone_number("+14155552671") == c1.id
    assert telephony_service.get_company_for_phone_number("+14155559999") == c2.id
    assert telephony_service.get_company_for_phone_number("+19999999999") is None

def test_2_inbound_call_twiml(client, telephony_tenants):
    c1, _ = telephony_tenants
    res = client.post(
        "/api/telephony/voice/inbound",
        data={
            "From": "+16505551234",
            "To": "+14155552671",
            "CallSid": "CA123456789"
        }
    )
    assert res.status_code == 200
    assert "text/xml" in res.content_type
    xml_str = res.data.decode("utf-8")
    
    # Parse TwiML XML
    root = ET.fromstring(xml_str)
    assert root.tag == "Response"
    gather = root.find("Gather")
    assert gather is not None
    assert f"company_id={c1.id}" in gather.attrib.get("action", "")
    say = gather.find("Say")
    assert say is not None
    assert len(say.text) > 0

def test_3_voice_gather_processes_speech(client, telephony_tenants):
    c1, _ = telephony_tenants
    res = client.post(
        f"/api/telephony/voice/gather?company_id={c1.id}",
        data={
            "CallSid": "CA123456789",
            "From": "+16505551234",
            "SpeechResult": "What are your business hours?"
        }
    )
    assert res.status_code == 200
    xml_str = res.data.decode("utf-8")
    root = ET.fromstring(xml_str)
    assert root.tag == "Response"
    # Should have a Gather with Say or Say with answer
    say = root.find(".//Say")
    assert say is not None
    assert len(say.text) > 0

def test_4_call_status_callback(client):
    res = client.post(
        "/api/telephony/voice/status",
        data={
            "CallSid": "CA123456789",
            "CallDuration": "45",
            "CallStatus": "completed"
        }
    )
    assert res.status_code == 200
    log = telephony_service._call_logs.get("CA123456789")
    assert log is not None
    assert log["duration_seconds"] == 45
    assert log["status"] == "completed"

def test_5_conversations_api(client, telephony_tenants):
    c1, _ = telephony_tenants
    headers = {
        "Authorization": "Bearer mock_token",
        "X-Test-User-Id": c1.owner_user_id,
        "X-Company-ID": c1.id
    }
    # Create conversation
    conv = conversation_service.get_or_create_conversation(c1.id, user_id="user_test_caller")
    conversation_service.add_message(conv.id, c1.id, role="user", content="Hello, I need pricing information.")
    conversation_service.add_message(conv.id, c1.id, role="assistant", content="Here is our standard pricing.")

    res = client.get(f"/api/companies/{c1.id}/conversations", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert "conversations" in data
    assert any(c["id"] == conv.id for c in data["conversations"])

def test_6_analytics_api(client, telephony_tenants):
    c1, _ = telephony_tenants
    headers = {
        "Authorization": "Bearer mock_token",
        "X-Test-User-Id": c1.owner_user_id,
        "X-Company-ID": c1.id
    }
    res = client.get(f"/api/companies/{c1.id}/analytics", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert "total_queries" in data
    assert "resolution_rate" in data
    assert "appointments_scheduled" in data
    assert "categories" in data

def test_7_audio_service_synthesize():
    # Verify synthesize_to_file handles empty and valid strings safely
    assert audio_service.synthesize_to_file("") is None
    filepath = audio_service.synthesize_to_file("Testing audio service synthesis.")
    assert filepath is not None
    assert os.path.exists(filepath)
    # Clean up test audio file
    try:
        os.remove(filepath)
    except Exception:
        pass

def test_8_company_agent_chat_api(client, telephony_tenants):
    c1, _ = telephony_tenants
    headers = {
        "Authorization": "Bearer mock_token",
        "X-Test-User-Id": c1.owner_user_id,
        "X-Company-ID": c1.id
    }
    res = client.post(
        f"/api/agent/companies/{c1.id}/agent/chat",
        headers=headers,
        json={
            "message": "Hello, what services does Beacon Medical offer?",
            "synthesize_audio": False
        }
    )
    assert res.status_code == 200
    data = res.get_json()
    assert "response" in data
    assert "conversation_id" in data
    assert "latency_ms" in data
