<#
.SYNOPSIS
  Normalize the <head> section's stylesheet + main.js loading pattern across
  every HTML page. Final pattern:

    <link rel="preload" href="...styles.css" as="style">
    <link rel="stylesheet" href="...styles.css" media="print" onload="this.media='all'">
    <noscript><link rel="stylesheet" href="...styles.css"></noscript>
    <script defer src="...js/main.js"></script>

.EXAMPLE
  pwsh ./normalize-head-styles.ps1
#>

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

$files = Get-ChildItem -Path $root -Filter "*.html" -Recurse |
         Where-Object { $_.Name -ne "google-site-verification.html" }

$updated = 0
foreach ($f in $files) {
  $content = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
  $original = $content

  # Determine the relative path prefix (root pages use ""; services use "../../" etc.)
  $relPath = $f.FullName.Substring($root.Length).TrimStart('\', '/').Replace("\", "/")
  # relPath is now like "index.html" or "services/personalization/pet-wedding.html"
  # For relative path prefix, count directory levels: 0 for root, 2 for services/personalization/
  $dirs = if ($relPath -match '/') { $relPath.Substring(0, $relPath.LastIndexOf('/')) } else { "" }
  $depth = if ($dirs -eq "") { 0 } else { ($dirs -split "/").Count }
  $prefix = ""
  for ($i = 0; $i -lt $depth; $i++) { $prefix += "../" }

  $expectedBlock = @"
    <link rel="preload" href="${prefix}styles.css" as="style">
    <link rel="stylesheet" href="${prefix}styles.css" media="print" onload="this.media='all'">
    <noscript><link rel="stylesheet" href="${prefix}styles.css"></noscript>
    <script defer src="${prefix}js/main.js"></script>
"@

  # Match: any sequence of the 4 lines (in any state of duplication/corruption)
  # from the first <link rel="preload" ... styles.css> to the last <script defer ... main.js">
  $pat = '(?s)(    <link rel="preload" href="(?:(?:\.\./)*)styles\.css" as="style">.*?<script defer src="(?:(?:\.\./)*)js/main\.js"></script>)'
  $content = [regex]::Replace($content, $pat, $expectedBlock, 1)

  if ($content -ne $original) {
    [System.IO.File]::WriteAllText($f.FullName, $content, [System.Text.Encoding]::UTF8)
    Write-Host "[+] $($f.Name)" -ForegroundColor Green
    $updated++
  }
}

Write-Host ""
Write-Host "Done. files normalized: $updated" -ForegroundColor Cyan
