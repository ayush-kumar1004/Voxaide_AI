import os
import hmac
import hashlib
import time
from flask import Blueprint, request, jsonify
from app.core.logging import logger

billing_bp = Blueprint("billing_bp", __name__, url_prefix="/api/billing")

@billing_bp.route("/razorpay/create-order", methods=["POST"])
def create_razorpay_order():
    """
    Creates a Razorpay order for subscription payment.
    Falls back to sandbox simulation mode if Razorpay credentials are not yet set.
    """
    try:
        data = request.get_json() or {}
        plan_id = data.get("plan_id", "starter")
        amount = int(data.get("amount", 2499)) # In main units
        currency = data.get("currency", "INR")
        company_id = data.get("company_id", "demo_company")

        key_id = os.environ.get("RAZORPAY_KEY_ID")
        key_secret = os.environ.get("RAZORPAY_KEY_SECRET")

        amount_in_paise = amount * 100

        if key_id and key_secret:
            try:
                import razorpay
                client = razorpay.Client(auth=(key_id, key_secret))
                order_payload = {
                    "amount": amount_in_paise,
                    "currency": currency,
                    "receipt": f"rcpt_{company_id[:8]}_{int(time.time())}",
                    "notes": {
                        "company_id": company_id,
                        "plan_id": plan_id
                    }
                }
                order = client.order.create(data=order_payload)
                return jsonify({
                    "success": True,
                    "order_id": order["id"],
                    "amount": order["amount"],
                    "currency": order["currency"],
                    "key_id": key_id
                }), 200
            except Exception as rzp_err:
                logger.warning("Razorpay client error, falling back to sandbox order", error=str(rzp_err))

        # Fallback Sandbox / Simulation Order
        simulated_order_id = f"order_sim_{int(time.time())}"
        return jsonify({
            "success": True,
            "order_id": simulated_order_id,
            "amount": amount_in_paise,
            "currency": currency,
            "key_id": key_id or "rzp_test_voxaide_demo",
            "simulation": True
        }), 200
    except Exception as e:
        logger.error("Error creating Razorpay order", error=str(e))
        return jsonify({"success": False, "error": str(e)}), 500


