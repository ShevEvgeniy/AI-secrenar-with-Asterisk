param(
  [string]$CallId,
  [int]$TimeoutSec = 8,
  [string]$OutDir = ".\tmp\diag",
  [Alias("Verbose")][switch]$VerboseLog
)

$ErrorActionPreference = "Stop"
$allOk = $true
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = $utf8NoBom
[Console]::OutputEncoding = $utf8NoBom

function Write-Info([string]$Message) {
  Write-Host "[INFO] $Message"
}

function Write-Ok([string]$Message) {
  Write-Host "[OK] $Message"
}

function Write-Fail([string]$Message) {
  Write-Host "[FAIL] $Message"
  $script:allOk = $false
}

function Write-DebugLog([string]$Message) {
  if ($VerboseLog) {
    Write-Host "[VERBOSE] $Message"
  }
}

function Get-MaskedValue([string]$Name, [string]$Value) {
  if ([string]::IsNullOrWhiteSpace($Value)) {
    return "<empty>"
  }

  if ($Name -match "PASSWORD|TOKEN|SECRET|KEY") {
    if ($Value.Length -le 4) { return "****" }
    return ("{0}****{1}" -f $Value.Substring(0, 2), $Value.Substring($Value.Length - 2))
  }
  return $Value
}

function Load-DotEnv([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) {
    Write-Info ".env not found: $Path"
    return
  }

  foreach ($line in Get-Content -LiteralPath $Path -Encoding UTF8) {
    $trimmed = $line.Trim()
    if ([string]::IsNullOrWhiteSpace($trimmed)) { continue }
    if ($trimmed.StartsWith("#")) { continue }

    $parts = $trimmed.Split("=", 2)
    if ($parts.Count -ne 2) { continue }

    $name = $parts[0].Trim()
    $value = $parts[1].Trim()
    if ([string]::IsNullOrWhiteSpace($name)) { continue }

    if ($value.Length -ge 2) {
      if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
        $value = $value.Substring(1, $value.Length - 2)
      }
    }

    [Environment]::SetEnvironmentVariable($name, $value, "Process")
  }

  Write-Ok ".env loaded into process"
}

function Require-Command([string]$CommandName) {
  $cmd = Get-Command $CommandName -ErrorAction SilentlyContinue
  if (-not $cmd) {
    Write-Fail "$CommandName not found in PATH"
    return $false
  }
  return $true
}

function Run-External([string]$Exe, [string[]]$ArgList) {
  Write-DebugLog ("Run: " + $Exe + " " + ($ArgList -join " "))
  $output = & $Exe @ArgList 2>&1
  $exitCode = $LASTEXITCODE
  return [PSCustomObject]@{
    ExitCode = $exitCode
    Output = @($output)
    Text = (@($output) -join [Environment]::NewLine)
  }
}

function Test-NetPort(
  [Alias("Host")][string]$HostName,
  [int]$Port
) {
  $target = "{0}:{1}" -f $HostName, $Port
  try {
    $tnc = Test-NetConnection -ComputerName $HostName -Port $Port -WarningAction SilentlyContinue
    if ($tnc.TcpTestSucceeded) {
      Write-Ok "TCP $target reachable"
      return $true
    }
    Write-Fail "TCP $target unreachable"
    return $false
  } catch {
    Write-Fail "TCP $target check error: $($_.Exception.Message)"
    return $false
  }
}

function Ensure-Dir([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Path $Path -Force | Out-Null
  }
}

function Resolve-RepoRoot {
  $fallback = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
  $gitCmd = Get-Command git -ErrorAction SilentlyContinue
  if (-not $gitCmd) {
    return $fallback
  }

  try {
    $rootRaw = & git rev-parse --show-toplevel 2>$null
    $rootCandidate = "$rootRaw".Trim()
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($rootCandidate) -and (Test-Path -LiteralPath $rootCandidate)) {
      return $rootCandidate
    }
  } catch {
  }
  return $fallback
}

