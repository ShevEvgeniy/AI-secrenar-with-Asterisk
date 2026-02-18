param(
  [string]$Paths = "scripts/check_env.cmd,scripts/run_ari.cmd"
)

$items = $Paths -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
$root = Split-Path -Parent $PSScriptRoot
$bad = @()

foreach ($item in $items) {
  $full = Join-Path $root $item
  if (-not (Test-Path -LiteralPath $full)) {
    continue
  }

  $bytes = [System.IO.File]::ReadAllBytes($full)
  if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
    $bad += $item
  }
}

if ($bad.Count -gt 0) {
  foreach ($item in $bad) {
    Write-Output "BOM detected: $item"
  }
  exit 1
}

exit 0
