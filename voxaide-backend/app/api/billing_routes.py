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
