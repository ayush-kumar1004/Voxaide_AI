import os
import io
import json
import pytest
import sys
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["APP_ENV"] = "testing"

from app import app
from app.services.company_service import company_service
from app.services.knowledge_service import knowledge_service, KnowledgeService
from app.services.document_parser import DocumentParser, TextChunker
from app.providers.chroma_vector_store import ChromaVectorStore
from app.providers.embedding_provider import GeminiEmbeddingProvider
from app.services.agent_orchestrator import AgentOrchestrator, AgentRequest
from app.providers.base import LLMProvider, LLMResponse

# ----------------- Helpers to generate test files in memory -----------------

def create_sample_pdf_bytes(text: str) -> bytes:
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    # pypdf blank page metadata or annotation text
    buf = io.BytesIO()
    # To embed actual extractable text in a minimal PDF:
    # Use standard minimalist PDF content stream with text operator
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources <</Font <</F1 5 0 R>>>>>> endobj\n"
        b"4 0 obj <</Length " + str(len(text) + 40).encode('utf-8') + b">> stream\n"
        b"BT /F1 12 Tf 100 700 Td (" + text.encode('latin-1', errors='replace') + b") Tj ET\n"
        b"endstream\nendobj\n"
        b"5 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \n0000000244 00000 n \n0000000350 00000 n \n"
        b"trailer <</Size 6 /Root 1 0 R>>\nstartxref\n428\n%%EOF\n"
    )
    return pdf_content

def create_sample_docx_bytes(paragraphs: List[str]) -> bytes:
    import docx
    doc = docx.Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()

def create_sample_csv_bytes(rows: List[List[str]]) -> bytes:
    buf = io.StringIO()
    import csv
    writer = csv.writer(buf)
    for r in rows:
        writer.writerow(r)
    return buf.getvalue().encode('utf-8')

def create_sample_txt_bytes(text: str) -> bytes:
    return text.encode('utf-8')

# ----------------- Test Fixtures -----------------

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(scope="module")
def isolated_knowledge_service(tmp_path_factory):
    """Provides a fresh isolated ChromaDB vector store for this test module."""
    temp_dir = tmp_path_factory.mktemp("chroma_test")
    chroma_store = ChromaVectorStore(
        persist_directory=str(temp_dir),
        embedding_provider=GeminiEmbeddingProvider(),
        collection_name="test_knowledge_collection"
    )
    return KnowledgeService(vector_store=chroma_store)

@pytest.fixture(scope="module")
def two_companies():

    comp_a = company_service.create_company(
        name="SmileCare Dental",
        owner_user_id="user_owner_a"
    )
    comp_b = company_service.create_company(
        name="Urban Pets Clinic",
        owner_user_id="user_owner_b"
    )
    return {"comp_a": comp_a, "comp_b": comp_b}

# ----------------- Mandatory Tests -----------------

def test_1_pdf_ingestion(isolated_knowledge_service, two_companies):
    """Test 1: Ingest and parse PDF document."""
    comp_id = two_companies["comp_a"].id
    pdf_bytes = create_sample_pdf_bytes("SmileCare Root Canal therapy starts at 5000 rupees.")

    doc = isolated_knowledge_service.ingest_document(
        company_id=comp_id,
        filename="pricing_root_canal.pdf",
        content_bytes=pdf_bytes
    )

    assert doc.file_type == "pdf"
    assert doc.status == "indexed"
    assert doc.chunk_count > 0

def test_2_txt_ingestion(isolated_knowledge_service, two_companies):
    """Test 2: Ingest and parse TXT document."""
    comp_id = two_companies["comp_a"].id
    txt_bytes = create_sample_txt_bytes("Dental clinic is open Monday to Saturday from 9 AM to 7 PM.")

    doc = isolated_knowledge_service.ingest_document(
        company_id=comp_id,
        filename="hours_policy.txt",
        content_bytes=txt_bytes
    )

    assert doc.file_type == "txt"
    assert doc.status == "indexed"
    assert doc.chunk_count > 0

def test_3_docx_ingestion(isolated_knowledge_service, two_companies):
    """Test 3: Ingest and parse DOCX document."""
    comp_id = two_companies["comp_a"].id
    docx_bytes = create_sample_docx_bytes([
        "Appointment Policy for SmileCare Dental.",
        "Cancellations must be made at least 24 hours prior to appointment."
    ])

    doc = isolated_knowledge_service.ingest_document(
        company_id=comp_id,
        filename="appointment_policy.docx",
        content_bytes=docx_bytes
    )

    assert doc.file_type == "docx"
    assert doc.status == "indexed"
    assert doc.chunk_count > 0

def test_4_csv_ingestion(isolated_knowledge_service, two_companies):
    """Test 4: Ingest and parse CSV document."""
    comp_id = two_companies["comp_a"].id
    csv_bytes = create_sample_csv_bytes([
        ["Service", "Price", "Duration"],
        ["Teeth Cleaning", "1500 INR", "45 mins"],
        ["Dental Implants", "25000 INR", "90 mins"]
    ])

    doc = isolated_knowledge_service.ingest_document(
        company_id=comp_id,
        filename="services_catalog.csv",
        content_bytes=csv_bytes
    )

    assert doc.file_type == "csv"
    assert doc.status == "indexed"
    assert doc.chunk_count > 0

def test_5_chunking():
    """Test 5: Verify sliding-window text chunking and overlap."""
    chunker = TextChunker(chunk_size=50, chunk_overlap=10)
    sample_text = "The quick brown fox jumps over the lazy dog. " * 3
    chunks = chunker.chunk(sample_text)

    assert len(chunks) > 1
    assert all(len(c) <= 50 for c in chunks)

