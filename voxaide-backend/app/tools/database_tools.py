from typing import Dict, Any
from app.tools.base import AgentTool, tool_registry
from app.services.db_connector_service import postgres_service
from app.core.logging import logger

class QueryCompanyDatabaseTool(AgentTool):
    """
    Allows the AI agent to query the company's connected PostgreSQL database.
    Strictly read-only, sanitized, and isolated by company_id.
    """

    @property
    def name(self) -> str:
        return "query_company_database"

    @property
    def description(self) -> str:
        return (
            "Executes a safe read-only SELECT SQL query against the company's live PostgreSQL database "
            "to answer customer questions regarding orders, inventory, products, tracking, or account status."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": (
                        "A valid read-only PostgreSQL SELECT query. "
                        "Example: SELECT order_id, status, total, tracking_number FROM orders WHERE order_id = 'ZMT1003'"
                    )
                },
                "intent": {
                    "type": "string",
                    "description": "Brief description of what customer data is being looked up."
                }
            },
            "required": ["sql_query"]
        }

    def execute(self, company_id: str, sql_query: str, **kwargs) -> Dict[str, Any]:
        from app.api.connector_routes import _COMPANY_CONNECTORS

        connector = _COMPANY_CONNECTORS.get(company_id)
        if not connector:
            # Check Firestore if available
            try:
                import firebase_admin
                from firebase_admin import firestore
                if firebase_admin._apps:
                    db = firestore.client()
                    doc = db.collection("companies").document(company_id).collection("connectors").document("postgres").get()
                    if doc.exists:
                        connector = doc.to_dict()
                        _COMPANY_CONNECTORS[company_id] = connector
            except Exception as e:
                logger.warning("Could not query Firestore for connector", error=str(e))

        if not connector:
            # Fallback for demo: if demo_company, return demo data response so agent can answer
            if company_id == "demo_company":
                logger.info("Using demo order lookup simulation for demo_company")
                return {
                    "success": True,
                    "simulated": True,
                    "data": [
                        {
                            "order_id": "ZMT1003",
                            "status": "Delivered",
                            "items": "VoxAide Wireless Noise-Cancelling Headset",
                            "total": "$149.00",
                            "carrier": "FedEx",
                            "tracking_number": "TRK94829103",
                            "estimated_delivery": "Yesterday at 3:15 PM"
                        }
                    ]
                }
            return {
                "success": False,
                "error": "No connected PostgreSQL database found for this company. Please configure one in the Dashboard."
            }

        allowed_tables = connector.get("allowed_tables")
        return postgres_service.execute_safe_query(connector, sql_query, allowed_tables=allowed_tables)

# Register database tool with global registry
tool_registry.register(QueryCompanyDatabaseTool())
