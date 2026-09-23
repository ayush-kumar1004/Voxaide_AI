import io
import csv
import re
from typing import Tuple
from app.core.logging import logger

class DocumentParser:
    """Extracts and normalizes raw text from PDF, TXT, DOCX, and CSV files."""

    ALLOWED_EXTENSIONS = {"pdf", "txt", "docx", "csv"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    @classmethod
    def clean_text(cls, text: str) -> str:
        """Normalize whitespace and strip unprintable characters."""
        text = re.sub(r'[\r\n\t]+', ' ', text)
        text = re.sub(r'\s{2,}', ' ', text)
        return text.strip()

    @classmethod
    def parse(cls, filename: str, content_bytes: bytes) -> Tuple[str, str]:
        """
        Parses binary file bytes into normalized text.
        Returns (file_type, normalized_text).
        """
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in cls.ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file format '.{ext}'. Supported formats: {', '.join(cls.ALLOWED_EXTENSIONS)}")

        if len(content_bytes) > cls.MAX_FILE_SIZE:
            raise ValueError(f"File exceeds maximum allowed size of {cls.MAX_FILE_SIZE // (1024*1024)}MB.")

        extracted_text = ""

        try:
            if ext == "txt":
                try:
                    extracted_text = content_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    extracted_text = content_bytes.decode("latin-1", errors="ignore")

            elif ext == "pdf":
                from pypdf import PdfReader
                stream = io.BytesIO(content_bytes)
                reader = PdfReader(stream)
                pages = []
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        pages.append(page_text)
                extracted_text = "\n".join(pages)

            elif ext == "docx":
                import docx
                stream = io.BytesIO(content_bytes)
                doc = docx.Document(stream)
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                extracted_text = "\n".join(paragraphs)

            elif ext == "csv":
                text_stream = io.StringIO(content_bytes.decode("utf-8", errors="ignore"))
                reader = csv.reader(text_stream)
                rows = []
                for row in reader:
                    if any(cell.strip() for cell in row):
                        rows.append(" | ".join(row))
                extracted_text = "\n".join(rows)

        except Exception as e:
            logger.error("Failed to parse document", filename=filename, error=str(e))
            raise ValueError(f"Failed to parse {filename}: {str(e)}")

        cleaned = cls.clean_text(extracted_text)
        if not cleaned:
            raise ValueError(f"No readable text could be extracted from {filename}.")

        return ext, cleaned

class TextChunker:
    """Chunks normalized text with configurable size and overlap."""

    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(chunk_text)
            start += self.chunk_size - self.chunk_overlap
            if start >= text_len or end >= text_len:
                break

        return chunks