def test_6_embedding():
    """Test 6: Embedding provider produces normalized vectors."""
    provider = GeminiEmbeddingProvider()
    vec = provider.embed_text("Root canal treatment cost")
    assert isinstance(vec, list)
    assert len(vec) == 768

def test_7_retrieval(isolated_knowledge_service, two_companies):
    """Test 7: Semantic retrieval returns relevant chunks."""
    comp_id = two_companies["comp_a"].id
    results = isolated_knowledge_service.search(
        company_id=comp_id,
        query="What is the price of teeth cleaning?",
        top_k=2
    )

    assert len(results) > 0
    assert "text" in results[0]
    assert "Teeth Cleaning" in results[0]["text"] or "Root Canal" in results[0]["text"]

def test_8_cross_tenant_isolation(isolated_knowledge_service, two_companies):
    """Test 8: CRITICAL: Company A documents MUST NEVER be retrieved by Company B."""
    comp_a_id = two_companies["comp_a"].id
    comp_b_id = two_companies["comp_b"].id

    # Ingest confidential document into Company B only
    vet_doc_bytes = create_sample_txt_bytes("Urban Pets rabies vaccination costs 800 rupees.")
    isolated_knowledge_service.ingest_document(
        company_id=comp_b_id,
        filename="vet_pricing.txt",
        content_bytes=vet_doc_bytes
    )

    # Search under Company A for Company B's confidential service
    results_a = isolated_knowledge_service.search(
        company_id=comp_a_id,
        query="rabies vaccination",
        top_k=5
    )

    # Company A MUST NOT retrieve any chunks from Company B
    for res in results_a:
        assert "rabies" not in res["text"].lower()
        assert res.get("document_name") != "vet_pricing.txt"

    # Search under Company B MUST retrieve it
    results_b = isolated_knowledge_service.search(
        company_id=comp_b_id,
        query="rabies vaccination",
        top_k=5
    )
    assert len(results_b) > 0
    assert "rabies" in results_b[0]["text"].lower()

def test_9_deleted_document_no_longer_retrieved(isolated_knowledge_service, two_companies):
    """Test 9: Deleted document chunks are purged from vector store."""
    comp_id = two_companies["comp_a"].id
    temp_bytes = create_sample_txt_bytes("Temporary promotional discount code: SMILE50 for 50 percent off.")
    doc = isolated_knowledge_service.ingest_document(
        company_id=comp_id,
        filename="promo.txt",
        content_bytes=temp_bytes
    )

    # Verify present in retrieval
    search_before = isolated_knowledge_service.search(comp_id, "SMILE50", top_k=2)
    assert any("SMILE50" in r["text"] for r in search_before)

    # Delete document
    success = isolated_knowledge_service.delete_document(comp_id, doc.id)
    assert success is True

    # Verify absent from retrieval
    search_after = isolated_knowledge_service.search(comp_id, "SMILE50", top_k=2)
    assert not any("SMILE50" in r["text"] for r in search_after)

def test_10_source_metadata_returned(isolated_knowledge_service, two_companies):
    """Test 10: Retrieved chunks expose document_id, document_name, chunk_id, relevance_score."""
    comp_id = two_companies["comp_a"].id
    results = isolated_knowledge_service.search(comp_id, "cleaning", top_k=1)

    assert len(results) > 0
    chunk = results[0]
    assert "document_id" in chunk
    assert "document_name" in chunk
    assert "chunk_id" in chunk
    assert "relevance_score" in chunk
    assert chunk["relevance_score"] > 0

class GroundedMockLLM(LLMProvider):
    """Mock LLM that verifies system prompt contains retrieved chunks and enforces groundedness."""
    def __init__(self):
        self.last_system_instruction = ""
        self.last_prompt = ""

    def generate(self, prompt: str, system_instruction: str = "", **kwargs) -> LLMResponse:
        self.last_prompt = prompt
        self.last_system_instruction = system_instruction

        if "teeth cleaning" in prompt.lower() and "1500 INR" in system_instruction:
            return LLMResponse(content="According to SmileCare's records, teeth cleaning costs 1500 INR.")
        else:
            return LLMResponse(content="I do not have enough information in our company records to answer that question.")


def test_11_agent_answers_using_retrieved_context(isolated_knowledge_service, two_companies):
    """Test 11: AgentOrchestrator uses retrieved RAG chunks in system prompt and answers with evidence."""
    comp_a = two_companies["comp_a"]
    mock_llm = GroundedMockLLM()

    orchestrator = AgentOrchestrator(
        llm_provider=mock_llm,
        company_svc=company_service,
        knowledge_svc=isolated_knowledge_service
    )

    req = AgentRequest(
        company_id=comp_a.id,
        message="How much does teeth cleaning cost?"
    )

    res = orchestrator.process(req)

    assert "1500 INR" in res.text
    assert len(res.sources) > 0
    assert any(s["document_name"] == "services_catalog.csv" for s in res.sources)
    assert "VERIFIED BUSINESS KNOWLEDGE" in mock_llm.last_system_instruction

def test_12_agent_refuses_to_invent_missing_information(isolated_knowledge_service, two_companies):
    """Test 12: When knowledge is absent, agent refuses to invent hallucinated answers."""
    comp_a = two_companies["comp_a"]
    mock_llm = GroundedMockLLM()

    orchestrator = AgentOrchestrator(
        llm_provider=mock_llm,
        company_svc=company_service,
        knowledge_svc=isolated_knowledge_service
    )

    req = AgentRequest(
        company_id=comp_a.id,
        message="Do you do rocket propulsion maintenance?"
    )

    res = orchestrator.process(req)

    assert "do not have enough information" in res.text.lower()
