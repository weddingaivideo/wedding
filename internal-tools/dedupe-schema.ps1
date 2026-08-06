<#
.SYNOPSIS
  Remove the duplicate Organization/LocalBusiness/WebSite JSON-LD blocks
  from every page except index.html. The home page keeps the full set;
  every other page only needs its page-specific schema
  (BreadcrumbList, Service, FAQPage, Article, etc.).

.EXAMPLE
  pwsh ./dedupe-schema.ps1
#>

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$keepTypes = @("Organization", "LocalBusiness", "WebSite")

$files = Get-ChildItem -Path $root -Filter "*.html" -Recurse |
         Where-Object { $_.Name -ne "google-site-verification.html" -and $_.Name -ne "index.html" }

$updated = 0; $removed = 0
foreach ($f in $files) {
  $content = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
  $original = $content

  # Find each JSON-LD block; if its first @type is in $keepTypes, delete the whole <script> block
  $pat = '(?s)<script type="application/ld\+json">(\s*\{.*?\})\s*</script>'
  $content = [regex]::Replace($content, $pat, {
    param($m)
    $body = $m.Groups[1].Value
    $typeM = [regex]::Match($body, '"@type"\s*:\s*"([^"]+)"')
    if ($typeM.Success -and $script:keepTypes -contains $typeM.Groups[1].Value) {
      $script:removed++
      return ""
    }
    return $m.Value
  })

  if ($content -ne $original) {
    # Collapse multiple blank lines that the removal leaves behind
    $content = [regex]::Replace($content, "(`r?`n){3,}", "`r`n`r`n")
    [System.IO.File]::WriteAllText($f.FullName, $content, [System.Text.Encoding]::UTF8)
    Write-Host "[+] $($f.Name)" -ForegroundColor Green
    $updated++
  }
}

Write-Host ""
Write-Host "Done. files updated: $updated, schema blocks removed: $removed" -ForegroundColor Cyan
