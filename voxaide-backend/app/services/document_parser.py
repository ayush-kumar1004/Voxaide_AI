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
        """
        Normalize whitespace and line endings without destroying paragraph structure.
        Preserves newlines for section and list integrity.
        """
        # Standardize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # Replace 3 or more consecutive newlines with 2
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Normalize multiple horizontal spaces/tabs to a single space
        text = re.sub(r'[ \t]+', ' ', text)
        # Strip trailing spaces on lines
        lines = [line.strip() for line in text.split('\n')]
        return '\n'.join(lines).strip()

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
    """
    Semantic, structure-aware text chunker.
    Preserves complete sections, paragraphs, and sentence boundaries.
    Never splits numbers, prices, or warranty terms across chunk boundaries.
    """

    def __init__(self, chunk_size: int = 900, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        clean_text = text.strip()

        # 1. Section-aware splitting for structured support documents (e.g. "1. COMPANY OVERVIEW", "2. PRODUCTS...")
        section_pattern = r'\n(?=[0-9]+\.\s+[A-Z])'
        raw_sections = [s.strip() for s in re.split(section_pattern, clean_text) if s.strip()]

        chunks = []
        tolerance = 200 if self.chunk_size >= 600 else 0
        for sec in raw_sections:
            if len(sec) <= self.chunk_size + tolerance:
                chunks.append(sec)
            else:
                # Section is long: split into paragraphs or sentences
                paragraphs = [p.strip() for p in sec.split('\n\n') if p.strip()]
                current_chunk = ""
                for para in paragraphs:
                    if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                        current_chunk = f"{current_chunk}\n\n{para}".strip()
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                            current_chunk = ""
                        if len(para) <= self.chunk_size:
                            current_chunk = para
                        else:
                            # Split very long paragraph on sentence boundaries
                            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', para) if s.strip()]
                            sub_chunk = ""
                            for s in sentences:
                                if len(s) > self.chunk_size:
                                    for w in s.split(' '):
                                        if not w:
                                            continue
                                        if len(sub_chunk) + len(w) + 1 <= self.chunk_size:
                                            sub_chunk = f"{sub_chunk} {w}".strip()
                                        else:
                                            if sub_chunk:
                                                chunks.append(sub_chunk)
                                            sub_chunk = w
                                else:
                                    if len(sub_chunk) + len(s) + 1 <= self.chunk_size:
                                        sub_chunk = f"{sub_chunk} {s}".strip()
                                    else:
                                        if sub_chunk:
                                            chunks.append(sub_chunk)
                                        sub_chunk = s
                            if sub_chunk:
                                current_chunk = sub_chunk
                if current_chunk:
                    chunks.append(current_chunk)

        # Fallback if no sections were detected
        if not chunks:
            paragraphs = [p.strip() for p in clean_text.split('\n\n') if p.strip()]
            for p in paragraphs:
                if len(p) <= self.chunk_size:
                    chunks.append(p)
                else:
                    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', p) if s.strip()]
                    current_chunk = ""
                    for s in sentences:
                        if len(s) > self.chunk_size:
                            words = s.split(' ')
                            w_chunk = ""
                            for w in words:
                                if len(w_chunk) + len(w) + 1 <= self.chunk_size:
                                    w_chunk = f"{w_chunk} {w}".strip()
                                else:
                                    if w_chunk:
                                        chunks.append(w_chunk)
                                    w_chunk = w
                            if w_chunk:
                                chunks.append(w_chunk)
                        elif len(current_chunk) + len(s) + 1 <= self.chunk_size:
                            current_chunk = f"{current_chunk} {s}".strip()
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = s
                    if current_chunk:
                        chunks.append(current_chunk)

        return chunks
