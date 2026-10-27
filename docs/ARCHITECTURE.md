# AURA architecture

The target architecture is local-first: the Unity Android client records
audio and displays a licensed VRM avatar, while the local Python development
backend coordinates conversation, llama.cpp inference, whisper.cpp
transcription, Piper speech, and SQLite memory.

Phase 2 adds a local llama.cpp HTTP adapter and `POST /api/v1/chat`. The
backend sends a system prompt built from `character/personality.json`, a
bounded client-supplied recent history, and the current user message to the
server's OpenAI-compatible `/v1/chat/completions` endpoint. The endpoint
returns only actual model output; unavailable or malformed server responses
become explicit service errors.

The llama.cpp server should bind to `127.0.0.1` and is configured separately
from the FastAPI process. Role messages are left in the standard format so the
server uses the selected GGUF's embedded chat template or its configured
`--chat-template`. The client does not select or hard-code Qwen.

SQLite bootstrap, request IDs, and `/health` from Phase 1 remain unchanged.
Conversation persistence is intentionally deferred to Phase 3.

Development mode will use a private Wi-Fi connection between Android and the
Windows machine. Standalone Android inference is a separate performance-
dependent milestone and is not assumed to work on every device.
