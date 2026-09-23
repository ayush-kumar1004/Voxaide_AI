from flask import Blueprint, request, jsonify
from app.core.security import require_auth, require_company_access
from app.services.appointment_service import appointment_service
from app.tools.escalation_tool import escalate_tool_instance
from app.core.logging import logger

appointment_bp = Blueprint("appointment_routes", __name__, url_prefix="/api/companies")

@appointment_bp.route("/<company_id>/appointments", methods=["GET"])
@require_auth
@require_company_access("company_id")
def list_appointments(company_id: str):
    """List appointments for a company with optional date and status filters."""
    date_filter = request.args.get("date")
    status_filter = request.args.get("status")

    appts = appointment_service.list_appointments(
        company_id=company_id,
        date_str=date_filter,
        status=status_filter
    )
    return jsonify({
        "appointments": [a.model_dump() for a in appts],
        "count": len(appts)
    }), 200

@appointment_bp.route("/<company_id>/appointments", methods=["POST"])
@require_auth
@require_company_access("company_id")
def create_appointment(company_id: str):
    """Direct API appointment creation within business hours."""
    data = request.get_json(silent=True) or {}
    
    customer_name = data.get("customer_name")
    customer_phone = data.get("customer_phone")
    date_str = data.get("date")
    time_str = data.get("time")

    if not all([customer_name, customer_phone, date_str, time_str]):
        return jsonify({
            "error": "Missing required fields: customer_name, customer_phone, date, and time are required."
        }), 400

    try:
        appt = appointment_service.book_appointment(
            company_id=company_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            date_str=date_str,
            time_str=time_str,
            duration_minutes=int(data.get("duration_minutes", 30)),
            service=data.get("service", "General Consultation"),
            customer_email=data.get("customer_email"),
            notes=data.get("notes")
        )
        return jsonify({
            "message": "Appointment booked successfully.",
            "appointment": appt.model_dump()
        }), 201
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error("Appointment creation failed", error=str(e), company_id=company_id)
        return jsonify({"error": f"Failed to book appointment: {str(e)}"}), 500

@appointment_bp.route("/<company_id>/appointments/<appointment_id>", methods=["GET"])
@require_auth
@require_company_access("company_id")
def get_appointment(company_id: str, appointment_id: str):
    """Get single appointment with strict tenant access check."""
    appt = appointment_service.get_appointment(company_id, appointment_id)
    if not appt:
        return jsonify({"error": "Appointment not found or unauthorized access."}), 404
    return jsonify({"appointment": appt.model_dump()}), 200

@appointment_bp.route("/<company_id>/appointments/<appointment_id>/reschedule", methods=["PATCH", "POST"])
@require_auth
@require_company_access("company_id")
def reschedule_appointment(company_id: str, appointment_id: str):
    """Reschedule an existing appointment to a new slot."""
    data = request.get_json(silent=True) or {}
    new_date = data.get("new_date")
    new_time = data.get("new_time")

    if not new_date or not new_time:
        return jsonify({"error": "new_date and new_time are required."}), 400

    try:
        appt = appointment_service.reschedule_appointment(
            company_id=company_id,
            appointment_id=appointment_id,
            new_date_str=new_date,
            new_time_str=new_time,
            duration_minutes=data.get("duration_minutes")
        )
        return jsonify({
            "message": "Appointment rescheduled successfully.",
            "appointment": appt.model_dump()
        }), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error("Reschedule failed", error=str(e), appointment_id=appointment_id)
        return jsonify({"error": f"Failed to reschedule: {str(e)}"}), 500

@appointment_bp.route("/<company_id>/appointments/<appointment_id>/cancel", methods=["POST"])
@require_auth
@require_company_access("company_id")
def cancel_appointment(company_id: str, appointment_id: str):
    """Cancel an appointment and free its slot."""
    data = request.get_json(silent=True) or {}
    reason = data.get("reason", "Cancelled by customer or company.")

    try:
        appt = appointment_service.cancel_appointment(
            company_id=company_id,
            appointment_id=appointment_id,
            reason=reason
        )
        return jsonify({
            "message": "Appointment cancelled successfully.",
            "appointment": appt.model_dump()
        }), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error("Cancellation failed", error=str(e), appointment_id=appointment_id)
        return jsonify({"error": f"Failed to cancel: {str(e)}"}), 500

@appointment_bp.route("/<company_id>/escalations", methods=["GET"])
@require_auth
@require_company_access("company_id")
def list_escalations(company_id: str):
    """List escalation tickets for a company."""
    escalations = escalate_tool_instance.list_escalations(company_id)
    return jsonify({
        "escalations": escalations,
        "count": len(escalations)
    }), 200
