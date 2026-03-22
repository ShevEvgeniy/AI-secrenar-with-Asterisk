param(
  [Parameter(Mandatory = $true)]
  [string] $User,

  [Parameter(Mandatory = $true)]
  [Alias('Host')]
  [string] $HostName,

  [Parameter(Mandatory = $true)]
  [string] $Key,

  [int] $TimeoutMs = 8000,
  [string] $Out = ""
)

try {
  if ($Out -and (Test-Path -LiteralPath $Out)) {
    Remove-Item -LiteralPath $Out -Force -ErrorAction SilentlyContinue
  }
} catch {}

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "ssh.exe"
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true

$args = @(
  "-n", "-T", "-F", "NUL",
  "-i", $Key,
  "-o", "BatchMode=yes",
  "-o", "IdentitiesOnly=yes",
  "-o", "PreferredAuthentications=publickey",
  "-o", "PasswordAuthentication=no",
  "-o", "KbdInteractiveAuthentication=no",
  "-o", "ChallengeResponseAuthentication=no",
  "-o", "NumberOfPasswordPrompts=0",
  "-o", "StrictHostKeyChecking=accept-new",
  "-o", ("UserKnownHostsFile=" + $env:TEMP + "\known_hosts_ai_secretary.txt"),
  "-o", "GlobalKnownHostsFile=NUL",
  "-o", "UpdateHostKeys=no",
  "-o", "ConnectTimeout=5",
  "-o", "ConnectionAttempts=1",
  "-o", "ServerAliveInterval=5",
  "-o", "ServerAliveCountMax=1",
  ($User + "@" + $HostName),
  "echo OK"
)

if ($psi.ArgumentList -ne $null) {
  foreach ($arg in $args) {
    [void]$psi.ArgumentList.Add($arg)
  }
} else {
  $escaped = foreach ($arg in $args) {
    if ($arg -match '[\s"]') {
      '"' + ($arg -replace '"', '\"') + '"'
    } else {
      $arg
    }
  }
  $psi.Arguments = ($escaped -join " ")
}

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $psi

try {
  [void]$process.Start()

  if (-not $process.WaitForExit($TimeoutMs)) {
    try { $process.Kill() } catch {}
    if ($Out) {
      [System.IO.File]::WriteAllText($Out, "SSH timeout", [System.Text.Encoding]::ASCII)
    }
    exit 124
  }

  $stdout = $process.StandardOutput.ReadToEnd()
  $stderr = $process.StandardError.ReadToEnd()
  $combined = ($stdout + [Environment]::NewLine + $stderr).Trim()
  if ($Out) {
    [System.IO.File]::WriteAllText($Out, $combined, [System.Text.Encoding]::ASCII)
  }

  if ($process.ExitCode -eq 0 -and $stdout -match '(^|\s)OK(\s|$)') {
    exit 0
  }
  if ($process.ExitCode -ne 0) {
    exit $process.ExitCode
  }
  exit 2
}
catch {
  if ($Out) {
    [System.IO.File]::WriteAllText($Out, $_.Exception.Message, [System.Text.Encoding]::ASCII)
  }
  exit 1
}
