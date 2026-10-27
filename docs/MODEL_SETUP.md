# Model setup

Phase 2 accepts a user-provided GGUF model through a separately running
llama.cpp server. This repository does not download, include, or select a
model automatically.

## Selected model verification

Nytheria 3B is the selected roleplay fine-tune. Its upstream card is at
<https://huggingface.co/owlninjam/nytheria-3b> and the GGUF listing is at
<https://huggingface.co/mradermacher/nytheria-3b-GGUF>. The exact file
`nytheria-3b.Q4_K_M.gguf` exists and is 1,929,903,168 bytes (about 1.93 GB
decimal / 1.80 GiB). The quantized repository reports MIT and identifies
`owlninjam/nytheria-3b` as its base. The upstream Nytheria card identifies
`Qwen/Qwen2.5-3B-Instruct` as that model's base and links Qwen's separate
`qwen-research` terms, so both the MIT derivative terms and Qwen base terms
must be reviewed. The upstream Nytheria repository reports MIT in its model
card, but no standalone `LICENSE` file was available at the checked URL; the
model-card license text and base-model terms therefore still need to be
retained with any distribution. This is the selected Nytheria fine-tune, not a
silent substitution of the general-purpose Qwen model.

The Qwen base license is the Qwen Research License Agreement:
<https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/raw/main/LICENSE>. It grants
use, reproduction, distribution, and derivative rights for **non-commercial
purposes only**, with notice and attribution conditions. Local personal,
non-commercial evaluation appears within that grant, subject to complying
with the agreement and applicable law. Commercial use or redistribution of a
product requires separate legal review/licensing; this audit is not a legal
opinion.

The selected model is not present in this workspace, so real inference has
not been tested here. Do not download a different model or quantization.

After approval, download only the selected file to the configured project
directory and verify its size before use:

```powershell
$ModelUrl = "https://huggingface.co/mradermacher/nytheria-3b-GGUF/resolve/main/nytheria-3b.Q4_K_M.gguf"
$ModelPath = Join-Path (Resolve-Path ".\models\llm").Path "nytheria-3b.Q4_K_M.gguf"
Invoke-WebRequest -Uri $ModelUrl -OutFile $ModelPath
(Get-Item $ModelPath).Length
```

Expected size is exactly `1929903168` bytes. Do not run this command before
approval; it downloads approximately 1.93 GB.

For this CPU-oriented machine, prefer a compatible Q4_K_M file when the
selected model publishes one. A 2B/3B model can still require substantial RAM
for weights, context, and the server process; measure loading time, first-token
latency, tokens/second, and peak RAM after the exact file is selected.

## Local server

`llama-server` is not installed in this workspace. A compatible official
Windows x64 CPU build identified for approval is release `b10507`:

- Package: `llama-b10507-bin-win-cpu-x64.zip`
- Download size: 18,493,914 bytes (about 18.5 MB decimal)
- Source: <https://github.com/ggml-org/llama.cpp/releases/tag/b10507>
- SHA-256: `778a3588dd634ac43bd88b96b24da35ab83d68562fb921499b0ecdf831d6552d`
- Runtime license: llama.cpp MIT, from its official `LICENSE` file

The current `v0.7.0` release page is newer, but its GitHub API response in
this audit exposed only `nightly-tag.txt`, so no exact current Windows binary
size was available to approve. The b10507 package is an official CPU x64
release candidate and does not require administrator privileges when extracted
to a user-writable folder. It has not been downloaded or tested here.

After approval, extract the package to a user-writable directory such as
`tools\llama-b10507\`; do not modify system PATH unless explicitly desired.
Then run the server bound to loopback:

```powershell
tools\llama-b10507\llama-server.exe `
  -m models/llm/nytheria-3b.Q4_K_M.gguf `
  --host 127.0.0.1 --port 8080 --ctx-size 2048