function Normalize-KeyPath([string]$PathValue) {
  if ([string]::IsNullOrWhiteSpace($PathValue)) {
    return $PathValue
  }

  $normalized = $PathValue.Trim()
  if ($normalized.Length -ge 2) {
    if (($normalized.StartsWith('"') -and $normalized.EndsWith('"')) -or ($normalized.StartsWith("'") -and $normalized.EndsWith("'"))) {
      $normalized = $normalized.Substring(1, $normalized.Length - 2)
    }
  }
  while ($normalized.Contains("\\")) {
    $normalized = $normalized.Replace("\\", "\")
  }
  return $normalized
}

$repoRoot = Resolve-RepoRoot
Set-Location $repoRoot
Write-Info "Repo root: $repoRoot"

if (-not $env:VIRTUAL_ENV) {
  $activatePath = Join-Path $repoRoot ".venv\Scripts\Activate.ps1"
  if (Test-Path -LiteralPath $activatePath) {
    . $activatePath
    Write-Ok "Activated venv"
  } else {
    Write-Info "Venv activation script not found: $activatePath"
  }
} else {
  Write-Info "Using active venv: $env:VIRTUAL_ENV"
}

Load-DotEnv (Join-Path $repoRoot ".env")

$envSummaryKeys = @(
  "ARI_URL",
  "ARI_USER",
  "ARI_APP_NAME",
  "ASTERISK_SSH_HOST",
  "ASTERISK_SSH_USER",
  "ASTERISK_SSH_KEY",
  "ASTERISK_SOUNDS_DIR",
  "ASTERISK_SOUNDS_SUBDIR",
  "ASTERISK_DOCKER_CONTAINER"
)

Write-Host ""
Write-Host "ENV SUMMARY"
foreach ($k in $envSummaryKeys) {
  $v = [Environment]::GetEnvironmentVariable($k, "Process")
  Write-Host ("  {0}={1}" -f $k, (Get-MaskedValue -Name $k -Value $v))
}

$resolvedOutDir = if ([IO.Path]::IsPathRooted($OutDir)) { $OutDir } else { Join-Path $repoRoot $OutDir }
Ensure-Dir $resolvedOutDir
Write-Info "Output directory: $resolvedOutDir"

$sshHost = [Environment]::GetEnvironmentVariable("ASTERISK_SSH_HOST", "Process")
$sshUser = [Environment]::GetEnvironmentVariable("ASTERISK_SSH_USER", "Process")
$sshKey = Normalize-KeyPath ([Environment]::GetEnvironmentVariable("ASTERISK_SSH_KEY", "Process"))
[Environment]::SetEnvironmentVariable("ASTERISK_SSH_KEY", $sshKey, "Process")
$ariUrl = [Environment]::GetEnvironmentVariable("ARI_URL", "Process")
$ariUser = [Environment]::GetEnvironmentVariable("ARI_USER", "Process")
$ariPassword = [Environment]::GetEnvironmentVariable("ARI_PASSWORD", "Process")
$soundsDir = [Environment]::GetEnvironmentVariable("ASTERISK_SOUNDS_DIR", "Process")
$soundsSubdir = [Environment]::GetEnvironmentVariable("ASTERISK_SOUNDS_SUBDIR", "Process")
$dockerContainer = [Environment]::GetEnvironmentVariable("ASTERISK_DOCKER_CONTAINER", "Process")

if ([string]::IsNullOrWhiteSpace($soundsDir)) { $soundsDir = "/var/lib/asterisk/sounds" }
if ([string]::IsNullOrWhiteSpace($soundsSubdir)) { $soundsSubdir = "ai_secretary" }

$baseRemoteSounds = "{0}/{1}" -f $soundsDir.TrimEnd("/"), $soundsSubdir.Trim("/")
$sshOptions = @(
  "-i", $sshKey,
  "-o", "BatchMode=yes",
  "-o", "IdentitiesOnly=yes",
  "-o", "StrictHostKeyChecking=accept-new",
  "-o", "ConnectTimeout=$TimeoutSec",
  "-o", "ServerAliveInterval=3",
  "-o", "ServerAliveCountMax=1"
)

$hasSshBasics = $true
foreach ($req in @("ASTERISK_SSH_HOST", "ASTERISK_SSH_USER", "ASTERISK_SSH_KEY")) {
  if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($req, "Process"))) {
    Write-Fail "$req is required"
    $hasSshBasics = $false
  }
}
if ($hasSshBasics) {
  try {
    if (-not (Test-Path -LiteralPath $sshKey)) {
      Write-Fail "SSH key not found: $sshKey"
      $hasSshBasics = $false
    }
  } catch {
    Write-Fail "SSH key check failed: $sshKey ($($_.Exception.Message))"
    $hasSshBasics = $false
  }
}

Write-Host ""
Write-Host "CONNECTIVITY"
if (-not [string]::IsNullOrWhiteSpace($sshHost)) {
  Test-NetPort -HostName $sshHost -Port 22 | Out-Null
  Test-NetPort -HostName $sshHost -Port 8088 | Out-Null
} else {
  Write-Fail "ASTERISK_SSH_HOST is empty, cannot run port checks"
}

