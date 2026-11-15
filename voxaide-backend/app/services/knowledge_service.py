import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.models.document import Document
from app.services.document_parser import DocumentParser, TextChunker
from app.providers.chroma_vector_store import ChromaVectorStore
from app.core.database import get_firestore_client
from app.core.logging import logger

class KnowledgeService:
    """
    Production-oriented Knowledge Base & RAG Ingestion Service.
    CRITICAL TENANT ISOLATION:
    - Every ingested chunk is tagged with company_id.
    - Every retrieval filters strictly by company_id.
    """

    def __init__(self, vector_store=None):
        self.vector_store = vector_store or ChromaVectorStore()
        self.chunker = TextChunker(chunk_size=600, chunk_overlap=100)
        # In-memory document registry fallback for fast tests and decoupled execution
        self._docs_mem: Dict[str, Dict[str, Any]] = {}

    def _compute_checksum(self, content_bytes: bytes) -> str:
        return hashlib.sha256(content_bytes).hexdigest()

    def ingest_document(
        self,
        company_id: str,
        filename: str,
        content_bytes: bytes,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        if not company_id:
            raise ValueError("company_id is required for document ingestion.")

        # 1. Parse and clean text
        file_type, cleaned_text = DocumentParser.parse(filename, content_bytes)
        checksum = self._compute_checksum(content_bytes)

        # 2. Create document record
        doc = Document(
            company_id=company_id,
            filename=filename,
            file_type=file_type,
            status="processing",
            checksum=checksum,
            metadata=metadata or {}
        )

        # 3. Chunk text
        chunks = self.chunker.chunk(cleaned_text)
        doc.chunk_count = len(chunks)

        # 4. Prepare chunk objects for vector store
        chunk_objects = []
        for i, chunk_text in enumerate(chunks):
            chunk_id = f"{doc.id}_chk_{i}"
            chunk_objects.append({
                "id": chunk_id,
                "text": chunk_text,
                "document_id": doc.id,
                "document_name": filename,
                "chunk_index": i,
                "metadata": {
                    "company_id": company_id,
                    "document_id": doc.id,
                    "document_name": filename,
                    "file_type": file_type,
                    "chunk_index": i
                }
            })

        # 5. Index into Vector Store
        self.vector_store.add_documents(company_id=company_id, documents=chunk_objects)

        doc.status = "indexed"
        doc.processed_at = datetime.now(timezone.utc).isoformat()

        # 6. Persist document metadata and chunk payload to survive container restarts
        doc_dict = doc.model_dump()
        doc_dict["chunks_payload"] = [
            {"id": c["id"], "text": c["text"], "chunk_index": c["chunk_index"], "metadata": c["metadata"]}
            for c in chunk_objects
        ]

        db = get_firestore_client()
        if db:
            try:
                db.collection("documents").document(doc.id).set(doc_dict)
            except Exception as e:
                logger.error("Error saving document to Firestore", error=str(e), doc_id=doc.id)

        self._docs_mem[doc.id] = doc_dict

        # 7. Automatically sync tenant company profile and agent persona from knowledge base
        self._sync_company_profile_from_document(company_id, cleaned_text)

        logger.info(
            "Document ingested and indexed successfully",
            company_id=company_id,
            document_id=doc.id,
            filename=filename,
            chunks=len(chunks)
        )
        return doc

    def _sync_company_profile_from_document(self, company_id: str, text: str):
        """
        Extracts verified company branding and updates the company profile and agent persona.
        Ensures tenant identity dynamically matches uploaded business knowledge.
        """
        import re
        from app.services.company_service import company_service
        from app.core.database import get_firestore_client

        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if not lines:
            return

        detected_name = None
        first_line = lines[0]
        if "—" in first_line:
            candidate = first_line.split("—")[0].strip().title()
            if len(candidate) > 2 and "Knowledge" not in candidate:
                detected_name = candidate
        elif "-" in first_line:
            candidate = first_line.split("-")[0].strip().title()
            if len(candidate) > 2 and "Knowledge" not in candidate:
                detected_name = candidate

        match_co = re.search(r'([A-Z][a-zA-Z0-9\s]+(?:Appliances|Enterprises|Solutions|Services|Corp|Inc|Company|Retailer))\s+is\s+a\b', text)
        if match_co:
            detected_name = match_co.group(1).strip()

        if detected_name:
            if company_id in company_service._companies_mem:
                company_service._companies_mem[company_id]["name"] = detected_name

            company_service.update_agent_config(
                company_id,
                agent_name=f"{detected_name} Support Assistant"
            )

            db = get_firestore_client()
            if db:
                try:
                    db.collection("companies").document(company_id).update({"name": detected_name})
                except Exception:
                    pass

            logger.info("Updated company brand identity from knowledge base", company_id=company_id, name=detected_name)

    def list_documents(self, company_id: str) -> List[Document]:
        """List all documents for a company."""
        db = get_firestore_client()
        docs = []
        if db:
            try:
                records = db.collection("documents").where("company_id", "==", company_id).get()
                docs = [Document(**r.to_dict()) for r in records]
                if docs:
                    return docs
            except Exception as e:
                logger.error("Error fetching documents from Firestore", error=str(e))

        return [
            Document(**data) for data in self._docs_mem.values()
            if data.get("company_id") == company_id
        ]

    def get_document(self, company_id: str, document_id: str) -> Optional[Document]:
        db = get_firestore_client()
        if db:
            try:
                rec = db.collection("documents").document(document_id).get()
                if rec.exists:
                    data = rec.to_dict()
                    if data.get("company_id") == company_id:
                        return Document(**data)
            except Exception as e:
                logger.error("Error fetching document from Firestore", error=str(e))

        data = self._docs_mem.get(document_id)
        if data and data.get("company_id") == company_id:
            return Document(**data)
        return None

    def delete_document(self, company_id: str, document_id: str) -> bool:
        """Delete document from registry and purge its vectors from ChromaDB."""
        doc = self.get_document(company_id, document_id)
        if not doc:
            return False

        # Purge from vector store
        self.vector_store.delete_document(company_id=company_id, document_id=document_id)

        # Purge from database
        db = get_firestore_client()
        if db:
            try:
                db.collection("documents").document(document_id).delete()
            except Exception as e:
                logger.error("Error deleting document from Firestore", error=str(e))

        if document_id in self._docs_mem:
            del self._docs_mem[document_id]

        logger.info("Document deleted from knowledge base", company_id=company_id, document_id=document_id)
        return True

    def _maybe_rehydrate_from_firestore(self, company_id: str) -> bool:
        """Restores indexed vector chunks into ChromaDB if container was restarted."""
        db = get_firestore_client()
        if not db:
            return False

        try:
            records = db.collection("documents").where("company_id", "==", company_id).get()
            total_added = 0
            for r in records:
                d = r.to_dict()
                chunks = d.get("chunks_payload") or []
                if chunks:
                    self.vector_store.add_documents(company_id=company_id, documents=chunks)
                    total_added += len(chunks)
            if total_added > 0:
                logger.info(f"Re-hydrated {total_added} chunks into ChromaDB from Firestore for company {company_id}")
                return True
        except Exception as e:
            logger.warning("Could not re-hydrate documents from Firestore", error=str(e))
        return False

    def search(
        self,
        company_id: str,
        query: str,
        top_k: int = 4,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        RAG similarity search strictly scoped by company_id.
        """
        if not company_id:
            raise ValueError("company_id is mandatory for knowledge retrieval.")

        if not query or not query.strip():
            return []

        results = self.vector_store.similarity_search(
            company_id=company_id,
            query=query,
            top_k=top_k
        )

        if not results:
            if self._maybe_rehydrate_from_firestore(company_id):
                results = self.vector_store.similarity_search(
                    company_id=company_id,
                    query=query,
                    top_k=top_k
                )

        return results

# Global knowledge service instance
knowledge_service = KnowledgeService()
