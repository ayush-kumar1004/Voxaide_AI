import os
from typing import List, Dict, Any, Optional
import chromadb
from app.providers.base import VectorStore, EmbeddingProvider
from app.providers.embedding_provider import GeminiEmbeddingProvider
from app.core.logging import logger

class ChromaVectorStore(VectorStore):
    """
    ChromaDB vector store implementation with strict company_id isolation.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        collection_name: str = "voxaide_knowledge"
    ):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.persist_directory = persist_directory or os.path.join(base_dir, "data", "chroma")
        os.makedirs(self.persist_directory, exist_ok=True)

        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.embedding_provider = embedding_provider or GeminiEmbeddingProvider()
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Multi-tenant company knowledge base"}
        )

    def add_documents(self, company_id: str, documents: List[Dict[str, Any]]):
        """
        Embed and index chunks into the collection.
        CRITICAL: Validates that every chunk has metadata['company_id'] == company_id.
        """
        if not documents:
            return

        ids = []
        texts = []
        metadatas = []

        for doc in documents:
            chunk_id = doc["id"]
            text = doc["text"]
            meta = doc.get("metadata", {}).copy()
            meta["company_id"] = company_id
            if "document_id" in doc:
                meta["document_id"] = doc["document_id"]
            if "document_name" in doc:
                meta["document_name"] = doc["document_name"]
            if "chunk_index" in doc:
                meta["chunk_index"] = int(doc["chunk_index"])

            ids.append(chunk_id)
            texts.append(text)
            metadatas.append(meta)

        embeddings = self.embedding_provider.embed_documents(texts)

        self.collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings
        )
        logger.info(f"Indexed {len(ids)} chunks into ChromaDB for company {company_id}")

    def similarity_search(
        self,
        company_id: str,
        query: str,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant document chunks strictly scoped by company_id.
        """
        if not company_id:
            raise ValueError("company_id is required for similarity search.")

        query_embedding = self.embedding_provider.embed_text(query)

        # Query ChromaDB with MANDATORY company_id filter
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"company_id": company_id}
        )

        formatted = []
        if results and results.get("documents") and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            ids = results["ids"][0] if results.get("ids") else [""] * len(docs)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

            for doc_text, meta, chunk_id, dist in zip(docs, metas, ids, distances):
                # Calculate simple similarity score from distance (L2 or cosine)
                relevance = round(1.0 / (1.0 + float(dist)), 4) if dist is not None else 1.0
                formatted.append({
                    "text": doc_text,
                    "content": doc_text,  # alias for prompt builder
                    "document_name": meta.get("document_name", "Document"),
                    "source": meta.get("document_name", "Document"),
                    "document_id": meta.get("document_id", ""),
                    "chunk_id": chunk_id,
                    "id": chunk_id,
                    "relevance_score": relevance,
                    "metadata": meta
                })

        return formatted

    def delete_document(self, company_id: str, document_id: str):
        """Delete all chunks belonging to document_id under company_id."""
        self.collection.delete(
            where={
                "$and": [
                    {"company_id": company_id},
                    {"document_id": document_id}
                ]
            }
        )
        logger.info(f"Deleted document {document_id} chunks for company {company_id}")

    def delete_company_namespace(self, company_id: str):
        """Delete all knowledge chunks belonging to company_id."""
        self.collection.delete(where={"company_id": company_id})
        logger.info(f"Deleted entire namespace for company {company_id}")
