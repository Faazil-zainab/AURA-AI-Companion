$ErrorActionPreference = "Continue"

Write-Host "AURA environment check"
Write-Host "Workspace: $((Get-Location).Path)"

$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    $pythonVersion = (& python --version 2>&1)
    Write-Host "[OK] Python: $pythonVersion"
    if ($pythonVersion -notmatch "Python 3\.(11|12|13|14)") {
        Write-Host "[WARN] Python 3.11+ is recommended for this project."
    } elseif ($pythonVersion -notmatch "Python 3\.11") {
        Write-Host "[INFO] Python 3.11 is the project baseline; this machine reports $pythonVersion."
    }
} else {
    Write-Host "[MISSING] Python"
}

function Check-Command($name, $label = $name) {
    $command = Get-Command $name -ErrorAction SilentlyContinue
    if ($command) {
        Write-Host "[OK] ${label}: $($command.Source)"
    } else {
        Write-Host "[MISSING] $label"
    }
}

Check-Command "git"
Check-Command "cmake"
Check-Command "dotnet"
Check-Command "java"
Check-Command "adb" "Android platform-tools (adb)"
Check-Command "sdkmanager" "Android command-line tools (sdkmanager)"
Check-Command "Unity" "Unity Editor"
Check-Command "llama-server" "llama.cpp server"
Check-Command "whisper-cli" "whisper.cpp CLI"
Check-Command "piper" "Piper TTS"

$sdkCandidates = @($env:ANDROID_HOME, $env:ANDROID_SDK_ROOT, "$env:LOCALAPPDATA\Android\Sdk") | Where-Object { $_ }
$sdkFound = $false
foreach ($sdk in $sdkCandidates) {
    if (Test-Path $sdk) {
        $sdkFound = $true
        Write-Host "[OK] Android SDK directory: $sdk"
        break
    }
}
if (-not $sdkFound) {
    Write-Host "[MISSING] Android SDK directory"
}

Write-Host ""
Write-Host "Missing optional tools do not block the current backend tests; they are required by later phases."
