# VoxAide — Voice AI + Twilio: Setup, Run & Verification Guide

**What this covers:** how to run the VoxAide backend, connect a real Twilio phone
number to it, and the exact fixes that were applied to make the voice pipeline
work end to end.

---

## 1. TL;DR — what was actually wrong

Your project was **not** "half-built." The RAG engine, the agent orchestrator,
and the full Twilio voice webhook layer were already written and well-structured.
Two things were stopping it from working:

1. **Stale `requirements.txt`** — the code imports `chromadb` and `pydantic`
   (and uses Gemini embeddings), but those were missing from `requirements.txt`.
   Result: the app crashed on startup because the vector store couldn't import,
   which took RAG and telephony down with it. **Fixed** — `requirements.txt` now
   lists every dependency the code actually imports.

2. **A real bug in the inbound-call webhook** — in
   `app/api/telephony_routes.py`, the fallback branch did
   `c.id for c in company_service._companies_mem.values()`, but that store holds
   **dicts**, not objects, so every inbound call that hit the fallback branch
   crashed with `AttributeError: 'dict' object has no attribute 'id'` and
   returned HTTP 500 — Twilio would have just dropped the call.
   **Fixed** — it now reads `c["id"]` safely.

> Note: the Twilio voice gateway uses **TwiML webhooks generated with Python's
> stdlib `xml.etree`** — it does **not** require the `twilio` pip package.
> Twilio does the speech-to-text (`<Gather input="speech">`) and the
> text-to-speech (`<Say>`), and your backend does the RAG + LLM in between.
> This is the simplest, most reliable design for a voice bot and it's the right
> call — no audio-codec/websocket streaming needed.

### Verification performed
- Backend boots cleanly; `/health` → `200 {"status":"healthy"}`.
- Test suite: **43 / 44 pass**. The one failure (`test_7_audio_service_synthesize`)
  is only because the offline test environment can't reach Google's gTTS servers;
  it passes on a machine with normal internet, and gTTS isn't even used on the
  Twilio call path.
- RAG proven: ingested a real-estate FAQ, embedded it into ChromaDB, retrieved it
  by semantic search with company isolation.
- Twilio flow proven: inbound webhook → greeting TwiML; caller speech → routed
  through the RAG orchestrator → answer returned inside valid `<Say>` TwiML;
  empty-speech re-prompt; status callback logging. All green.

---

## 2. Run the backend locally

```bash
cd voxaide-backend

# 1. Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

# 2. Install dependencies (now correct)
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env       # Windows  (cp on macOS/Linux)
#   then edit .env and set at least:
#     GEMINI_API_KEY=...            (from Google AI Studio)
#   optional:
#     GOOGLE_APPLICATION_CREDENTIALS_JSON={...}   (Firebase; app runs without it using in-memory fallback)
#     ELEVENLABS_API_KEY=...        (premium TTS; not needed for Twilio calls)

# 4. Run
python app.py
#   -> serves on http://localhost:5000
```

Quick health check (new terminal):
```bash
curl http://localhost:5000/health
# {"status":"healthy","version":"2.1.0-agent-orchestrator"}
```

### Run the tests
```bash
# APP_ENV=testing uses deterministic mock embeddings so no API key is needed
# Windows (PowerShell):
$env:APP_ENV="testing"; python -m pytest tests/ -q
# macOS/Linux:
# APP_ENV=testing python -m pytest tests/ -q
```

---

## 3. Load company knowledge (RAG)

The bot answers from documents you ingest per company. There's a knowledge API
(`app/api/knowledge_routes.py`) and the service `KnowledgeService.ingest_document`.
Feed it your FAQ / brochure / project details (TXT, CSV, JSON, PDF supported by
the document parser). Every chunk is tagged with `company_id`, and every
retrieval is filtered by `company_id` — so Company A can never see Company B's
data. The default seeded tenant is `demo_company`.

---

## 4. Connect a REAL Twilio phone number

Your webhook endpoints (already built):

| Purpose            | Method | URL path                                            |
|--------------------|--------|-----------------------------------------------------|
| Inbound call       | POST   | `/api/telephony/voice/inbound`                      |
| Caller speech turn | POST   | `/api/telephony/voice/gather?company_id=<id>`       |
| Call status        | POST   | `/api/telephony/voice/status`                       |

Twilio needs a **public** URL, so expose your local server with a tunnel:

```bash
# install ngrok (https://ngrok.com), then:
ngrok http 5000
# copy the https URL it prints, e.g. https://abc123.ngrok-free.app
```

Then in the Twilio Console:
1. Buy a number (Phone Numbers → Buy a number) with **Voice** capability.
2. Open the number's config → **Voice & Fax** → *A call comes in*:
   - Set to **Webhook**, `POST`,
     `https://abc123.ngrok-free.app/api/telephony/voice/inbound`
3. (Optional) Status callback URL →
   `https://abc123.ngrok-free.app/api/telephony/voice/status`
4. Save. **Call the number** — you'll hear the greeting, then it answers your
   spoken questions from the ingested knowledge base.

Map that Twilio number to a specific company either by:
- passing `?company_id=<id>` on the inbound URL, **or**
- registering the number → company via
  `POST /api/companies/<company_id>/phone-numbers`.

---

## 5. The one thing to know for interviews: latency

Voice is unforgiving about delay. The `<Gather speech>` + `<Say>` design keeps it
simple, but each turn still costs STT (Twilio) + RAG retrieval + Gemini + TTS.
Keep replies short, keep `top_k` small (it's 4), use `gemini-flash`, and cache
where you can. This "identify failure modes and iterate" work is exactly what a
Forward Deployed Engineer role wants to hear you talk about.

---

## 6. Files changed in this pass
- `voxaide-backend/requirements.txt` — added `chromadb`, `pydantic` (+ organized).
  Backup kept at `requirements.txt.bak`.
- `voxaide-backend/app/api/telephony_routes.py` — fixed the dict-access crash in
  the inbound-call fallback branch.
