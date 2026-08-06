<#
.SYNOPSIS
  Update all HTML files to load the minified .min.css and .min.js
  variants instead of the full sources.

.EXAMPLE
  pwsh ./use-minified-assets.ps1
#>

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

$files = Get-ChildItem -Path $root -Filter "*.html" -Recurse |
         Where-Object { $_.Name -ne "google-site-verification.html" }

$updated = 0
foreach ($f in $files) {
  $content = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
  $original = $content

  # Replace styles.css with styles.min.css (in preload + stylesheet + noscript)
  $content = [regex]::Replace($content, 'href="((?:\.\./)*)styles\.css"', 'href="$1styles.min.css"')
  # Same for src="js/main.js" -> src="js/main.min.js"
  $content = [regex]::Replace($content, 'src="((?:\.\./)*)js/main\.js"', 'src="$1js/main.min.js"')

  if ($content -ne $original) {
    [System.IO.File]::WriteAllText($f.FullName, $content, [System.Text.Encoding]::UTF8)
    Write-Host "[+] $($f.Name)" -ForegroundColor Green
    $updated++
  }
}

Write-Host ""
Write-Host "Done. files updated: $updated" -ForegroundColor Cyan
