from flask import Blueprint, request, jsonify
from app.core.security import require_auth, require_company_access
from app.services.knowledge_service import knowledge_service
from app.core.logging import logger

knowledge_bp = Blueprint("knowledge_routes", __name__, url_prefix="/api/companies")

@knowledge_bp.route("/<company_id>/knowledge/upload", methods=["POST"])
@require_auth
@require_company_access("company_id")
def upload_document(company_id: str):
    """
    Upload, parse, chunk, and index a company knowledge document into ChromaDB.
    Supported: PDF, TXT, DOCX, CSV (<10MB).
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Expected 'file' multipart field."}), 400

    uploaded_file = request.files["file"]
    if not uploaded_file.filename:
        return jsonify({"error": "No file selected."}), 400

    filename = uploaded_file.filename
    content_bytes = uploaded_file.read()

    try:
        doc = knowledge_service.ingest_document(
            company_id=company_id,
            filename=filename,
            content_bytes=content_bytes
        )
        return jsonify({
            "message": f"Document '{filename}' successfully ingested and indexed.",
            "document": doc.model_dump()
        }), 201

    except ValueError as val_err:
        return jsonify({"error": str(val_err)}), 400
    except Exception as e:
        logger.error("Document upload failed", error=str(e), company_id=company_id, filename=filename)
        return jsonify({"error": f"Failed to ingest document: {str(e)}"}), 500

@knowledge_bp.route("/<company_id>/knowledge/documents", methods=["GET"])
@require_auth
@require_company_access("company_id")
def list_documents(company_id: str):
    """List all indexed documents for the company."""
    docs = knowledge_service.list_documents(company_id)
    return jsonify({"documents": [d.model_dump() for d in docs]}), 200

@knowledge_bp.route("/<company_id>/knowledge/documents/<document_id>", methods=["DELETE"])
@require_auth
@require_company_access("company_id")
def delete_document(company_id: str, document_id: str):
    """Delete a document and purge all its vectors from the vector store."""
    success = knowledge_service.delete_document(company_id, document_id)
    if not success:
        return jsonify({"error": "Document not found or access denied."}), 404

    return jsonify({"message": f"Document '{document_id}' and all associated vector chunks deleted."}), 200

@knowledge_bp.route("/<company_id>/knowledge/search", methods=["POST"])
@require_auth
@require_company_access("company_id")
def search_knowledge(company_id: str):
    """Debug & validation endpoint for testing company-isolated vector retrieval."""
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    top_k = int(data.get("top_k", 4))

    if not query:
        return jsonify({"error": "Query cannot be empty."}), 400

    results = knowledge_service.search(company_id=company_id, query=query, top_k=top_k)
    return jsonify({
        "company_id": company_id,
        "query": query,
        "results_count": len(results),
        "results": results
    }), 200
