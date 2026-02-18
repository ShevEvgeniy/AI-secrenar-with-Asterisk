param(
  [Parameter(Mandatory=$true)][string]$Path,
  [Parameter(Mandatory=$true)][string]$Out
)

# ?????? .env
$lines = Get-Content -LiteralPath $Path -ErrorAction Stop

$outLines = New-Object System.Collections.Generic.List[string]

foreach ($line in $lines) {
  $l = $line.Trim()
  if ([string]::IsNullOrWhiteSpace($l)) { continue }
  if ($l.StartsWith('#') -or $l.StartsWith(';')) { continue }

  $idx = $l.IndexOf('=')
  if ($idx -lt 1) { continue }

  $k = $l.Substring(0, $idx).Trim()
  $v = $l.Substring($idx + 1).Trim()

  # ????? ??????? ???????
  if (($v.StartsWith('"') -and $v.EndsWith('"')) -or ($v.StartsWith("'") -and $v.EndsWith("'"))) {
    if ($v.Length -ge 2) { $v = $v.Substring(1, $v.Length - 2) }
  }

  # ????????????? ??? cmd ??? EnableDelayedExpansion:
  # ^  -> ^^
  # !  -> ^!
  # %  -> %%
  # "  -> ^"
  $v = $v -replace '\^', '^^'
  $v = $v -replace '!', '^!'
  $v = $v -replace '%', '%%'
  $v = $v -replace '"', '^"'

  if (-not [string]::IsNullOrWhiteSpace($k)) {
    $outLines.Add('set "' + $k + '=' + $v + '"')
  }
}

# ????? ASCII ??? BOM
$enc = New-Object System.Text.ASCIIEncoding
[System.IO.File]::WriteAllLines($Out, $outLines, $enc)

exit 0