$ariHttpCode = ""
if ((Require-Command "curl.exe") -and -not [string]::IsNullOrWhiteSpace($ariUrl) -and -not [string]::IsNullOrWhiteSpace($ariUser)) {
  $curlArgs = @(
    "-sS",
    "-u", ("{0}:{1}" -f $ariUser, $ariPassword),
    "-o", "NUL",
    "-w", "%{http_code}",
    ("{0}/asterisk/info" -f $ariUrl.TrimEnd("/"))
  )
  $curlRes = Run-External -Exe "curl.exe" -ArgList $curlArgs
  $ariHttpCode = $curlRes.Text.Trim()
  Write-Host "ARI /asterisk/info HTTP=$ariHttpCode"
  if ($curlRes.ExitCode -eq 0 -and $ariHttpCode -eq "200") {
    Write-Ok "ARI HTTP probe"
  } else {
    Write-Fail "ARI HTTP probe failed (code=$ariHttpCode, exit=$($curlRes.ExitCode))"
  }
} else {
  Write-Fail "Cannot run ARI HTTP probe (curl/ARI_URL/ARI_USER missing)"
}

$sshMkdirOk = $false
$scpOk = $false
$dockerProbeOk = $false
$dockerConfigured = -not [string]::IsNullOrWhiteSpace($dockerContainer)

