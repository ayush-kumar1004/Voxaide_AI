import json
from flask import Blueprint, request, jsonify, g
from app.services.db_connector_service import postgres_service
from app.core.logging import logger

connector_bp = Blueprint("connector_bp", __name__, url_prefix="/api/companies/<company_id>/connectors")

# In-memory store fallback for demo/local environments if Firestore is not connected
_COMPANY_CONNECTORS = {}

@connector_bp.route("/postgres/test", methods=["POST"])
def test_postgres(company_id: str):
    """
    Tests a company's PostgreSQL connection credentials and returns visible tables.
    """
    data = request.get_json() or {}
    result = postgres_service.test_connection(data)
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code

@connector_bp.route("/postgres", methods=["POST"])
def save_postgres_connector(company_id: str):
    """
    Saves or updates a company's PostgreSQL connector configuration.
    """
    data = request.get_json() or {}
    
    # Test connection first to verify validity
    test_result = postgres_service.test_connection(data)
    if not test_result.get("success"):
        return jsonify({
            "success": False,
            "error": f"Cannot save invalid connection: {test_result.get('error')}"
        }), 400

    # Introspect schema for allowed tables
    allowed_tables = data.get("allowed_tables") or test_result.get("tables", [])
    schema_res = postgres_service.get_table_schemas(data, allowed_tables=allowed_tables)

    connector_data = {
        "company_id": company_id,
        "type": "postgresql",
        "host": data.get("host"),
        "port": data.get("port", 5432),
        "dbname": data.get("dbname"),
        "user": data.get("user"),
        "password": data.get("password"),
        "sslmode": data.get("sslmode", "prefer"),
        "connection_string": data.get("connection_string"),
        "allowed_tables": allowed_tables,
        "schemas": schema_res.get("schemas", {}),
        "status": "connected"
    }

    _COMPANY_CONNECTORS[company_id] = connector_data

    # Persist in Firestore if available
    try:
        import firebase_admin
        from firebase_admin import firestore
        if firebase_admin._apps:
            db = firestore.client()
            db.collection("companies").document(company_id).collection("connectors").document("postgres").set(connector_data, merge=True)
    except Exception as e:
        logger.warning("Could not persist connector to Firestore", error=str(e))

    safe_summary = {k: v for k, v in connector_data.items() if k not in ["password", "connection_string"]}
    return jsonify({
        "success": True,
        "message": f"PostgreSQL database connected! Configured {len(allowed_tables)} table(s).",
        "connector": safe_summary
    }), 200

@connector_bp.route("/postgres", methods=["GET"])
def get_postgres_connector(company_id: str):
    """
    Returns the active PostgreSQL connector configuration for a company.
    """
    connector = _COMPANY_CONNECTORS.get(company_id)
    if not connector:
        try:
            import firebase_admin
            from firebase_admin import firestore
            if firebase_admin._apps:
                db = firestore.client()
                doc = db.collection("companies").document(company_id).collection("connectors").document("postgres").get()
                if doc.exists:
                    connector = doc.to_dict()
                    _COMPANY_CONNECTORS[company_id] = connector
        except Exception:
            pass

    if not connector:
        return jsonify({"success": False, "connected": False, "message": "No active PostgreSQL connector."}), 200

    safe_summary = {k: v for k, v in connector.items() if k not in ["password", "connection_string"]}
    return jsonify({
        "success": True,
        "connected": True,
        "connector": safe_summary
    }), 200

@connector_bp.route("/postgres/query", methods=["POST"])
def execute_test_query(company_id: str):
    """
    Executes a safe read-only test query on behalf of the company.
    """
    connector = _COMPANY_CONNECTORS.get(company_id)
    if not connector:
        return jsonify({"success": False, "error": "Company has no active PostgreSQL connector."}), 400

    data = request.get_json() or {}
    sql = data.get("sql", "").strip()
    if not sql:
        return jsonify({"success": False, "error": "Missing 'sql' query parameter."}), 400

    result = postgres_service.execute_safe_query(connector, sql)
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code
