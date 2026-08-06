<#
.SYNOPSIS
  Move <script src="js/main.js"> from end of body to <head> with `defer`
  attribute, and add <link rel="preload" as="style" href="styles.css"> in head.

  Why: main.js currently blocks HTML parse at end of body (chain peak 407ms).
  With defer, browser downloads main.js in parallel with HTML/CSS, executes
  after parsing finishes. Saves 200-300ms on critical path.

.EXAMPLE
  pwsh ./defer-main-js.ps1
#>

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

$files = Get-ChildItem -Path $root -Filter "*.html" -Recurse |
         Where-Object { $_.Name -ne "google-site-verification.html" }

$updated = 0
foreach ($f in $files) {
  $content = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
  $original = $content

  # Skip if already using defer
  if ($content -match 'src="js/main\.js"[^>]*defer') {
    continue
  }

  # 1) Remove the body-end <script src="...js/main.js"></script> tag
  $content = [regex]::Replace(
    $content,
    '[\t ]*<script src="(?:(?:\.\./)+|)js/main\.js"></script>\s*\n',
    '',
    1
  )

  # 2) Replace the existing <link rel="stylesheet" href="...styles.css"> with
  #    preload + async pattern (preload starts fetch early, onload swaps to
  #    actual stylesheet without blocking render)
  $content = [regex]::Replace(
    $content,
    '<link rel="stylesheet" href="((?:\.\./)*)styles\.css">',
    '<link rel="preload" href="$1styles.css" as="style">' + "`n" +
    '    <link rel="stylesheet" href="$1styles.css" media="print" onload="this.media=' + "'" + 'all' + "'" + '">' + "`n" +
    '    <noscript><link rel="stylesheet" href="$1styles.css"></noscript>',
    1
  )

  # 3) Add <script defer src="...js/main.js"> in head, right after the stylesheet
  $content = [regex]::Replace(
    $content,
    '(<noscript><link rel="stylesheet" href="((?:\.\./)*)styles\.css"></noscript>)',
    '$1' + "`n" + '    <script defer src="$2js/main.js"></script>',
    1
  )

  if ($content -ne $original) {
    [System.IO.File]::WriteAllText($f.FullName, $content, [System.Text.Encoding]::UTF8)
    Write-Host "[+] $($f.Name)" -ForegroundColor Green
    $updated++
  }
}

Write-Host ""
Write-Host "Done. files updated: $updated" -ForegroundColor Cyan