if ((Require-Command "ssh.exe") -and $hasSshBasics) {
  Write-Host ""
  Write-Host "SSH MKDIR PROBE"
  $mkdirCmd = "mkdir -p $baseRemoteSounds/_probe && echo OK"
  $sshArgsMkdir = @($sshOptions + @("$sshUser@$sshHost", $mkdirCmd))
  $mkdirRes = Run-External -Exe "ssh.exe" -ArgList $sshArgsMkdir
  $mkdirLogPath = Join-Path $resolvedOutDir "ssh_mkdir_probe.txt"
  $mkdirRes.Output | Set-Content -Path $mkdirLogPath -Encoding UTF8
  if ($mkdirRes.ExitCode -eq 0 -and $mkdirRes.Text -match "(?m)^OK\s*$") {
    $sshMkdirOk = $true
    Write-Ok "SSH mkdir probe"
  } else {
    Write-Fail "SSH mkdir probe failed (see $mkdirLogPath)"
  }

  Write-Host ""
  Write-Host "SCP PROBE"
  if (Require-Command "scp.exe") {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $localProbe = Join-Path $resolvedOutDir "probe.txt"
    $remoteProbe = "/tmp/diag_probe_${stamp}.txt"
    "diag-probe $stamp" | Set-Content -Path $localProbe -Encoding UTF8

    $scpArgs = @($sshOptions + @($localProbe, ("{0}@{1}:{2}" -f $sshUser, $sshHost, $remoteProbe)))
    $scpRes = Run-External -Exe "scp.exe" -ArgList $scpArgs
    $scpLogPath = Join-Path $resolvedOutDir "scp_probe_upload.txt"
    $scpRes.Output | Set-Content -Path $scpLogPath -Encoding UTF8

    $verifyCmd = "test -f $remoteProbe && head -c 80 $remoteProbe && echo OK"
    $sshArgsVerify = @($sshOptions + @("$sshUser@$sshHost", $verifyCmd))
    $verifyRes = Run-External -Exe "ssh.exe" -ArgList $sshArgsVerify
    $verifyLogPath = Join-Path $resolvedOutDir "scp_probe_verify.txt"
    $verifyRes.Output | Set-Content -Path $verifyLogPath -Encoding UTF8

    if ($scpRes.ExitCode -eq 0 -and $verifyRes.ExitCode -eq 0 -and $verifyRes.Text -match "(?m)^OK\s*$") {
      $scpOk = $true
      Write-Ok "SCP upload+verify probe"
    } else {
      Write-Fail "SCP probe failed (see $scpLogPath, $verifyLogPath)"
    }
  } else {
    Write-Fail "scp.exe not found in PATH"
  }

  Write-Host ""
  Write-Host "DOCKER PROBE"
  $dockerNamesCmd = "docker ps --format '{{.Names}}' | head -n 5"
  $dockerNamesArgs = @($sshOptions + @("$sshUser@$sshHost", $dockerNamesCmd))
  $dockerNamesRes = Run-External -Exe "ssh.exe" -ArgList $dockerNamesArgs
  $dockerNamesLog = Join-Path $resolvedOutDir "docker_ps.txt"
  $dockerNamesRes.Output | Set-Content -Path $dockerNamesLog -Encoding UTF8
  $dockerNames = @($dockerNamesRes.Output | ForEach-Object { "$_".Trim() } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
  $hasAsterisk = @($dockerNames | Where-Object { $_ -match "asterisk" })
  if ($dockerNamesRes.ExitCode -eq 0 -and ($hasAsterisk.Count -gt 0 -or $dockerNames.Count -gt 0)) {
    $dockerProbeOk = $true
    Write-Ok "Docker listing via SSH"
  } else {
    Write-Fail "Docker listing failed/empty (see $dockerNamesLog)"
  }

  if ($dockerConfigured) {
    $dockerExecCmd = "docker exec $dockerContainer sh -lc 'id; ls -la /etc/asterisk | head -n 5'"
    $dockerExecArgs = @($sshOptions + @("$sshUser@$sshHost", $dockerExecCmd))
    $dockerExecRes = Run-External -Exe "ssh.exe" -ArgList $dockerExecArgs
    $dockerExecLog = Join-Path $resolvedOutDir "docker_exec_probe.txt"
    $dockerExecRes.Output | Set-Content -Path $dockerExecLog -Encoding UTF8
    if ($dockerExecRes.ExitCode -eq 0) {
      Write-Ok "Docker exec probe ($dockerContainer)"
    } else {
      $dockerProbeOk = $false
      Write-Fail "Docker exec probe failed (see $dockerExecLog)"
    }
  } else {
    Write-Info "ASTERISK_DOCKER_CONTAINER is not set; docker exec probe skipped"
  }
}

if (-not [string]::IsNullOrWhiteSpace($CallId)) {
  Write-Host ""
  Write-Host "CALLID CHECKS ($CallId)"

  $eventsPath = Join-Path $repoRoot "data\storage\artifacts\$CallId\events.jsonl"
  $eventsTailPath = Join-Path $resolvedOutDir "events_tail.txt"
  if (Test-Path -LiteralPath $eventsPath) {
    Get-Content -Path $eventsPath -Tail 80 | Set-Content -Path $eventsTailPath -Encoding UTF8
    Write-Ok "Saved local events tail: $eventsTailPath"
  } else {
    Write-Info "Local events file not found: $eventsPath"
  }

  if ((Require-Command "ssh.exe") -and $hasSshBasics) {
    $remoteCallDir = "$baseRemoteSounds/$CallId"
    $remoteCallCmd = "test -d $remoteCallDir && echo OK"
    $remoteCallArgs = @($sshOptions + @("$sshUser@$sshHost", $remoteCallCmd))
    $remoteCallRes = Run-External -Exe "ssh.exe" -ArgList $remoteCallArgs
    $remoteCallLog = Join-Path $resolvedOutDir "remote_callid_host.txt"
    $remoteCallRes.Output | Set-Content -Path $remoteCallLog -Encoding UTF8
    if ($remoteCallRes.ExitCode -eq 0 -and $remoteCallRes.Text -match "(?m)^OK\s*$") {
      Write-Ok "Remote host call dir exists: $remoteCallDir"
    } else {
      Write-Fail "Remote host call dir missing: $remoteCallDir (see $remoteCallLog)"
    }

    if ($dockerConfigured) {
      $dockerCallCmd = "docker exec $dockerContainer sh -lc 'test -d $remoteCallDir && ls -la $remoteCallDir | head -n 20 && echo OK'"
      $dockerCallArgs = @($sshOptions + @("$sshUser@$sshHost", $dockerCallCmd))
      $dockerCallRes = Run-External -Exe "ssh.exe" -ArgList $dockerCallArgs
      $dockerCallLog = Join-Path $resolvedOutDir "remote_callid_docker.txt"
      $dockerCallRes.Output | Set-Content -Path $dockerCallLog -Encoding UTF8
      if ($dockerCallRes.ExitCode -eq 0 -and $dockerCallRes.Text -match "(?m)^OK\s*$") {
        Write-Ok "Remote docker call dir exists: $remoteCallDir"
      } else {
        Write-Fail "Remote docker call dir missing: $remoteCallDir (see $dockerCallLog)"
      }
    }
  }
}

Write-Host ""
Write-Host "SUMMARY"
$coreOk = ($ariHttpCode -eq "200") -and $sshMkdirOk -and $scpOk
if ($dockerConfigured) {
  $coreOk = $coreOk -and $dockerProbeOk
}

if ($coreOk -and $allOk) {
  Write-Host "ALL_OK"
  Write-Host "Artifacts: $resolvedOutDir"
  exit 0
}

Write-Host "DIAG FAILED"
Write-Host "Artifacts: $resolvedOutDir"
exit 1
