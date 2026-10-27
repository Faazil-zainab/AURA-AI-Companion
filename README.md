# AURA

AURA is a local-first Android AI companion project. Phase 2 adds a local
llama.cpp HTTP adapter and chat API on top of the Phase 1 backend. Model files,
voice models, and avatar assets are intentionally not included in this
repository.

## Phase 1 quick start

```powershell
.\scripts\check_environment.ps1
.\scripts\setup.ps1
.\scripts\start_backend.ps1
```

Then open `http://127.0.0.1:8000/health`. The endpoint must return HTTP 200
with `"status": "ok"`.

## Phase 2 local model

Install or build `llama.cpp` separately, place the approved Nytheria GGUF in
`models/llm/`, and start the server on loopback:

```powershell
llama-server -m models/llm/nytheria-3b.Q4_K_M.gguf --host 127.0.0.1 --port 8080 --ctx-size 2048
```

Copy `backend/.env.example` to `.env` if configuration changes are needed,
then start the backend. The chat endpoint is `POST /api/v1/chat`. The backend
uses the server's OpenAI-compatible `/v1/chat/completions` endpoint and reports
model-server failures instead of generating fallback text.

Run the opt-in real-server test only after a compatible server and model are
running:

```powershell
$env:AURA_RUN_LLM_INTEGRATION = "1"
python -m pytest backend/tests/test_llm_integration.py -q
```

Run the backend tests from the project root:

```powershell
python -m pytest backend/tests -q
```

The project targets Python 3.11. The current workspace may use another
compatible Python version when 3.11 is unavailable; the environment check
reports that distinction.

## Scope boundary

Phase 2 is implemented without bundling or downloading a model. Later phases
will add SQLite conversation memory, offline speech, and the Unity/VRM Android
client. No cloud AI API is configured.

See `docs/IMPLEMENTATION_STATUS.md` for evidence and known limitations.
# AURA-AI-Companion
