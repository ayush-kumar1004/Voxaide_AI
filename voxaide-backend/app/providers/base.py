from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class ToolCallRequest:
    name: str
    arguments: Dict[str, Any]
    id: Optional[str] = None

@dataclass
class LLMResponse:
    content: str
    tool_calls: List[ToolCallRequest] = field(default_factory=list)
    finish_reason: str = "stop"
    usage_metadata: Dict[str, Any] = field(default_factory=dict)

class LLMProvider(ABC):
    """Abstract interface for LLM backends (Gemini, OpenAI, Anthropic, Local)."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.3
    ) -> LLMResponse:
        """Generate a response given a prompt, history, and optional tool schemas."""
        pass

class EmbeddingProvider(ABC):
    """Abstract interface for text embedding models."""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass

class VectorStore(ABC):
    """Abstract interface for company-isolated vector databases."""

    @abstractmethod
    def add_documents(self, company_id: str, documents: List[Dict[str, Any]]):
        pass

    @abstractmethod
    def similarity_search(
        self,
        company_id: str,
        query: str,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete_document(self, company_id: str, document_id: str):
        pass

    @abstractmethod
    def delete_company_namespace(self, company_id: str):
        pass
