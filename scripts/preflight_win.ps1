param(
  [switch]$RunTests
)

$ErrorActionPreference = "Stop"
$failed = $false

function Step([string]$msg) {
  Write-Host ""
  Write-Host "==> $msg"
}

function MarkFail([string]$msg) {
  Write-Host "[FAIL] $msg"
  $script:failed = $true
}

function MarkOk([string]$msg) {
  Write-Host "[OK] $msg"
}

function Load-DotEnv([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) {
    Write-Host "[INFO] .env not found: $Path"
    return
  }
  foreach ($line in Get-Content -LiteralPath $Path) {
    $trimmed = $line.Trim()
    if (-not $trimmed -or $trimmed.StartsWith("#")) {
      continue
    }
    $m = [regex]::Match($trimmed, "^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
    if (-not $m.Success) {
      continue
    }
    $name = $m.Groups[1].Value
    $value = $m.Groups[2].Value.Trim()
    if ($value.Length -ge 2) {
      if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
        $value = $value.Substring(1, $value.Length - 2)
      }
    }
    [Environment]::SetEnvironmentVariable($name, $value, "Process")
  }
}

$scriptDir = $PSScriptRoot
$projectRoot = Resolve-Path (Join-Path $scriptDir "..")
Set-Location $projectRoot
Step "Project root: $projectRoot"
[Environment]::SetEnvironmentVariable("PYTHONPATH", "src", "Process")

Step "Activate virtualenv (if needed)"
if (-not $env:VIRTUAL_ENV) {
  $activatePath = Join-Path $projectRoot ".venv\\Scripts\\Activate.ps1"
  if (Test-Path -LiteralPath $activatePath) {
    . $activatePath
    MarkOk "Activated $activatePath"
  } else {
    MarkFail ".venv activation script not found: $activatePath"
  }
} else {
  MarkOk "Already active: $env:VIRTUAL_ENV"
}

try {
  $pythonCmd = Get-Command python -ErrorAction Stop
  Write-Host "Python: $($pythonCmd.Source)"
} catch {
  MarkFail "python not found in PATH"
}

Step "Load .env into current process"
Load-DotEnv (Join-Path $projectRoot ".env")
MarkOk ".env loaded"

Step "Run scripts/check_env.cmd"
cmd /c ".\\scripts\\check_env.cmd"
$checkEnvRc = $LASTEXITCODE
Write-Host "check_env.cmd exit=$checkEnvRc"
if ($checkEnvRc -ne 0) {
  MarkFail "check_env.cmd failed"
} else {
  MarkOk "check_env.cmd"
}

Step "Run explicit SSH key-only check"
$sshOut = Join-Path $projectRoot "ssh_key_check_out.txt"
if (-not $env:ASTERISK_SSH_USER -or -not $env:ASTERISK_SSH_HOST -or -not $env:ASTERISK_SSH_KEY) {
  MarkFail "ASTERISK_SSH_USER / ASTERISK_SSH_HOST / ASTERISK_SSH_KEY are required for ssh_key_check"
} else {
  powershell -NoProfile -ExecutionPolicy Bypass -File ".\\scripts\\ssh_key_check.ps1" `
    -User "$env:ASTERISK_SSH_USER" `
    -Host "$env:ASTERISK_SSH_HOST" `
    -Key "$env:ASTERISK_SSH_KEY" `
    -TimeoutMs 6000 `
    -Out "$sshOut"
  $sshRc = $LASTEXITCODE
  Write-Host "ssh_key_check.ps1 exit=$sshRc out=$sshOut"
  if ($sshRc -ne 0) {
    MarkFail "ssh_key_check.ps1 failed"
  } else {
    MarkOk "ssh_key_check.ps1"
  }
}

Step "Run Silero smoke"
python -c "from ai_secretary.tts.silero import SileroTTS; b=SileroTTS().synthesize('test'); print(b[:4], len(b)); import sys; sys.exit(0 if b[:4]==b'RIFF' and b[8:12]==b'WAVE' else 1)"
$sileroRc = $LASTEXITCODE
Write-Host "silero smoke exit=$sileroRc"
if ($sileroRc -ne 0) {
  MarkFail "Silero smoke failed"
} else {
  MarkOk "Silero smoke"
}

if ($RunTests) {
  Step "Run pytest -q"
  python -m pytest -q
  $testsRc = $LASTEXITCODE
  Write-Host "pytest exit=$testsRc"
  if ($testsRc -ne 0) {
    MarkFail "pytest failed"
  } else {
    MarkOk "pytest"
  }
}

if ($failed) {
  Write-Host ""
  Write-Host "PREFLIGHT FAILED"
  exit 1
}

Write-Host ""
Write-Host "PREFLIGHT OK"
exit 0
