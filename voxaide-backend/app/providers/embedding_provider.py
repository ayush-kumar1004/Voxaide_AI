import os
import hashlib
import math
from typing import List, Optional
import google.generativeai as genai
from app.providers.base import EmbeddingProvider
from app.core.logging import logger

class GeminiEmbeddingProvider(EmbeddingProvider):
    """
    Embedding provider using Google's text-embedding-004 model.
    Falls back to deterministic hash-embeddings in test environments.
    """

    def __init__(self, model_name: str = "models/text-embedding-004", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def _deterministic_mock_embed(self, text: str, dim: int = 768) -> List[float]:
        """Fast offline pseudo-embedding for testing and cost-free local CI."""
        words = text.lower().split()
        vec = [0.0] * dim
        for w in words:
            # Deterministic bucket hash
            h = int(hashlib.md5(w.encode('utf-8')).hexdigest(), 16) % dim
            vec[h] += 1.0

        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [round(x / norm, 6) for x in vec]

    def embed_text(self, text: str) -> List[float]:
        if os.environ.get("APP_ENV") == "testing" or not self.api_key:
            return self._deterministic_mock_embed(text)

        try:
            res = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_query"
            )
            return res.get("embedding", [])
        except Exception as e:
            logger.warning("Gemini embedding failed, using local fallback", error=str(e))
            return self._deterministic_mock_embed(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if os.environ.get("APP_ENV") == "testing" or not self.api_key:
            return [self._deterministic_mock_embed(t) for t in texts]

        try:
            res = genai.embed_content(
                model=self.model_name,
                content=texts,
                task_type="retrieval_document"
            )
            return res.get("embedding", [])
        except Exception as e:
            logger.warning("Batch Gemini embedding failed, using local fallback", error=str(e))
            return [self._deterministic_mock_embed(t) for t in texts]
