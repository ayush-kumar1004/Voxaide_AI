# VoxAide AI — Voice Architecture Migration Plan

**Document Version:** 1.0.0  
**Date:** September 2026  
**Status:** Approved Migration Roadmap  
**Target:** Safe, zero-downtime transition from legacy turn-based audio prototype to real-time streaming voice architecture.

---

## 1. Overview & Migration Philosophy

The legacy prototype currently relies on static MP3 generation, unary HTTP requests, gTTS fallback, and browser-only recording. 
To transition VoxAide to a production-grade voice customer support platform, we must replace this pipeline with **Twilio Media Streams + Real-time Streaming WebSockets**.

To prevent breaking the application during this transition, we follow a strict **Strangler Fig Migration Pattern**:
1. **Identify & Isolate:** Catalog all legacy dependencies and touchpoints.
2. **Build the Core First:** Implement the provider-agnostic `AgentOrchestrator`, `RAGService`, and `Tools` independently of any audio transport.
3. **Build the New Streaming Bridge:** Implement the real-time WebSocket bridge (`Twilio Media Streams ↔ Gemini Live / Streaming Audio`).
4. **Build Dual-Mode Testing:** Implement the interactive web playground (supporting both text and streaming audio) calling the same orchestrator.
5. **Verify & Validate:** Run automated end-to-end tests for RAG factuality, tenant isolation, and appointment booking.
6. **Decommission Obsolete Code:** Remove gTTS, legacy MP3 generators, and dead routes only after the replacement is verified.

---

## 2. Legacy Audio Inventory & Deprecation Checklist

The following items are marked for phased deprecation and removal:

| Component / Artifact | File Location | Reason for Decommissioning | Planned Replacement |
| :--- | :--- | :--- | :--- |
| `gTTS` library & dependency | `voxaide-backend/requirements.txt`, `app.py` line 13 | Robotic voice, blocking disk I/O, no streaming, non-production. | Real-time 24kHz PCM streaming via Gemini Live / WebSockets. |
| `synthesize_speech()` function | `voxaide-backend/app.py` lines 238–283 | Synchronous REST calls to ElevenLabs / gTTS saving local MP3s. | Direct audio frame streaming over WebSockets. |
| Static audio storage | `voxaide-backend/static/audio/*.mp3` | Disk clutter, high latency, privacy/GDPR liability. | Ephemeral streaming buffers in memory; zero disk writes. |
| Unary `/talk` route | `voxaide-backend/app.py` lines 286–373 | Expects full WAV file upload, slow, non-streaming, no barge-in. | Persistent WebSocket endpoint `/api/voice/stream` + Twilio stream. |
| Browser `MediaRecorder` WAV mock | `src/pages/CustomerChat.tsx` | Fragile MIME type handling; records entire monologue before sending. | Streaming Web Audio API / AudioWorklet or WebSockets + Text chat fallback. |
| `arb_history.csv` | Project root | Leftover crypto arbitrage file (already removed in Phase 1). | Cleaned. |
| `firestore.py` | `voxaide-backend/firestore.py` | Unauthenticated duplicate firestore client (already removed in Phase 1).| Cleaned. |

---

## 3. Detailed Step-by-Step Migration Phases

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  STEP 1: CORE   │     │   STEP 2: RAG    │     │  STEP 3: TOOLS   │
│  Orchestrator   ├────►│  Ingestion &     ├────►│  Appointment     │
│  & Company Model│     │  ChromaDB Tenant │     │  Booking Engine  │
└─────────────────┘     └──────────────────┘     └────────┬─────────┘
                                                          │
