# Implementation status

## Phase 1 — complete for the available environment

Implemented:

- Required top-level directory layout and model/asset placeholders.
- Environment-backed backend configuration and `.env.example`.
- FastAPI application with structured startup/shutdown logging.
- SQLite bootstrap with a checked-in schema file.
- `GET /health` returning HTTP 200 and a request ID.
- Generic error logging and safe 500 response handling.
- PowerShell environment, setup, and backend start scripts.
- Automated health and database initialization tests.

Validation evidence from the Phase 1 run:

- `python -m compileall -q backend/app backend/tests`: passed.
- `python -m pytest backend/tests -q`: passed, 2 tests.
- `scripts/check_environment.ps1`: completed successfully.
- Character JSON validation: `animation_config.json`, `expressions.json`, and
  `personality.json` parsed successfully.
- Live Uvicorn check on `127.0.0.1:8765`: `GET /health` returned HTTP 200,
  `status: ok`, and a generated request ID.

Rerun the backend tests with `python -m pytest backend/tests -q` after checkout.

## Phase 2 — implemented without a local model

Implemented:

- Configurable llama.cpp OpenAI-compatible HTTP adapter in
  `backend/app/services/llm_service.py`.
- Configurable system-prompt placement (`system`, `merge_user`, or `omit`) so
  model-specific chat-template requirements are explicit.
- Character prompt construction from `character/personality.json`.
- Bounded client-supplied history for the current request; no persistence is
  added before Phase 3.
- `POST /api/v1/chat` with Pydantic validation and explicit 503/502 failures.
- Safe handling for connection failures, timeouts, HTTP failures, malformed
  responses, and empty model output.
- Mock tests for successful inference, prompt construction, invalid input,
  timeout, unavailable server, malformed response, request IDs, and health
  regression.
- Opt-in real-server integration test guarded by
  `AURA_RUN_LLM_INTEGRATION=1`.

Phase 2 validation from this run: `python -m compileall -q backend/app
backend/tests` passed; `python -m pytest backend/tests -q` passed with 8 tests
and 1 expected opt-in integration skip. A live Uvicorn smoke check returned
HTTP 200 from `/health`; with the model URL pointed at an unused local port,
`POST /api/v1/chat` returned HTTP 503 with the request ID preserved. A check
against the occupied default port 8080 returned HTTP 502 because that port
answered HTTP 404 rather than exposing the llama.cpp endpoint.

## Phase 2 real-model readiness audit — 2026-10-27

Audit result: **blocked; real inference remains unvalidated**.

Local findings:

- Python 3.14.5 is running the backend successfully. The AURA HTTP stack
  imports and the existing tests pass under this interpreter.
- No `llama-server`, `llama`, or `llama-cli` executable is installed or on
  PATH. No llama.cpp build has therefore been selected or tested on Windows.
- `models/llm` contains only `.gitkeep`; no GGUF is installed.
- `pip check` reports unrelated pre-existing Django conflicts involving
  `crispy-bootstrap4`/`crispy-django-forms`; it does not report an AURA
  dependency conflict. The environment has pytest 9.1.1 while
  `backend/requirements.txt` declares `pytest>=8,<9`; tests pass, but this
  declaration/runtime mismatch should be resolved during environment setup.

Upstream metadata audit without downloading weights:

- Selected repository exists at the documented Hugging Face URL. Exact file:
  `nytheria-3b.Q4_K_M.gguf`, 1,929,903,168 bytes. Its GGUF metadata reports
  the `qwen2` architecture, 32,768-token context metadata, and a Qwen-style
  system/assistant chat template. The quantized repository reports MIT and
  bases on `owlninjam/nytheria-3b`; that upstream model states it is fine-tuned
  from `Qwen/Qwen2.5-3B-Instruct`.
- The Qwen base uses the Qwen Research License Agreement, which limits the
  grant to non-commercial purposes and requires notices/attribution. The
  upstream Nytheria card says MIT, but no standalone LICENSE file was found at
  the checked upstream path. Personal non-commercial evaluation appears
  permitted subject to the terms; commercial distribution requires separate
  legal review.

Runtime candidate identified without downloading:

- Official `ggml-org/llama.cpp` release `b10507`.
- `llama-b10507-bin-win-cpu-x64.zip`, 18,493,914 bytes.
- SHA-256: `778a3588dd634ac43bd88b96b24da35ab83d68562fb921499b0ecdf831d6552d`.
- Official llama.cpp MIT license.
- Proposed extraction path: `tools\llama-b10507\`.

Approval boundary:

- Model download: 1,929,903,168 bytes to `models\llm\`.
- Runtime download: 18,493,914 bytes to a user-writable `tools\` directory.
- Minimum payload is about 1.95 GB decimal combined; reserve additional free
  space for download staging, extraction, and runtime logs.
- No administrator privileges or PATH changes are required by the proposed
  procedure. Neither download was performed because explicit approval is
  required.

The exact Windows PowerShell server, direct-inference, AURA endpoint, and
opt-in test procedure is recorded in `docs/MODEL_SETUP.md`. No model or large
dependency was downloaded during this audit.

## Missing dependencies

- Unity Editor and Unity Android Build Support: not detected.
- Android `adb` and `sdkmanager` were not on PATH; an Android SDK directory
  exists and needs command-line tools/path configuration.
- llama.cpp, whisper.cpp, Piper, and FFmpeg executables: not detected.
- No GGUF model file is present in `models/llm/`; no download or real inference
  was performed.
- Python 3.11 is not installed; Python 3.14.5 is available in this workspace.

## Not implemented yet

Real model inference has not been tested because no llama.cpp server or GGUF
file is installed. The mock HTTP integration is validated, but it is not
evidence of model compatibility or generated output. Model license/base-model
review and exact-file approval remain open. STT, TTS, conversation
persistence, WebSocket streaming, memory CRUD, age-gate UI, Unity
scenes/scripts, VRM loading, animation, lip synchronization, Android builds,
and standalone on-device inference remain deferred.

## Next recommended phase

Phase 3: add SQLite-backed session messages and explicit memory CRUD around the
existing chat flow, while preserving the current no-fallback behavior.
