from flask import Blueprint, request, jsonify, g
from app.core.security import require_auth, require_company_access
from app.services.agent_orchestrator import agent_orchestrator, AgentRequest
from app.core.logging import logger

agent_bp = Blueprint("agent_routes", __name__, url_prefix="/api/agent")

@agent_bp.route("/test", methods=["POST"])
@require_auth
@require_company_access("company_id")
def test_agent():
    """
    Authenticated text-based agent testing endpoint.
    Verifies user has access to company_id, then processes the message via AgentOrchestrator.
    """
    data = request.get_json() or {}
    company_id = data.get("company_id")
    message = data.get("message", "").strip()
    conversation_id = data.get("conversation_id")
    channel = data.get("channel", "web_text")

    if not message:
        return jsonify({"error": "Message cannot be empty."}), 400

    user_id = g.user.get("uid")

    agent_request = AgentRequest(
        company_id=company_id,
        message=message,
        conversation_id=conversation_id,
        user_id=user_id,
        channel=channel,
        metadata={"client": "test_agent_api"}
    )

    response = agent_orchestrator.process(agent_request)

    return jsonify({
        "response": response.text,
        "conversation_id": response.conversation_id,
        "tool_calls": response.tool_calls,
        "sources": response.sources,
        "should_escalate": response.should_escalate,
        "latency_ms": response.latency_ms
    }), 200

@agent_bp.route("/companies/<company_id>/agent/chat", methods=["POST"])
@require_auth
@require_company_access("company_id")
def company_chat(company_id: str):
    """
    Company-specific agent chat endpoint with optional TTS audio synthesis.
    Used by Dashboard Test Agent Playground and Customer Chat.
    """
    from app.services.audio_service import audio_service

    data = request.get_json() or {}
    message = data.get("message", "").strip()
    conversation_id = data.get("conversation_id")
    channel = data.get("channel", "web_text")
    want_audio = data.get("synthesize_audio", False)

    if not message:
        return jsonify({"error": "Message cannot be empty."}), 400

    user_id = getattr(g, "user", {}).get("uid")

    agent_request = AgentRequest(
        company_id=company_id,
        message=message,
        conversation_id=conversation_id,
        user_id=user_id,
        channel=channel,
        metadata={"client": "dashboard_chat"}
    )

    response = agent_orchestrator.process(agent_request)

    audio_url = None
    if want_audio and response.text:
        audio_url = audio_service.synthesize_speech_url(
            text=response.text,
            base_url=request.host_url
        )

    return jsonify({
        "response": response.text,
        "audio_url": audio_url,
        "conversation_id": response.conversation_id,
        "tool_calls": response.tool_calls,
        "sources": response.sources,
        "should_escalate": response.should_escalate,
        "latency_ms": response.latency_ms
    }), 200