```

The server's GGUF metadata normally supplies the chat template. If the chosen
model requires an override, configure llama.cpp's `--chat-template` option
according to that model's upstream documentation. AURA sends standard role
messages to `/v1/chat/completions` and does not hard-code a Qwen template.

For the exact Nytheria GGUF above, metadata contains the Qwen-style template
with a `system` role and an assistant generation prompt. Use the default
`AURA_LLM_SYSTEM_PROMPT_MODE=system`; `merge_user` is not required for this
selected model. `omit` is available only when the selected model explicitly
needs no system prompt.

Configure the backend with `backend/.env.example`. Important settings are
`AURA_LLM_SERVER_URL`, `AURA_LLM_CHAT_ENDPOINT`, `AURA_LLM_MODEL_NAME`,
`AURA_LLM_SYSTEM_PROMPT_MODE`, `AURA_LLM_CONTEXT_SIZE`,
`AURA_LLM_MAX_TOKENS`, and `AURA_LLM_TIMEOUT_SECONDS`.

The opt-in integration test requires both a running server and a compatible
GGUF model:

```powershell
$env:AURA_RUN_LLM_INTEGRATION = "1"
python -m pytest backend/tests/test_llm_integration.py -q
```

No cloud API is used. whisper.cpp and Piper remain later-phase components.

## Windows PowerShell smoke test

The following procedure does not download anything. After approval and
successful extraction/download of the two approved files, run the server in
PowerShell window 1:

```powershell
$ModelPath = (Resolve-Path ".\models\llm\nytheria-3b.Q4_K_M.gguf").Path
& ".\tools\llama-b10507\llama-server.exe" `
  -m $ModelPath `
  --host 127.0.0.1 `
  --port 8080 `
  --ctx-size 2048
```

`--host 127.0.0.1` keeps the model server loopback-only. `--ctx-size 2048`
matches the current AURA default and is a conservative starting point for a
16 GB CPU machine; the Gemma GGUF metadata reports an 8192-token model
context, but that does not require using the full context.

In PowerShell window 2, verify the server and configure AURA. The model ID is
read from the running server rather than guessed:

```powershell
$env:AURA_LLM_SERVER_URL = "http://127.0.0.1:8080"
$env:AURA_LLM_CHAT_ENDPOINT = "/v1/chat/completions"
$env:AURA_LLM_SYSTEM_PROMPT_MODE = "merge_user"
$env:AURA_LLM_CONTEXT_SIZE = "2048"
$env:AURA_LLM_MAX_TOKENS = "128"
$env:AURA_LLM_TIMEOUT_SECONDS = "120"
$ModelId = (Invoke-RestMethod "http://127.0.0.1:8080/v1/models").data[0].id
$env:AURA_LLM_MODEL_NAME = $ModelId
$ModelId
```

Test direct llama.cpp inference before starting AURA:

```powershell
$directBody = @{
  model = $ModelId
  messages = @(@{ role = "user"; content = "Reply with exactly: local model ready" })
  temperature = 0.2
  max_tokens = 32
  stream = $false
} | ConvertTo-Json -Depth 10

$direct = Invoke-RestMethod `
  -Uri "http://127.0.0.1:8080/v1/chat/completions" `
  -Method Post `
  -ContentType "application/json" `
  -Body $directBody

$direct.choices[0].message.content
```

Start AURA in the same window so the environment variables are inherited:

```powershell
.\scripts\start_backend.ps1
```

In a third window, test the AURA endpoint and request ID:

```powershell
$auraBody = @{
  session_id = "audit-session"
  message = "Reply with exactly: AURA model ready"
  voice_enabled = $false
} | ConvertTo-Json -Depth 10

$aura = Invoke-WebRequest `
  -Uri "http://127.0.0.1:8000/api/v1/chat" `
  -Method Post `
  -Headers @{ "X-Request-ID" = "real-model-audit" } `
  -ContentType "application/json" `
  -Body $auraBody

$aura.StatusCode
$aura.Headers["X-Request-ID"]
$aura.Content | ConvertFrom-Json
```

Finally, with the same AURA environment variables available, run the opt-in
test:

```powershell
# Stop the backend in window 2 with Ctrl+C first, then run this there.
$env:AURA_RUN_LLM_INTEGRATION = "1"
python -m pytest backend/tests/test_llm_integration.py -q
```

Do not set `AURA_RUN_LLM_INTEGRATION=1` until direct inference has returned a
real response from the approved model.
