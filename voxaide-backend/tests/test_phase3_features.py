import json
import pytest
from app import create_app
from app.services.company_service import company_service

@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers():
    return {
        "Authorization": "Bearer dev_token_demo_company",
        "X-Company-ID": "demo_company",
        "Content-Type": "application/json"
    }

def test_telephony_stream_twiml(client):
    """Verifies that inbound calls requesting stream mode return Twilio Stream TwiML."""
    res = client.get("/api/telephony/voice/inbound?company_id=demo_company&stream=true")
    assert res.status_code == 200
    assert "Stream" in res.data.decode("utf-8")
    assert "wss://" in res.data.decode("utf-8")

def test_simulate_phone_call(client, auth_headers):
    """Verifies that simulated phone calls process through the agent orchestrator and log turns."""
    payload = {
        "message": "Where is my order #ZMT-8492?",
        "caller_phone": "+15551234567"
    }
    res = client.post(
        "/api/companies/demo_company/telephony/simulate-call",
        headers=auth_headers,
        data=json.dumps(payload)
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "call_sid" in data
    assert "response" in data

def test_voice_preview(client, auth_headers):
    """Verifies speech preview synthesis."""
    payload = {
        "text": "Testing voice preview",
        "voice_model": "en-US-JennyNeural",
        "provider": "edge-tts"
    }
    res = client.post(
        "/api/agent/companies/demo_company/voice/preview",
        headers=auth_headers,
        data=json.dumps(payload)
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "preview_url" in data

def test_company_quota(client):
    """Verifies company quota returns plan parameters."""
    res = client.get("/api/billing/companies/demo_company/quota")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "quotas" in data
    assert "max_agents" in data["quotas"]
    assert "max_call_minutes" in data["quotas"]

def test_razorpay_webhook_processing(client):
    """Verifies webhook processing and plan updating."""
    webhook_payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_webhook_01",
                    "amount": 799900,
                    "notes": {
                        "company_id": "demo_company",
                        "plan_id": "growth"
                    }
                }
            }
        }
    }
    res = client.post(
        "/api/billing/webhook/razorpay",
        headers={"Content-Type": "application/json"},
        data=json.dumps(webhook_payload)
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "received"