┌─────────────────┐     ┌──────────────────┐              │
│  STEP 6: CLEAN  │     │  STEP 5: TELECOM │     ┌────────▼─────────┐
│  Decommission   │◄────┤  Twilio Inbound  │◄────┤  STEP 4: STREAM  │
│  gTTS & Static  │     │  Media Streams   │     │  Real-Time Voice │
│  MP3 Pipeline   │     │  Phone Numbers   │     │  WebSocket Bridge│
└─────────────────┘     └──────────────────┘     └──────────────────┘
```

---

### Step 1: Central Agent Orchestrator & Multi-Tenant Isolation
- Implement `AgentOrchestrator` in `voxaide-backend/app/services/agent_orchestrator.py`.
- Ensure all business reasoning, prompt construction, memory, and tool decisions happen here.
- The orchestrator accepts clean input: `process_turn(company_id, session_id, user_text, stream_callback)`.
- *Validation:* Independent unit tests verify that `AgentOrchestrator` handles greetings, FAQs, and intent detection without touching audio.

### Step 2: Knowledge Ingestion & Isolated Vector Storage
- Build `DocumentService` (supporting PDF, TXT, DOCX, CSV) with semantic chunking.
- Implement abstract `VectorStore` with `ChromaVectorStore` implementation.
- Enforce mandatory tenant filtering on every search: `where={"company_id": company_id}`.
- *Validation:* Verify that Company A cannot retrieve Company B's documents under any query.

### Step 3: Business Tools & Appointment Booking Engine
- Create typed `AgentTool` abstraction with Pydantic schemas.
- Implement `AppointmentBookingTool` (`customer_name`, `phone`, `date`, `time`, `service`).
- Persist confirmed appointments to Firestore collection `appointments` under `{company_id}`.
- Implement `HumanEscalationTool` creating a callback ticket or initiating phone transfer.
- *Validation:* End-to-end tool execution tests with mock inputs and invalid parameters.

### Step 4: Real-Time Streaming Voice Bridge
- Implement an asynchronous WebSocket gateway (`voxaide-backend/app/services/voice_gateway.py`).
- Implement audio transcoding:
  - Inbound: 8kHz G.711 μ-law (Twilio) ➔ 16kHz Linear PCM (AI).
  - Outbound: 24kHz Linear PCM (AI) ➔ 8kHz G.711 μ-law (Twilio).
- Integrate native interruption handling: on detecting caller voice, emit `clear` message to Twilio stream to instantly flush playback.
- Implement web audio client for dashboard testing.

### Step 5: Twilio Phone Number Connection
- Implement `/api/twilio/voice` webhook returning TwiML:
  ```xml
  <Response>
    <Connect>
      <Stream url="wss://YOUR-SERVER-DOMAIN/api/twilio/media-stream" />
    </Connect>
  </Response>
  ```
- Map inbound phone number to `company_id` via Firestore metadata.
- Connect live phone calls to `AgentOrchestrator`.

### Step 6: Verification, Testing & Decommissioning
- Verify that both phone calls and the web playground produce identical, grounded RAG answers and execute appointment bookings.
- Run complete test suite:
  - Unit tests
  - RAG groundedness evaluation (`evaluation/questions.json`)
  - Security company isolation test
- **Decommission Legacy Assets:**
  - Delete `static/audio/` directory.
  - Remove `synthesize_speech()` and legacy `/talk` route from `app.py`.
  - Remove `gtts` from `requirements.txt`.
  - Clean up dead imports and unused environment variables.

---

## 4. Verification Checkpoints

Before removing any legacy code, each of the following checkpoints must pass:

1. **Text Playground Test:** Admin can type *"What is the cost of teeth cleaning?"* and receive a grounded answer with cited source document (`pricing.pdf`).
2. **Appointment Booking Test:** Admin can complete an appointment booking through conversation; record appears in Firestore with `status: "confirmed"`.
3. **Interruption Test:** During voice playback, incoming user audio triggers a buffer clear within 300ms without crashing the WebSocket session.
4. **Tenant Isolation Test:** Querying Company A's agent for Company B's exclusive product name returns *"I do not have information about that service."*
5. **Human Escalation Test:** Saying *"I want to speak with a manager"* invokes the callback/escalation workflow with structured logging.

---

## 5. Rollback & Contingency Plan

If the real-time WebSocket connection experiences unexpected upstream provider instability during testing:
- The `AgentOrchestrator` remains 100% operational via REST/Text mode.
- The system can fallback to a streaming cascading STT/TTS adapter without rewriting RAG or appointment booking.
- Telephony can temporarily use TwiML `<Say>` and `<Gather>` fallback handlers without data loss.
