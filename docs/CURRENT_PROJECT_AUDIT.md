# VoxAide AI - Current Project Audit

**Audit Date:** September 2026  
**Auditor:** Antigravity Senior Engineering Team  
**Workspace:** `e:\voxaide-main`  
**Target Goal:** Transform VoxAide into a polished, technically defensible, end-to-end multi-tenant AI Voice Customer Support Platform.

---

## 1. Executive Summary

VoxAide was started as a prototype for voice-enabled customer service using Firebase, React, Flask, and Google Gemini.
While the marketing landing pages and client-side Firebase authentication are well-designed and functional, the platform's core promises—specifically **RAG-based knowledge retrieval**, **multi-tenant company isolation**, and **Twilio phone integration**—are either missing, hardcoded, or completely mocked.

Additionally, the backend currently fails to start out-of-the-box due to an uninstalled dependency (`gtts`), and contains security vulnerabilities including plaintext password handling in unused Flask routes and exposed credentials in `.env`.

---

## 2. Repository Inventory & Component Status Matrix

| Layer / Feature | Declared in Code/Docs | Current Implementation State | Technical Reality & Diagnosis |
| :--- | :--- | :--- | :--- |
| **Frontend UI** | React + Vite + Tailwind | **WORKING** | 0 TypeScript errors (`tsc --noEmit` passes). Clean UI with shadcn/ui components. |
| **Frontend Routing** | React Router v6 | **PARTIALLY IMPLEMENTED** | Routes exist (`/dashboard`, `/customer-chat`, etc.), but navigation bar lacks links to them. |
| **User Authentication** | Firebase Auth | **PARTIALLY WORKING / SPLIT** | Frontend uses client-side Firebase Auth directly (`createUserWithEmailAndPassword`). Backend has redundant, unhashed `/api/signup` & `/api/login` endpoints storing plaintext passwords. |
| **Database (Firestore)** | Google Cloud Firestore | **WORKING (BASIC)** | Active Firebase project `voxaide`. Collections: `users`, `contacts`, `orders`. Lacks multi-tenant company schemas. |
| **Document Ingestion** | Support TXT, JSON, CSV | **MOCKED** | Dashboard file upload only updates local React component state. No file parsing, no chunking, no persistence. |
| **Vector Storage** | Not yet integrated | **MISSING** | No vector database installed (no Chroma, Pinecone, Qdrant, or FAISS). |
| **RAG Pipeline** | Company-specific Knowledge | **MISSING** | No document chunking, no embedding generation, no semantic search. Model responds from base LLM knowledge. |
| **AI LLM Engine** | Gemini 2.5 Flash | **PARTIALLY WORKING** | Gemini SDK configured. `/talk` endpoint passes audio and prompt to Gemini. |
| **AI Business Tools** | Firestore Tool Calling | **PARTIALLY IMPLEMENTED (HARDCODED)** | Functions `get_order_details` and `cancel_order` hardcoded for single order demo (`ZMT1003`). No appointment booking, no extensible tool registry. |
| **Speech-to-Text (STT)**| Voice Input | **PARTIALLY IMPLEMENTED** | Audio blob sent to Gemini multimodal audio endpoint. Browser mic recording is brittle (no text input fallback). |
| **Text-to-Speech (TTS)**| ElevenLabs / gTTS | **BROKEN** | `gtts` missing from Python environment causing startup crash. Audio files saved to local disk `static/audio`. |
| **Twilio Integration** | Twilio Voice Calls | **COMPLETELY MISSING** | Claimed in `README.md`, but 0 lines of Twilio code exist anywhere in the codebase. |
| **Multi-Tenancy** | Company Isolation | **MISSING** | No company models, no company ID namespace, no tenant isolation. |
| **Analytics & Logs** | Support Analytics | **MOCKED** | Dashboard metrics (156 queries, 94% resolution) and conversation table are hardcoded static data. |

---

## 3. Detailed Architecture Analysis

### Current Architecture

```
[Browser Client]
  │
  ├── React 18 UI (Vite @ port 8080)
  ├── Firebase Client SDK ──► Firebase Auth & Firestore (/users)
  │
  └── Audio Fetch ──► Flask Monolith (voxaide-backend/app.py @ port 5000)
                            │
                            ├── Startup CRASH (Missing `gtts`)
                            ├── Gemini 2.5 Flash (Direct Multimodal Audio)
                            ├── Firestore Admin (/orders, /contacts, /users)
                            └── gTTS / ElevenLabs (Local MP3 generation)
```

### Architectural Gaps

1. **No RAG Engine:** The primary architectural pillar—retrieving proprietary company knowledge to prevent hallucinations—does not exist.
2. **No Multi-Tenant Isolation:** All data in Firestore is flat. There is no concept of `company_id`, company boundaries, or scoped permissions.
3. **No Webhook Gateway for Telephony:** No integration for incoming PSTN/SIP phone calls.
4. **Tight Coupling in `app.py`:** A single 383-line file contains Flask initialization, Firebase admin credentials creation, Gemini tool definitions, prompt strings, and audio synthesis.

---

## 4. Security Audit & Findings

1. **Plaintext Passwords in Backend:**
   - In `voxaide-backend/app.py` line 187, `/api/signup` writes raw `password` to Firestore without hashing: `'password': password, # NOTE: You should hash this in production!`.
   - In line 215, `/api/login` compares raw string passwords.
   - *Mitigation:* Unify authentication around Firebase Auth ID tokens or bcrypt-hashed passwords. Verify Firebase ID tokens server-side.
