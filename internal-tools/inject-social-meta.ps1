<#
.SYNOPSIS
  Inject missing Open Graph + Twitter Card meta tags into every HTML file.

.DESCRIPTION
  Walks the workspace, opens each *.html page, and ensures the <head> has:
    - og:site_name
    - og:locale
    - og:type           (only adds if absent; doesn't overwrite)
    - twitter:image
    - twitter:title
    - twitter:description
  Pulls values from existing title/description/og:url/og:image tags.
  Idempotent: re-running won't duplicate.

.EXAMPLE
  pwsh ./inject-social-meta.ps1
#>

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$baseUrl = "https://weddingai.video"

$files = Get-ChildItem -Path $root -Filter "*.html" -Recurse |
         Where-Object { $_.Name -ne "google-site-verification.html" }

$updated = 0; $skipped = 0
foreach ($f in $files) {
  $content = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
  $original = $content

  # ---- Extract values from existing tags ----
  function Get-Meta([string]$html, [string]$attr, [string]$val) {
    $pat = '<meta\s+(?:name|property)="' + [regex]::Escape($attr) + '"\s+content="([^"]*)"'
    $m = [regex]::Match($html, $pat)
    if ($m.Success) { return $m.Groups[1].Value } else { return "" }
  }
  $title       = [regex]::Match($content, '<title>\s*([^<]+?)\s*</title>').Groups[1].Value
  $description = Get-Meta $content "description" ""
  $ogImage     = Get-Meta $content "og:image" ""
  $ogType      = Get-Meta $content "og:type" ""
  $twCard      = Get-Meta $content "twitter:card" ""

  # If a file has no twitter:card at all, skip (it might not be a content page)
  if ([string]::IsNullOrEmpty($twCard)) {
    Write-Host "[skip] no twitter:card in $($f.Name)" -ForegroundColor DarkGray
    $skipped++
    continue
  }

  # ---- Build the meta lines we want to ensure exist ----
  $inserts = @()
  $inserts += '    <meta property="og:site_name" content="WeddingAI.video">'
  $inserts += '    <meta property="og:locale" content="en_US">'
  if ([string]::IsNullOrEmpty($ogType)) {
    $inserts += '    <meta property="og:type" content="website">'
  }
  if (-not ($content -match 'name="twitter:title"')) {
    $t = $title -replace '&#x27;',"'" -replace '&amp;','&'
    $inserts += "    <meta name=`"twitter:title`" content=`"$t`">"
  }
  if (-not ($content -match 'name="twitter:description"') -and -not [string]::IsNullOrEmpty($description)) {
    $d = $description -replace '&#x27;',"'" -replace '&amp;','&'
    $inserts += "    <meta name=`"twitter:description`" content=`"$d`">"
  }
  if (-not ($content -match 'name="twitter:image"') -and -not [string]::IsNullOrEmpty($ogImage)) {
    $inserts += "    <meta name=`"twitter:image`" content=`"$ogImage`">"
  }

  if ($inserts.Count -eq 0) {
    Write-Host "[ok] $($f.Name) already complete" -ForegroundColor DarkGray
    continue
  }

  # ---- Inject right after the existing twitter:card line ----
  $twCardEscaped = [regex]::Escape($twCard)
  $pattern = '(<meta name="twitter:card"\s+content="' + $twCardEscaped + '">)'
  $block = $inserts -join "`n"
  $content = [regex]::Replace($content, $pattern, "`$1`n$block", 1)

  if ($content -ne $original) {
    [System.IO.File]::WriteAllText($f.FullName, $content, [System.Text.Encoding]::UTF8)
    Write-Host "[+] $($f.Name) - added $($inserts.Count) tag(s)" -ForegroundColor Green
    $updated++
  } else {
    $skipped++
  }
}

Write-Host ""
Write-Host "Done. updated=$updated, skipped=$skipped" -ForegroundColor Cyan
