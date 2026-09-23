from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid

class Document(BaseModel):
    """Metadata for an uploaded company knowledge document."""
    id: str = Field(default_factory=lambda: f"doc_{uuid.uuid4().hex[:8]}")
    company_id: str
    filename: str
    file_type: str  # pdf, txt, docx, csv
    storage_path: Optional[str] = None
    status: str = "indexed"  # uploaded, processing, indexed, failed
    checksum: Optional[str] = None
    uploaded_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    processed_at: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    chunk_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentChunk(BaseModel):
    """A semantic chunk extracted from a document with tenant scoping."""
    id: str = Field(default_factory=lambda: f"chk_{uuid.uuid4().hex[:10]}")
    document_id: str
    company_id: str
    chunk_index: int
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding_ref: Optional[str] = None
