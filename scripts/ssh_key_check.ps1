param(
  [Parameter(Mandatory=$true)][string]$User,
  [Parameter(Mandatory=$true)][string]$Host,
  [Parameter(Mandatory=$true)][string]$Key,
  [Parameter(Mandatory=$true)][int]$TimeoutMs,
  [Parameter(Mandatory=$true)][string]$Out
)

try {
  if (Test-Path -LiteralPath $Out) {
    Remove-Item -LiteralPath $Out -Force -ErrorAction SilentlyContinue
  }
} catch {}

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = 'ssh.exe'
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true

$args = @(
  '-n','-T','-F','NUL',
  '-i', $Key,
  '-o','BatchMode=yes',
  '-o','IdentitiesOnly=yes',
  '-o','PreferredAuthentications=publickey',
  '-o','PasswordAuthentication=no',
  '-o','KbdInteractiveAuthentication=no',
  '-o','ChallengeResponseAuthentication=no',
  '-o','NumberOfPasswordPrompts=0',
  '-o','StrictHostKeyChecking=accept-new',
  '-o',('UserKnownHostsFile=' + $env:TEMP + '\known_hosts_ai_secretary.txt'),
  '-o','GlobalKnownHostsFile=NUL',
  '-o','UpdateHostKeys=no',
  '-o','ConnectTimeout=5',
  '-o','ConnectionAttempts=1',
  '-o','ServerAliveInterval=5',
  '-o','ServerAliveCountMax=1',
  ($User + '@' + $Host),
  'exit 0'
)

foreach ($arg in $args) {
  [void]$psi.ArgumentList.Add($arg)
}

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $psi

try {
  [void]$process.Start()

  if (-not $process.WaitForExit($TimeoutMs)) {
    try { $process.Kill() } catch {}
    [System.IO.File]::WriteAllText($Out, 'SSH timeout', [System.Text.Encoding]::ASCII)
    exit 124
  }

  $stdout = $process.StandardOutput.ReadToEnd()
  $stderr = $process.StandardError.ReadToEnd()
  $combined = ($stdout + [Environment]::NewLine + $stderr).Trim()
  [System.IO.File]::WriteAllText($Out, $combined, [System.Text.Encoding]::ASCII)
  exit $process.ExitCode
}
catch {
  [System.IO.File]::WriteAllText($Out, $_.Exception.Message, [System.Text.Encoding]::ASCII)
  exit 1
}