2. **Credential Exposure:**
   - `voxaide-backend/.env` contains raw JSON service account credentials and Gemini API key.
   - *Mitigation:* Ensure `.env` is strictly git-ignored; provide a clean `.env.example` with placeholders.
3. **Overly Permissive Firestore Rules:**
   - `firestore.rules` lines 11–13:
     ```
     match /{document=**} {
       allow read, write: if request.auth != null;
     }
     ```
     Any authenticated user can read and modify all data across all collections.
   - *Mitigation:* Restrict Firestore rules to company-owned subcollections or route mutations through the authenticated backend API.
4. **Prompt Injection & Document Poisoning:**
   - Current prompts do not distinguish system instructions from untrusted user or document inputs.

---

## 5. Code Quality & Dead Code

- **Dead Code:**
  - `voxaide-backend/firestore.py`: Initializes an unconfigured `firestore.Client()` never imported anywhere.
  - `voxaide-backend/utils.py`: Contains `hash_password` and `check_password` functions that are imported in `app.py` but never invoked.
  - `arb_history.csv`: 26KB of crypto arbitrage records completely unrelated to VoxAide.
- **Mock Code:**
  - `src/pages/Dashboard.tsx`: Static mock tables, mock files, and mock graphs.
  - `CustomerChat.tsx`: Hardcoded order demo suggestions (`ZMT1003`).

---

## 6. Target Architecture & Recommended Solutions

### Recommended Vector Database: **ChromaDB (with Abstract VectorStore Interface)**
- **Why ChromaDB?**
  - Runs in-process in Python with zero cloud cost or external infra overhead.
  - Supports persistent on-disk storage (`data/chromadb`).
  - Supports metadata filtering out-of-the-box (`where={"company_id": company_id}`), guaranteeing company isolation.
  - Easy to spin up and demo live during technical interviews without relying on remote network connectivity.
  - Wrapped behind an abstract `VectorStore` interface (`add_documents`, `similarity_search`, `delete_document`, `delete_company_namespace`) so switching to Pinecone, Qdrant, or pgvector is a one-line configuration switch.

### Target Clean Modular Monolith Structure

```
voxaide-backend/
├── app/
│   ├── api/
│   │   ├── auth_routes.py
│   │   ├── company_routes.py
│   │   ├── knowledge_routes.py
│   │   ├── agent_routes.py
│   │   ├── appointment_routes.py
│   │   └── twilio_routes.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── logging.py
│   ├── models/
│   │   ├── company.py
│   │   ├── document.py
│   │   └── appointment.py
│   ├── services/
│   │   ├── rag_service.py
│   │   ├── embedding_service.py
│   │   ├── vector_store.py
│   │   ├── llm_service.py
│   │   ├── voice_service.py
│   │   └── appointment_service.py
│   ├── tools/
│   │   ├── base.py
│   │   └── appointment_tool.py
│   └── prompts/
│       ├── system_prompts.py
│       └── rag_prompts.py
├── tests/
├── data/
├── main.py
└── requirements.txt
```

---

## 7. Phased Implementation Roadmap

- **Phase 1: Stabilize Existing Project & Environment**
  - Fix missing dependencies (`gtts`, etc.) and ensure backend boots cleanly.
  - Clean up dead files (`firestore.py`, `arb_history.csv`).
  - Add backend test suite harness.
  - Centralize environment configuration with `.env.example`.
- **Phase 2: Company & Multi-Tenant Model**
  - Implement company abstraction (`company_id`, name, industry, agent config).
  - Secure tenant association and Firestore schema.
- **Phase 3: RAG Ingestion Pipeline & Isolated Vector Store**
  - Document parser (PDF, TXT, DOCX, CSV).
  - Semantic chunking engine with metadata (`company_id`, `doc_id`, etc.).
  - VectorStore abstraction with ChromaDB and company-scoped similarity search.
- **Phase 4: Test Agent Playground & Web Chat**
  - Interactive web agent testing interface with RAG source traceability, latency, and debug mode.
  - Hybrid chat interface supporting both Text and Voice.
- **Phase 5: Business Tool Execution Engine**
  - Tool calling interface (`AgentTool`).
  - End-to-end `AppointmentBookingTool` with validation and Firestore persistence.
- **Phase 6: Twilio Voice Call Gateway**
  - Twilio incoming call webhook (`/api/twilio/voice`) with TwiML `<Gather>`.
  - Speech processing webhook with RAG context, tool calling, and TwiML voice response.
  - Graceful fallback and human escalation callback request.
- **Phase 7: Real-Time Admin Dashboard**
  - Live knowledge base file management (upload, view status, delete, re-index).
  - Real call logs, conversation transcripts, and appointment manager.
  - Derived analytics (total queries, resolution rate, top intents).
- **Phase 8: Automated Testing & AI Evaluation**
  - Unit tests for chunking, isolation, and appointment schemas.
  - Security test: Company A data NEVER leaks to Company B.
  - AI evaluation suite for groundedness and factuality.
- **Phase 9: Documentation & Interview Readiness**
  - System architecture diagrams, API specs, Demo guide, and Resume facts.
