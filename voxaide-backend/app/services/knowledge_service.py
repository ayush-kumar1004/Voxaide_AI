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

        # 6. Persist document metadata
        db = get_firestore_client()
        if db:
            try:
                db.collection("documents").document(doc.id).set(doc.model_dump())
            except Exception as e:
                logger.error("Error saving document to Firestore", error=str(e), doc_id=doc.id)

        self._docs_mem[doc.id] = doc.model_dump()
        logger.info(
            "Document ingested and indexed successfully",
            company_id=company_id,
            document_id=doc.id,
            filename=filename,
            chunks=len(chunks)
        )
        return doc

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

        return self.vector_store.similarity_search(
            company_id=company_id,
            query=query,
            top_k=top_k
        )

# Global knowledge service instance
knowledge_service = KnowledgeService()
