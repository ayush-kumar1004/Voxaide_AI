import re
from typing import Dict, Any, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.logging import logger

DANGEROUS_SQL_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|GRANT|REVOKE|EXEC|EXECUTE|CREATE)\b",
    re.IGNORECASE
)

class PostgresConnectorService:
    """
    Secure, read-only PostgreSQL database connector service.
    Allows AI agents to inspect schemas and execute safe SELECT queries.
    """

    @staticmethod
    def parse_conn_params(params: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts standard psycopg2 connection parameters."""
        conn_str = params.get("connection_string", "").strip()
        if conn_str and conn_str.startswith("postgres"):
            return {"dsn": conn_str, "connect_timeout": 5}

        return {
            "host": params.get("host", "localhost"),
            "port": int(params.get("port", 5432)),
            "dbname": params.get("dbname") or params.get("database", "postgres"),
            "user": params.get("user") or params.get("username", "postgres"),
            "password": params.get("password", ""),
            "sslmode": params.get("sslmode", "prefer"),
            "connect_timeout": 5
        }

    def test_connection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Tests connectivity and returns visible public tables."""
        conn_args = self.parse_conn_params(params)
        conn = None
        try:
            conn = psycopg2.connect(**conn_args)
            with conn.cursor() as cur:
                cur.execute("SET statement_timeout = '4000';")
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                      AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """)
                tables = [row[0] for row in cur.fetchall()]

            return {
                "success": True,
                "message": f"Successfully connected to PostgreSQL! Found {len(tables)} table(s).",
                "tables": tables
            }
        except Exception as e:
            logger.warning("Postgres connection test failed", error=str(e))
            return {
                "success": False,
                "error": f"Connection failed: {str(e)}"
            }
        finally:
            if conn:
                conn.close()

    def get_table_schemas(self, params: Dict[str, Any], allowed_tables: Optional[List[str]] = None) -> Dict[str, Any]:
        """Returns column names and types for the specified tables."""
        conn_args = self.parse_conn_params(params)
        conn = None
        schemas = {}
        try:
            conn = psycopg2.connect(**conn_args)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SET statement_timeout = '4000';")
                query = """
                    SELECT table_name, column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public'
                """
                if allowed_tables:
                    cur.execute(query + " AND table_name = ANY(%s) ORDER BY table_name, ordinal_position;", (allowed_tables,))
                else:
                    cur.execute(query + " ORDER BY table_name, ordinal_position;")

                for row in cur.fetchall():
                    tbl = row["table_name"]
                    if tbl not in schemas:
                        schemas[tbl] = []
                    schemas[tbl].append(f"{row['column_name']} ({row['data_type']})")

            return {"success": True, "schemas": schemas}
        except Exception as e:
            logger.warning("Failed to fetch Postgres schema", error=str(e))
            return {"success": False, "error": str(e), "schemas": {}}
        finally:
            if conn:
                conn.close()

    def execute_safe_query(self, params: Dict[str, Any], sql: str, allowed_tables: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Executes a strictly read-only SQL query with timeout and row limit constraints.
        """
        clean_sql = sql.strip().rstrip(";")

        # Security check 1: Must start with SELECT or WITH
        if not (clean_sql.upper().startswith("SELECT") or clean_sql.upper().startswith("WITH")):
            return {"success": False, "error": "Security violation: Only read-only SELECT queries are allowed."}

        # Security check 2: No destructive keywords
        if DANGEROUS_SQL_PATTERN.search(clean_sql):
            return {"success": False, "error": "Security violation: Query contains forbidden modification keywords."}

        # Security check 3: Append LIMIT 25 if not already present
        if "LIMIT" not in clean_sql.upper():
            clean_sql += " LIMIT 25"

        conn_args = self.parse_conn_params(params)
        conn = None
        try:
            conn = psycopg2.connect(**conn_args)
            conn.set_session(readonly=True, autocommit=True)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SET statement_timeout = '3000';") # 3s timeout
                cur.execute(clean_sql)
                rows = cur.fetchall()

            # Convert rows to serializable dicts
            result_rows = [dict(r) for r in rows]
            return {
                "success": True,
                "row_count": len(result_rows),
                "data": result_rows
            }
        except Exception as e:
            logger.warning("Safe query execution failed", sql=clean_sql, error=str(e))
            return {"success": False, "error": f"Database query error: {str(e)}"}
        finally:
            if conn:
                conn.close()

# Global postgres connector instance
postgres_service = PostgresConnectorService()
