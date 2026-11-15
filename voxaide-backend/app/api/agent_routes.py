from flask import Blueprint, request, jsonify, g
from app.core.security import require_auth, require_company_access
from app.services.agent_orchestrator import agent_orchestrator, AgentRequest
from app.services.audio_service import audio_service
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
    agent_id = data.get("agent_id")
    conversation_id = data.get("conversation_id")
    channel = data.get("channel", "web_text")
    want_audio = data.get("synthesize_audio", False)

    if not message:
        return jsonify({"error": "Message cannot be empty."}), 400

    user_id = getattr(g, "user", {}).get("uid")

    agent_request = AgentRequest(
        company_id=company_id,
        agent_id=agent_id,
        message=message,
        conversation_id=conversation_id,
        user_id=user_id,
        channel=channel,
        metadata={"client": "dashboard_chat"}
    )

    response = agent_orchestrator.process(agent_request)

    audio_url = None
    if want_audio and response.text:
        base_url = request.host_url.rstrip("/")
        if request.headers.get("X-Forwarded-Proto") == "https" or "onrender.com" in request.host:
            base_url = base_url.replace("http://", "https://")
        audio_url = audio_service.synthesize_speech_url(
            text=response.text,
            base_url=base_url
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

# ----------------- MULTI-AGENT STUDIO ROUTES -----------------
@agent_bp.route("/companies/<company_id>/agents", methods=["GET"])
@require_auth
@require_company_access("company_id")
def list_company_agents(company_id: str):
    from app.services.company_service import company_service
    agents = company_service.list_agents(company_id)
    return jsonify({
        "success": True,
        "agents": [a.model_dump() for a in agents]
    }), 200

@agent_bp.route("/companies/<company_id>/agents", methods=["POST"])
@require_auth
@require_company_access("company_id")
def create_company_agent(company_id: str):
    from app.services.company_service import company_service
    from app.api.billing_routes import PLAN_QUOTAS

    data = request.get_json() or {}
    name = data.get("agent_name", "").strip()
    if not name:
        return jsonify({"success": False, "error": "Agent name is required."}), 400

    # Quota check
    existing_agents = company_service.list_agents(company_id)
    sub = company_service._companies_mem.get(company_id, {}).get("subscription", {})
    plan_id = sub.get("plan_id", "growth")
    quota = PLAN_QUOTAS.get(plan_id, PLAN_QUOTAS["growth"])

    if len(existing_agents) >= quota["max_agents"]:
        return jsonify({
            "success": False,
            "error": f"Agent limit reached for your {quota['plan_name']} plan ({quota['max_agents']} max). Please upgrade to deploy more agents."
        }), 403

    agent = company_service.create_agent(company_id, **data)
    return jsonify({
        "success": True,
        "agent": agent.model_dump(),
        "message": f"Agent '{agent.agent_name}' created successfully."
    }), 201

@agent_bp.route("/companies/<company_id>/agents/<agent_id>", methods=["GET"])
@require_auth
@require_company_access("company_id")
def get_company_agent(company_id: str, agent_id: str):
    from app.services.company_service import company_service
    agent = company_service.get_agent(company_id, agent_id=agent_id)
    return jsonify({"success": True, "agent": agent.model_dump()}), 200

@agent_bp.route("/companies/<company_id>/agents/<agent_id>", methods=["PUT"])
@require_auth
@require_company_access("company_id")
def update_company_agent(company_id: str, agent_id: str):
    from app.services.company_service import company_service
    data = request.get_json() or {}
    updated = company_service.update_agent(company_id, agent_id, **data)
    if not updated:
        return jsonify({"success": False, "error": "Agent not found."}), 404
    return jsonify({"success": True, "agent": updated.model_dump(), "message": "Agent updated."}), 200

@agent_bp.route("/companies/<company_id>/agents/<agent_id>", methods=["DELETE"])
@require_auth
@require_company_access("company_id")
def delete_company_agent(company_id: str, agent_id: str):
    from app.services.company_service import company_service
    success = company_service.delete_agent(company_id, agent_id)
    if not success:
        return jsonify({"success": False, "error": "Cannot delete agent or agent not found."}), 400
    return jsonify({"success": True, "message": "Agent deleted successfully."}), 200

@agent_bp.route("/companies/<company_id>/voice/preview", methods=["POST"])
@require_auth
@require_company_access("company_id")
def preview_voice(company_id: str):
    """
    Synthesizes a short voice preview sample for Edge-TTS or ElevenLabs.
    """
    from app.services.audio_service import audio_service
    data = request.get_json() or {}
    text = data.get("text", "Hello! This is a preview of your AI customer support voice on VoxAide.")
    voice_model = data.get("voice_model", "en-US-JennyNeural")
    provider = data.get("provider", "edge-tts")
    elevenlabs_api_key = data.get("elevenlabs_api_key")

    base_url = request.host_url.rstrip("/")
    if request.headers.get("X-Forwarded-Proto") == "https" or "onrender.com" in request.host:
        base_url = base_url.replace("http://", "https://")

    preview_url = audio_service.generate_preview(
        text=text,
        voice_model=voice_model,
        provider=provider,
        elevenlabs_api_key=elevenlabs_api_key,
        base_url=base_url
    )

    if not preview_url:
        return jsonify({"success": False, "error": "Could not synthesize audio preview."}), 500

    return jsonify({
        "success": True,
        "preview_url": preview_url,
        "voice_model": voice_model,
        "provider": provider
    }), 200
