# Claude Code Prompt — VoxAide Voice + Twilio

Copy everything in the code block below into Claude Code (run it from inside the
`voxaide-main` folder). It is written to match your **actual** codebase, not a
generic template. It assumes the two fixes already applied (requirements.txt +
the inbound-webhook dict bug); if you're starting from a fresh clone, it will
re-apply them safely.

---

```
You are working in the VoxAide repo. The backend is a Flask "modular monolith"
at ./voxaide-backend. It is a multi-tenant AI voice customer-support platform:
RAG over ChromaDB (Gemini text-embedding-004), a channel-agnostic
AgentOrchestrator (Gemini 2.5 Flash + tool calling), and a Twilio voice gateway
that uses TwiML <Gather input="speech"> for STT and <Say> for TTS (no twilio pip
package, no audio streaming). Do NOT rearchitect any of this — it works.

Context on structure:
- Entry: voxaide-backend/app.py -> app/__init__.py (create_app, registers blueprints)
- RAG: app/services/knowledge_service.py, app/providers/chroma_vector_store.py,
  app/providers/embedding_provider.py
- Orchestrator: app/services/agent_orchestrator.py
- Telephony: app/api/telephony_routes.py, app/services/telephony_service.py
- Company/tenancy: app/services/company_service.py (in-memory store holds DICTS,
  not objects — index with c["id"], never c.id)
- Tests: voxaide-backend/tests/  (run with APP_ENV=testing for mock embeddings)

Do the following, verifying each step by running code before moving on:

1. DEPENDENCIES. Ensure voxaide-backend/requirements.txt lists every third-party
   package the code imports. It MUST include: Flask, flask-cors, gunicorn,
   python-dotenv, requests, pydantic, bcrypt, firebase-admin,
   google-cloud-firestore, google-generativeai, chromadb, gtts. Create a venv,
   pip install -r requirements.txt, and confirm it resolves.

2. BOOT. Run: APP_ENV=testing python -c "from app import app;
   print(app.test_client().get('/health').get_json())" from voxaide-backend.
   It must print status healthy. Fix any import/startup error until it does.

3. TELEPHONY BUG GUARD. In app/api/telephony_routes.py, the inbound-call
   fallback that lists companies must read the dict key "id", not attribute .id
   (company_service._companies_mem stores model_dump() dicts). Confirm an
   inbound POST with an UNREGISTERED "To" number returns 200 + valid TwiML
   (this exercises the fallback branch), not HTTP 500.

4. VERIFY RAG. Write a scratch script that ingests a small real-estate FAQ via
   knowledge_service.ingest_document(company_id="demo_company", ...), then calls
   knowledge_service.search(...) and prints the retrieved chunk. Confirm
   retrieval works and is company-scoped.

5. VERIFY FULL VOICE FLOW with app.test_client(): 
   POST /api/telephony/voice/inbound (form: To, From, CallSid) -> assert 200 and
   <Response>...<Gather input="speech"> greeting TwiML.
   POST /api/telephony/voice/gather?company_id=demo_company
   (form: CallSid, From, SpeechResult="what flat sizes are available") -> assert
   200 and a <Say> reply inside <Gather>. If GEMINI_API_KEY is unset the reply
   will be the graceful escalation message — that's expected; with a key it
   returns the RAG answer.
   POST /api/telephony/voice/status (form: CallSid, CallDuration, CallStatus)
   -> assert 200.

6. RUN THE TEST SUITE: APP_ENV=testing python -m pytest tests/ -q. Everything
   should pass except possibly test_7_audio_service_synthesize, which only fails
   when the environment can't reach Google's gTTS servers (network), not a code
   bug. If other tests fail, fix the code.

7. Do NOT commit secrets. Ensure voxaide-backend/.env and the keys/ folder stay
   gitignored. Leave .env.example with placeholders only.

Report: a short summary of what you changed, the test results, and the exact
steps to point a real Twilio number at the webhooks via ngrok.
```

---

### Optional follow-up prompts (paste after the above succeeds)

**Lower call latency:**
```
In the Twilio gather path, reduce per-turn latency: keep RAG top_k small, ensure
the Gemini model is a flash variant, trim the system prompt, and add a short
timeout + fast fallback so a slow LLM call never leaves the caller in silence.
Measure and print latency_ms per turn from AgentResponse.
```

**Real-estate lead capture tool:**
```
Add a new agent tool (following app/tools/base.py and appointment_tools.py) that
captures a real-estate lead: name, phone, budget, preferred location, BHK size.
Register it in the tool registry, persist to Firestore under the company, and
have the orchestrator call it when a caller expresses buying intent. Add a test.
```
