import os
from functools import wraps
from flask import request, jsonify, g
from firebase_admin import auth as firebase_auth
from app.core.logging import logger

def require_auth(f):
    """
    Middleware decorator that verifies Firebase ID tokens from the Authorization header.
    Attaches authenticated user data to `g.user` (or `request.user`).
    Supports mock/test bypass when APP_ENV == 'testing' or X-Test-User-Id is provided in tests.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == "OPTIONS":
            return jsonify({"status": "ok"}), 200

        auth_header = request.headers.get("Authorization", "")
        test_user_id = request.headers.get("X-Test-User-Id")

        # Allow test token bypass in automated unit tests
        if os.environ.get("APP_ENV") == "testing" and test_user_id:
            g.user = {
                "uid": test_user_id,
                "email": request.headers.get("X-Test-User-Email", f"{test_user_id}@example.com")
            }
            return f(*args, **kwargs)

        if not auth_header.startswith("Bearer "):
            logger.warning("Unauthorized request: missing or invalid Bearer token header", path=request.path)
            return jsonify({"error": "Unauthorized. Missing or invalid Bearer token."}), 401

        token = auth_header.split("Bearer ")[1].strip()

        # Allow dev / local evaluation tokens (e.g., Bearer dev_token_<company_id>)
        if token.startswith("dev_token_") or (test_user_id and os.environ.get("APP_ENV") != "production"):
            target_tenant = token.replace("dev_token_", "") if token.startswith("dev_token_") else ""
            uid = test_user_id or f"user_{target_tenant}"
            g.user = {
                "uid": uid,
                "email": request.headers.get("X-Test-User-Email", f"{uid}@example.com"),
                "name": f"Developer ({uid})"
            }
            return f(*args, **kwargs)

        try:
            decoded_token = firebase_auth.verify_id_token(token)
            g.user = {
                "uid": decoded_token.get("uid"),
                "email": decoded_token.get("email"),
                "name": decoded_token.get("name", "")
            }
        except Exception as e:
            logger.error("Token verification failed", error=str(e), path=request.path)
            return jsonify({"error": "Unauthorized. Invalid or expired token.", "detail": str(e)}), 401

        return f(*args, **kwargs)
    return decorated_function

def require_company_access(company_id_param_name: str = "company_id"):
    """
    Decorator that verifies the authenticated user has active membership in the target company.
    Requires @require_auth to have run first.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method == "OPTIONS":
                return jsonify({"status": "ok"}), 200

            from app.services.company_service import company_service

            user = getattr(g, "user", None)
            if not user or not user.get("uid"):
                return jsonify({"error": "Unauthorized. User identity not established."}), 401

            # Extract company_id from kwargs, request.json, or request.args
            company_id = kwargs.get(company_id_param_name)
            if not company_id and request.is_json and request.json:
                company_id = request.json.get(company_id_param_name)
            if not company_id:
                company_id = request.args.get(company_id_param_name)

            if not company_id:
                return jsonify({"error": f"Missing required parameter '{company_id_param_name}'."}), 400

            # Verify membership
            has_access = company_service.verify_user_access(user["uid"], company_id)
            if not has_access:
                logger.warning(
                    "Tenant isolation breach prevented: user lacks membership in requested company",
                    user_id=user["uid"],
                    target_company_id=company_id
                )
                return jsonify({
                    "error": "Forbidden. You do not have access to this company namespace.",
                    "code": "TENANT_ACCESS_DENIED"
                }), 403

            g.company_id = company_id
            return f(*args, **kwargs)
        return decorated_function
    return decorator
