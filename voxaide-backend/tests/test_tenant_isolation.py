import os
import json
import pytest
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set APP_ENV to testing
os.environ["APP_ENV"] = "testing"

from app import app
from app.services.company_service import company_service
from app.services.conversation_service import conversation_service
from app.services.knowledge_service import knowledge_service

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def setup_tenants():
    """Create two distinct companies owned by different users."""
    # Company A
    user_a = "user_alpha_123"
    comp_a = company_service.create_company(
        name="SmileCare Dental",
        owner_user_id=user_a,
        description="Comprehensive dental services."
    )

    # Company B
    user_b = "user_beta_456"
    comp_b = company_service.create_company(
        name="AutoFix Mechanics",
        owner_user_id=user_b,
        description="Automotive repair and maintenance."
    )

    return {
        "user_a": user_a,
        "comp_a": comp_a,
        "user_b": user_b,
        "comp_b": comp_b
    }

def test_unauthenticated_request_rejected(client, setup_tenants):
    """Test 9: Verify unauthenticated requests are rejected with 401."""
    comp_a_id = setup_tenants["comp_a"].id
    res = client.get(f"/api/companies/{comp_a_id}")
    assert res.status_code == 401
    data = json.loads(res.data)
    assert "error" in data

def test_authenticated_user_can_access_their_company(client, setup_tenants):
    """Test 1: Authenticated user A can access Company A."""
    comp_a_id = setup_tenants["comp_a"].id
    user_a = setup_tenants["user_a"]

    headers = {
        "Authorization": "Bearer mock_token",
        "X-Test-User-Id": user_a
    }
    res = client.get(f"/api/companies/{comp_a_id}", headers=headers)
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["company"]["id"] == comp_a_id
    assert data["company"]["name"] == "SmileCare Dental"

def test_unauthorized_user_cannot_access_another_company(client, setup_tenants):
    """Test 2 & 8: User B cannot access Company A's data (403 Forbidden)."""
    comp_a_id = setup_tenants["comp_a"].id
    user_b = setup_tenants["user_b"]

    headers = {
        "Authorization": "Bearer mock_token",
        "X-Test-User-Id": user_b
    }
    res = client.get(f"/api/companies/{comp_a_id}", headers=headers)
    assert res.status_code == 403
    data = json.loads(res.data)
    assert data.get("code") == "TENANT_ACCESS_DENIED"

def test_agent_config_is_company_specific(setup_tenants):
    """Test 3: Company A and Company B have isolated agent configurations."""
    comp_a_id = setup_tenants["comp_a"].id
    comp_b_id = setup_tenants["comp_b"].id

    config_a = company_service.get_agent_config(comp_a_id)
    config_b = company_service.get_agent_config(comp_b_id)

    assert "SmileCare" in config_a.agent_name
    assert "AutoFix" in config_b.agent_name
    assert config_a.company_id == comp_a_id
    assert config_b.company_id == comp_b_id

def test_conversation_is_company_scoped(setup_tenants):
    """Test 4: Conversations belonging to Company A cannot be retrieved by Company B."""
    comp_a_id = setup_tenants["comp_a"].id
    comp_b_id = setup_tenants["comp_b"].id

    conv_a = conversation_service.get_or_create_conversation(
        company_id=comp_a_id,
        channel="web_text"
    )

    conversation_service.add_message(
        conversation_id=conv_a.id,
        company_id=comp_a_id,
        role="user",
        content="What is the price of tooth extraction?"
    )

    # Retrieval under Company A succeeds
    conv_retrieved_a = conversation_service.get_conversation(comp_a_id, conv_a.id)
    assert conv_retrieved_a is not None

    # Cross-tenant retrieval under Company B MUST return None
    conv_retrieved_b = conversation_service.get_conversation(comp_b_id, conv_a.id)
    assert conv_retrieved_b is None

    # Message history under Company B must return empty list
    messages_b = conversation_service.get_recent_messages(conv_a.id, company_id=comp_b_id)
    assert len(messages_b) == 0

def test_knowledge_service_enforces_company_id():
    """Test 7: RAG interface requires and enforces company_id."""
    with pytest.raises(ValueError):
        knowledge_service.search(company_id="", query="What are your hours?")
