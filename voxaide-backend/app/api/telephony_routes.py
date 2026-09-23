from flask import Blueprint, request, Response, jsonify
from app.core.security import require_auth, require_company_access
from app.services.telephony_service import telephony_service
from app.services.agent_orchestrator import agent_orchestrator, AgentRequest
from app.services.company_service import company_service
from app.core.logging import logger

telephony_bp = Blueprint("telephony_routes", __name__)

# ==============================================================================
# TWILIO WEBHOOKS (VOICE TRANSPORT ADAPTER)
# ==============================================================================

@telephony_bp.route("/api/telephony/voice/inbound", methods=["POST", "GET"])
def handle_inbound_call():
    """
    Twilio Inbound Voice Webhook.
    Resolves tenant by called number, logs call initiation, and returns TwiML greeting.
    """
    to_number = request.values.get("To", "")
    from_number = request.values.get("From", "")
    call_sid = request.values.get("CallSid", "")

    # Look up company by assigned phone number or query parameter
    company_id = request.args.get("company_id")
    if not company_id and to_number:
        company_id = telephony_service.get_company_for_phone_number(to_number)

    if not company_id:
        # Default fallback company or reject.
        # _companies_mem stores dicts (model_dump()), so read the "id" key.
        # Stay tolerant of object-form values just in case.
        all_companies = [
            (c.get("id") if isinstance(c, dict) else getattr(c, "id", None))
            for c in company_service._companies_mem.values()
        ]
        all_companies = [cid for cid in all_companies if cid]
        company_id = all_companies[0] if all_companies else "demo_company"

    # Record call start
    telephony_service.record_call_start(
        call_sid=call_sid,
        company_id=company_id,
        from_number=from_number,
        to_number=to_number,
        direction="inbound"
    )

    logger.info("Inbound telephony call received", call_sid=call_sid, company_id=company_id, from_number=from_number)

    host_url = request.host_url.rstrip("/")
    twiml_xml = telephony_service.generate_twiml_greeting(company_id=company_id, host_url=host_url)
    return Response(twiml_xml, mimetype="text/xml")

@telephony_bp.route("/api/telephony/voice/gather", methods=["POST", "GET"])
def handle_voice_gather():
    """
    Processes caller speech input through the central AgentOrchestrator,
    executes business tools / RAG, and responds with TwiML speech audio.
    """
    call_sid = request.values.get("CallSid", "")
    from_number = request.values.get("From", "")
    speech_result = request.values.get("SpeechResult", "").strip()
    company_id = request.args.get("company_id") or "demo_company"

    if not speech_result:
        # No speech recognized
        host_url = request.host_url.rstrip("/")
        xml = telephony_service.generate_twiml_turn(
            reply_text="I didn't quite catch that. Could you please repeat your question?",
            company_id=company_id,
            host_url=host_url
        )
        return Response(xml, mimetype="text/xml")

    # Route speech through the central AgentOrchestrator
    agent_req = AgentRequest(
        company_id=company_id,
        message=speech_result,
        conversation_id=f"call_{call_sid}",
        channel="phone",
        metadata={"caller_phone": from_number, "call_sid": call_sid}
    )

    agent_res = agent_orchestrator.process(agent_req)

    # Record conversational turn in call log
    telephony_service.record_call_turn(
        call_sid=call_sid,
        user_text=speech_result,
        assistant_text=agent_res.text
    )

    should_hangup = False
    lower_res = agent_res.text.lower()
    if any(phrase in lower_res for phrase in ["goodbye", "have a great day", "bye for now"]):
        should_hangup = True

    host_url = request.host_url.rstrip("/")
    twiml_xml = telephony_service.generate_twiml_turn(
        reply_text=agent_res.text,
        company_id=company_id,
        host_url=host_url,
        should_hangup=should_hangup
    )
    return Response(twiml_xml, mimetype="text/xml")

@telephony_bp.route("/api/telephony/voice/status", methods=["POST", "GET"])
def handle_call_status():
    """Twilio status callback logging call duration and completion."""
    call_sid = request.values.get("CallSid", "")
    duration = int(request.values.get("CallDuration", 0))
    status = request.values.get("CallStatus", "completed")

    telephony_service.record_call_end(call_sid=call_sid, duration_seconds=duration, status=status)
    logger.info("Call status recorded", call_sid=call_sid, duration=duration, status=status)
    return jsonify({"status": "logged"}), 200

# ==============================================================================
# COMPANY TELEPHONY MANAGEMENT ENDPOINTS
# ==============================================================================

@telephony_bp.route("/api/companies/<company_id>/phone-numbers", methods=["GET"])
@require_auth
@require_company_access("company_id")
def list_company_phone_numbers(company_id: str):
    """Lists virtual phone numbers assigned to this company."""
    numbers = telephony_service.list_phone_numbers(company_id)
    return jsonify({"phone_numbers": numbers, "count": len(numbers)}), 200

@telephony_bp.route("/api/companies/<company_id>/phone-numbers", methods=["POST"])
@require_auth
@require_company_access("company_id")
def register_company_phone_number(company_id: str):
    """Assigns a virtual phone number to the company."""
    data = request.get_json(silent=True) or {}
    phone_number = data.get("phone_number")
    label = data.get("label", "Support Line")

    if not phone_number:
        return jsonify({"error": "phone_number is required."}), 400

    record = telephony_service.register_phone_number(
        company_id=company_id,
        phone_number=phone_number,
        label=label
    )
    return jsonify({
        "message": f"Phone number {phone_number} successfully connected to company.",
        "phone_number": record
    }), 201

@telephony_bp.route("/api/companies/<company_id>/call-logs", methods=["GET"])
@require_auth
@require_company_access("company_id")
def list_company_call_logs(company_id: str):
    """Lists call logs for this company."""
    calls = telephony_service.list_call_logs(company_id)
    return jsonify({"call_logs": calls, "count": len(calls)}), 200
