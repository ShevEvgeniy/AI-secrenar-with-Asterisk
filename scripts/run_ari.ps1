# Run ARI listener from PowerShell
# Usage: .\scripts\run_ari.ps1

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

$pyproject = Join-Path $projectRoot "pyproject.toml"
$requirements = Join-Path $projectRoot "requirements.txt"
if (-not (Test-Path $pyproject) -and -not (Test-Path $requirements)) {
  Write-Host "[run_ari] Project root not found. Expected pyproject.toml or requirements.txt in $projectRoot"
  exit 1
}

Set-Location $projectRoot

# Load .env if present
$envPath = Join-Path $projectRoot ".env"
if (Test-Path $envPath) {
  try {
    $lines = Get-Content -Path $envPath -Encoding UTF8
    foreach ($line in $lines) {
      $trimmed = $line.Trim()
      if ([string]::IsNullOrWhiteSpace($trimmed)) { continue }
      if ($trimmed.StartsWith("#") -or $trimmed.StartsWith(";")) { continue }

      $parts = $trimmed.Split("=", 2)
      if ($parts.Count -ne 2) { continue }
      $key = $parts[0].Trim()
      $value = $parts[1].Trim()
      if ([string]::IsNullOrWhiteSpace($key)) { continue }

      if (($value.StartsWith("\"") -and $value.EndsWith("\"")) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
        $value = $value.Substring(1, $value.Length - 2)
      }
      $value = $value.Trim()

      if ([string]::IsNullOrWhiteSpace($env:$key)) {
        $env:$key = $value
      }
    }
    Write-Host ".env loaded"
  } catch {
    Write-Host "[FAIL] .env read error: $($_.Exception.Message)"
    exit 1
  }
} else {
  Write-Host ".env not found (ok)"
}

$activate = Join-Path $projectRoot ".venv\Scripts\Activate.ps1"
if (-not (Test-Path $activate)) {
  Write-Host "[run_ari] Virtualenv not found: $activate"
  Write-Host "[run_ari] Create it with: python -m venv .venv"
  exit 1
}

Write-Host "[run_ari] Activating venv..."
. $activate

$env:PYTHONPATH = "src"

function Ensure-EnvDefault($name, $value) {
  if ([string]::IsNullOrWhiteSpace($env:$name)) {
    $env:$name = $value
  }
}

Ensure-EnvDefault "ARI_URL" "http://92.118.85.117:8088/ari"
Ensure-EnvDefault "ARI_USER" "ai_secretary2"
Ensure-EnvDefault "ARI_PASSWORD" "AiSec2_2026"
Ensure-EnvDefault "ARI_APP_NAME" "ai_secretary"
Ensure-EnvDefault "ASTERISK_SSH_HOST" "92.118.85.117"
Ensure-EnvDefault "ASTERISK_SSH_USER" "tulauser"
Ensure-EnvDefault "ASTERISK_SSH_KEY" "$env:USERPROFILE\.ssh\selectel_gpu"
Ensure-EnvDefault "ASTERISK_SOUNDS_DIR" "/var/lib/asterisk/sounds"
Ensure-EnvDefault "ASTERISK_SOUNDS_SUBDIR" "ai_secretary"

if (-not (Test-Path $env:ASTERISK_SSH_KEY)) {
  Write-Host "[run_ari] SSH key not found: $env:ASTERISK_SSH_KEY"
  exit 1
}

Write-Host "[run_ari] Config summary:"
Write-Host "  ARI_URL=$env:ARI_URL"
Write-Host "  ARI_USER=$env:ARI_USER"
Write-Host "  ARI_APP_NAME=$env:ARI_APP_NAME"
Write-Host "  SSH_HOST=$env:ASTERISK_SSH_HOST"
Write-Host "  SSH_USER=$env:ASTERISK_SSH_USER"
Write-Host "  SSH_KEY=$env:ASTERISK_SSH_KEY"
Write-Host "  SOUNDS_DIR=$env:ASTERISK_SOUNDS_DIR"
Write-Host "  SOUNDS_SUBDIR=$env:ASTERISK_SOUNDS_SUBDIR"

Write-Host "[run_ari] Starting ARI listener..."
python -m ai_secretary.telephony.ari_app
