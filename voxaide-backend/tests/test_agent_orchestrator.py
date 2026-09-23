import os
import json
import pytest
import sys
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["APP_ENV"] = "testing"

from app import app
from app.providers.base import LLMProvider, LLMResponse, ToolCallRequest
from app.services.agent_orchestrator import AgentOrchestrator, AgentRequest, agent_orchestrator
from app.services.company_service import company_service
from app.tools.base import AgentTool, ToolRegistry

class MockLLMProvider(LLMProvider):
    """Deterministic Mock LLM for testing orchestrator without external API calls."""

    def __init__(self, fixed_response: str = "Mocked answer", tool_calls: Optional[List[ToolCallRequest]] = None):
        self.fixed_response = fixed_response
        self.tool_calls = tool_calls or []
        self.last_system_instruction = ""
        self.last_prompt = ""

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.3
    ) -> LLMResponse:
        self.last_prompt = prompt
        self.last_system_instruction = system_instruction
        return LLMResponse(
            content=self.fixed_response,
            tool_calls=self.tool_calls,
            finish_reason="stop"
        )

class MockBookingTool(AgentTool):
    """Mock tool to verify company_id is passed during tool execution."""

    @property
    def name(self) -> str:
        return "mock_booking"

    @property
    def description(self) -> str:
        return "Book an appointment."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "date": {"type": "string"},
                "time": {"type": "string"}
            },
            "required": ["date"]
        }

    def execute(self, company_id: str, **kwargs) -> Dict[str, Any]:
        # Assert company_id is received
        return {
            "booked_company_id": company_id,
            "status": "success",
            "date": kwargs.get("date")
        }

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def test_company():
    user_id = "user_dentist_777"
    comp = company_service.create_company(
        name="Apex Smiles",
        owner_user_id=user_id,
        description="Painless dental implants and cleaning."
    )
    return {"user_id": user_id, "company": comp}

def test_orchestrator_receives_correct_company_context(test_company):
    """Test 5: AgentOrchestrator resolves company and injects company details into system prompt."""
    comp = test_company["company"]
    mock_llm = MockLLMProvider(fixed_response="Our clinic is open until 6 PM.")

    custom_orchestrator = AgentOrchestrator(
        llm_provider=mock_llm,
        company_svc=company_service
    )

    req = AgentRequest(
        company_id=comp.id,
        message="What are your hours?"
    )

    res = custom_orchestrator.process(req)

    assert res.text == "Our clinic is open until 6 PM."
    assert "Apex Smiles" in mock_llm.last_system_instruction
    assert "Painless dental implants" in mock_llm.last_system_instruction
    assert res.conversation_id != ""

def test_tool_execution_receives_company_id(test_company):
    """Test 6: When tool is executed, company_id is strictly passed to prevent cross-tenant operations."""
    comp = test_company["company"]

    tools = ToolRegistry()
    mock_tool = MockBookingTool()
    tools.register(mock_tool)

    mock_llm = MockLLMProvider(
        fixed_response="",
        tool_calls=[ToolCallRequest(name="mock_booking", arguments={"date": "tomorrow"})]
    )

    custom_orchestrator = AgentOrchestrator(
        llm_provider=mock_llm,
        company_svc=company_service,
        tools=tools
    )

    req = AgentRequest(
        company_id=comp.id,
        message="Can I book for tomorrow?"
    )

    res = custom_orchestrator.process(req)

    assert len(res.tool_calls) == 1
    call_record = res.tool_calls[0]
    assert call_record["name"] == "mock_booking"
    assert call_record["result"]["result"]["booked_company_id"] == comp.id

def test_api_test_agent_endpoint(client, test_company):
    """Test authenticated POST /api/agent/test endpoint."""
    comp = test_company["company"]
    user_id = test_company["user_id"]

    headers = {
        "Authorization": "Bearer mock_token",
        "X-Test-User-Id": user_id
    }

    # Valid request
    res = client.post("/api/agent/test", headers=headers, json={
        "company_id": comp.id,
        "message": "Hello there!"
    })

    assert res.status_code == 200
    data = json.loads(res.data)
    assert "response" in data
    assert "conversation_id" in data

    # Unauthorized access (User B attempting to test Company A)
    unauth_headers = {
        "Authorization": "Bearer mock_token",
        "X-Test-User-Id": "intruder_user_999"
    }

    unauth_res = client.post("/api/agent/test", headers=unauth_headers, json={
        "company_id": comp.id,
        "message": "Give me company secrets"
    })

    assert unauth_res.status_code == 403
    unauth_data = json.loads(unauth_res.data)
    assert unauth_data.get("code") == "TENANT_ACCESS_DENIED"
