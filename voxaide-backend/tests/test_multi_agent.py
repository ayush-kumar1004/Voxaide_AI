import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_list_agents_for_company(client):
    res = client.get("/api/agent/companies/demo_company/agents", headers={
        "Authorization": "Bearer dev_token_demo_company",
        "X-Company-ID": "demo_company",
        "X-Test-User-Id": "user_demo_company"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["agents"]) >= 2
    agent_ids = [a["agent_id"] for a in data["agents"]]
    assert "agent_support_01" in agent_ids

def test_create_and_delete_agent(client):
    headers = {
        "Authorization": "Bearer dev_token_demo_company",
        "X-Company-ID": "demo_company",
        "X-Test-User-Id": "user_demo_company"
    }
    # 1. Create
    create_res = client.post("/api/agent/companies/demo_company/agents", headers=headers, json={
        "agent_name": "Maya - Escalation Lead",
        "role": "VIP Customer Support",
        "voice_model": "en-US-JennyNeural",
        "greeting": "Hello, I am Maya from executive support."
    })
    assert create_res.status_code == 201
    created = create_res.get_json()["agent"]
    agent_id = created["agent_id"]

    # 2. Get
    get_res = client.get(f"/api/agent/companies/demo_company/agents/{agent_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.get_json()["agent"]["agent_name"] == "Maya - Escalation Lead"

    # 3. Delete
    del_res = client.delete(f"/api/agent/companies/demo_company/agents/{agent_id}", headers=headers)
    assert del_res.status_code == 200

def test_serve_widget_script(client):
    res = client.get("/widget.js")
    assert res.status_code == 200
    assert "application/javascript" in res.content_type
    assert b"VoxaideWidgetLoaded" in res.data
