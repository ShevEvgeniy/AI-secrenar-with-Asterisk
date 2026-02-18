# Check environment for ARI call flow
# Usage: .\scripts\check_env.ps1

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

Set-Location $projectRoot

$allOk = $true

function Fail($msg) {
  Write-Host "[FAIL] $msg"
  $script:allOk = $false
}

function Ok($msg) {
  Write-Host "[OK] $msg"
}

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

# Check ssh/scp
if (Get-Command ssh.exe -ErrorAction SilentlyContinue) {
  Ok "SSH found"
} else {
  Fail "SSH not found. Install OpenSSH Client (Windows Features) or add ssh.exe to PATH"
}

if (Get-Command scp.exe -ErrorAction SilentlyContinue) {
  Ok "SCP found"
} else {
  Fail "SCP not found. Install OpenSSH Client (Windows Features) or add scp.exe to PATH"
}

# Check venv python
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
  Ok "Venv python found"
} else {
  Fail "Venv python not found: $venvPython. Create it with: python -m venv .venv"
}

$env:PYTHONPATH = "src"

# Required env vars
$requiredVars = @(
  "ARI_URL",
  "ARI_USER",
  "ARI_PASSWORD",
  "ASTERISK_SSH_HOST",
  "ASTERISK_SSH_USER",
  "ASTERISK_SSH_KEY"
)

foreach ($var in $requiredVars) {
  if ([string]::IsNullOrWhiteSpace($env:$var)) {
    Fail "Missing env var: $var"
  }
}

if ($allOk) {
  $ariInfoUrl = "$($env:ARI_URL)/asterisk/info"
  $ariCode = & curl.exe -s -o NUL -w "%{http_code}" -u "$($env:ARI_USER):$($env:ARI_PASSWORD)" $ariInfoUrl
  if ($ariCode -eq "200") {
    Ok "ARI /asterisk/info -> 200"
  } else {
    Fail "ARI /asterisk/info -> $ariCode ($ariInfoUrl)"
  }

  $sshTarget = "$($env:ASTERISK_SSH_USER)@$($env:ASTERISK_SSH_HOST)"
  $sshOut = & ssh.exe -i "$($env:ASTERISK_SSH_KEY)" -o BatchMode=yes -o IdentitiesOnly=yes -o ConnectTimeout=10 $sshTarget "echo SSH_KEY_OK" 2>&1
  if ($sshOut -match "SSH_KEY_OK") {
    Ok "SSH key-only -> SSH_KEY_OK"
  } else {
    Fail "SSH key-only failed. Ensure server uses AuthenticationMethods publickey (not publickey,password) for user tulauser"
  }
}

if ($allOk) {
  Write-Host "ALL CHECKS PASSED"
  exit 0
} else {
  Write-Host "CHECKS FAILED"
  exit 1
}
