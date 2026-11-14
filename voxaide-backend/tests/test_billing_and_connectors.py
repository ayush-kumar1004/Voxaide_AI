import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_razorpay_create_order_simulation(client):
    res = client.post("/api/billing/razorpay/create-order", json={
        "plan_id": "growth",
        "amount": 7999,
        "currency": "INR",
        "company_id": "test_co"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "order_id" in data
    assert data["amount"] == 799900
    assert data["currency"] == "INR"

def test_razorpay_verify_payment_simulation(client):
    res = client.post("/api/billing/razorpay/verify-payment", json={
        "razorpay_order_id": "order_sim_12345",
        "razorpay_payment_id": "pay_sim_12345",
        "razorpay_signature": "mock_sig",
        "company_id": "test_co",
        "plan_id": "growth"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["status"] == "active"

def test_postgres_connector_get_empty(client):
    res = client.get("/api/companies/unconnected_co/connectors/postgres")
    assert res.status_code == 200
    data = res.get_json()
    assert data["connected"] is False

def test_postgres_safe_query_guardrails():
    from app.services.db_connector_service import postgres_service
    # Test rejection of non-SELECT statements
    res_drop = postgres_service.execute_safe_query({}, "DROP TABLE users;")
    assert res_drop["success"] is False
    assert "Security violation" in res_drop["error"]

    res_insert = postgres_service.execute_safe_query({}, "INSERT INTO users VALUES ('hacker');")
    assert res_insert["success"] is False
    assert "Security violation" in res_insert["error"]
