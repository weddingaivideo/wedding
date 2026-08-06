<#
.SYNOPSIS
  Inject <link rel="manifest"> and <link rel="apple-touch-icon"> into every HTML page.

.EXAMPLE
  pwsh ./inject-pwa-tags.ps1
#>

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

# Compute manifest path: pages at root use "/manifest.json", nested pages use "/../manifest.json" etc.
function Get-ManifestPath([string]$htmlRel) {
  $depth = ($htmlRel -split '\\').Count - 1
  $prefix = ""
  for ($i = 0; $i -lt $depth; $i++) { $prefix += "../" }
  return $prefix + "manifest.json"
}

$files = Get-ChildItem -Path $root -Filter "*.html" -Recurse |
         Where-Object { $_.Name -ne "google-site-verification.html" }

$updated = 0
foreach ($f in $files) {
  $content = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
  $original = $content
  $rel = $f.FullName.Substring($root.Length + 1)

  $manifestPath = Get-ManifestPath $rel
  $iconPath = $manifestPath -replace 'manifest\.json$', 'apple-touch-icon.png'

  $themeMeta = '<meta name="theme-color" content="#c45a72">'
  $manifestLink = "<link rel=`"manifest`" href=`"$manifestPath`">"
  $appleLink = "<link rel=`"apple-touch-icon`" href=`"$iconPath`">"
  $mobileCapable = '<meta name="apple-mobile-web-app-capable" content="yes">'
  $mobileTitle = '<meta name="apple-mobile-web-app-title" content="WeddingAI.video">'

  # Inject after the existing <link rel="icon"> line
  $pattern = '(<link rel="icon"[^>]+>)'
  $replacement = "`$1`n    $themeMeta`n    $manifestLink`n    $appleLink`n    $mobileCapable`n    $mobileTitle"
  $content = [regex]::Replace($content, $pattern, $replacement, 1)

  if ($content -ne $original) {
    [System.IO.File]::WriteAllText($f.FullName, $content, [System.Text.Encoding]::UTF8)
    Write-Host "[+] $rel" -ForegroundColor Green
    $updated++
  }
}

Write-Host ""
Write-Host "Done. files updated: $updated" -ForegroundColor Cyan
