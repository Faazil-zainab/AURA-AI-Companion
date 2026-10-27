$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { "python" }

Push-Location (Join-Path $root "backend")
try {
    & $python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
} finally {
    Pop-Location
}