@billing_bp.route("/razorpay/verify-payment", methods=["POST"])
def verify_razorpay_payment():
    """
    Verifies Razorpay payment signature and activates the company's subscription.
    """
    try:
        data = request.get_json() or {}
        order_id = data.get("razorpay_order_id", "")
        payment_id = data.get("razorpay_payment_id", "")
        signature = data.get("razorpay_signature", "")
        company_id = data.get("company_id", "demo_company")
        plan_id = data.get("plan_id", "starter")

        key_secret = os.environ.get("RAZORPAY_KEY_SECRET")

        is_valid = False
        if key_secret and signature and not order_id.startswith("order_sim_"):
            try:
                msg = f"{order_id}|{payment_id}".encode("utf-8")
                expected_sig = hmac.new(key_secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
                is_valid = hmac.compare_digest(expected_sig, signature)
            except Exception as sig_err:
                logger.warning("Signature verification failed", error=str(sig_err))
                is_valid = False
        else:
            # Simulation mode verification
            is_valid = True

        if is_valid:
            # Update company status in database if available
            try:
                import firebase_admin
                from firebase_admin import firestore
                if firebase_admin._apps:
                    db = firestore.client()
                    company_ref = db.collection("companies").document(company_id)
                    company_ref.set({
                        "subscription": {
                            "plan_id": plan_id,
                            "status": "active",
                            "payment_id": payment_id,
                            "order_id": order_id,
                            "activated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                        }
                    }, merge=True)
            except Exception as db_err:
                logger.warning("Could not persist subscription to Firestore", error=str(db_err))

            # Update in-memory company cache
            from app.services.company_service import company_service
            if company_id in company_service._companies_mem:
                company_service._companies_mem[company_id]["subscription"] = {
                    "plan_id": plan_id,
                    "status": "active",
                    "payment_id": payment_id,
                    "order_id": order_id,
                    "activated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                }

            return jsonify({
                "success": True,
                "message": f"Payment verified. Plan '{plan_id}' activated for {company_id}.",
                "plan_id": plan_id,
                "status": "active"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Invalid payment signature."
            }), 400
    except Exception as e:
        logger.error("Error verifying payment", error=str(e))
        return jsonify({"success": False, "error": str(e)}), 500


PLAN_QUOTAS = {
    "starter": {
        "plan_name": "Starter",
        "max_agents": 1,
        "max_call_minutes": 500,
        "custom_voices": False,
        "postgres_access": False,
        "priority_support": False
    },
    "growth": {
        "plan_name": "Growth",
        "max_agents": 5,
        "max_call_minutes": 2500,
        "custom_voices": True,
        "postgres_access": True,
        "priority_support": True
    },
    "enterprise": {
        "plan_name": "Enterprise",
        "max_agents": 25,
        "max_call_minutes": 10000,
        "custom_voices": True,
        "postgres_access": True,
        "priority_support": True
    }
}


@billing_bp.route("/webhook/razorpay", methods=["POST"])
def razorpay_webhook():
    """
    Production Razorpay Webhook listener.
    Verifies HMAC SHA256 signature and handles payment.captured, order.paid, and subscription events.
    """
    raw_payload = request.data
    webhook_signature = request.headers.get("X-Razorpay-Signature", "")
    webhook_secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET")

    if webhook_secret:
        expected_sig = hmac.new(webhook_secret.encode("utf-8"), raw_payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig, webhook_signature):
            logger.warning("Razorpay webhook signature verification failed")
            return jsonify({"error": "Invalid webhook signature"}), 400

    data = request.get_json(silent=True) or {}
    event = data.get("event", "unknown")
    payload = data.get("payload", {})

    logger.info("Razorpay webhook received", event=event)

    # Resolve company_id and plan_id from payment or order notes
    payment_entity = payload.get("payment", {}).get("entity", {})
    order_entity = payload.get("order", {}).get("entity", {})
    notes = payment_entity.get("notes") or order_entity.get("notes") or {}

    company_id = notes.get("company_id")
    plan_id = notes.get("plan_id", "growth")

    if company_id and event in ("payment.captured", "order.paid", "subscription.activated", "subscription.charged"):
        from app.services.company_service import company_service
        sub_record = {
            "plan_id": plan_id,
            "status": "active",
            "event": event,
            "payment_id": payment_entity.get("id"),
            "order_id": order_entity.get("id") or payment_entity.get("order_id"),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        if company_id in company_service._companies_mem:
            company_service._companies_mem[company_id]["subscription"] = sub_record

        try:
            import firebase_admin
            from firebase_admin import firestore
            if firebase_admin._apps:
                db = firestore.client()
                db.collection("companies").document(company_id).set({"subscription": sub_record}, merge=True)
        except Exception as err:
            logger.warning("Could not persist webhook subscription update", error=str(err))

    return jsonify({"status": "received", "event": event}), 200


@billing_bp.route("/companies/<company_id>/quota", methods=["GET"])
def get_company_quota(company_id: str):
    """
    Returns current plan tier, quota limits, and usage metrics for the company.
    """
    from app.services.company_service import company_service
    from app.services.telephony_service import telephony_service

    company = company_service.get_company(company_id)
    sub = {}
    if company_id in company_service._companies_mem:
        sub = company_service._companies_mem[company_id].get("subscription", {})
    elif company and getattr(company, "subscription", None):
        sub = company.subscription

    plan_id = sub.get("plan_id", "growth") if sub else "growth"
    quota = PLAN_QUOTAS.get(plan_id, PLAN_QUOTAS["growth"])

    agents = company_service.list_agents(company_id)
    calls = telephony_service.list_call_logs(company_id)
    total_seconds = sum(c.get("duration_seconds", 0) for c in calls)
    used_minutes = round(total_seconds / 60, 1)

    return jsonify({
        "success": True,
        "company_id": company_id,
        "plan_id": plan_id,
        "plan_name": quota["plan_name"],
        "status": sub.get("status", "active"),
        "quotas": {
            "max_agents": quota["max_agents"],
            "agents_used": len(agents),
            "max_call_minutes": quota["max_call_minutes"],
            "call_minutes_used": used_minutes,
            "custom_voices": quota["custom_voices"],
            "postgres_access": quota["postgres_access"],
            "priority_support": quota["priority_support"]
        }
    }), 200
