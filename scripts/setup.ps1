$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root ".venv"
$requirements = Join-Path $root "backend\requirements.txt"

$pythonCommand = Get-Command py -ErrorAction SilentlyContinue
if ($pythonCommand) {
    & py -3.11 --version *> $null
    if ($LASTEXITCODE -eq 0) {
        $python = "py"
        $pythonArgs = @("-3.11")
    } else {
        Write-Warning "Python 3.11 was not found; using the active python command."
        $python = "python"
        $pythonArgs = @()
    }
} else {
    $python = "python"
    $pythonArgs = @()
}

Write-Host "Creating virtual environment at $venv"
& $python @pythonArgs -m venv $venv
if ($LASTEXITCODE -ne 0) { throw "Virtual environment creation failed." }

$venvPython = Join-Path $venv "Scripts\python.exe"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r $requirements

Write-Host "Setup complete. Activate with: .\.venv\Scripts\Activate.ps1"
