<#
.SYNOPSIS
  Inject <link rel="preconnect"> and <link rel="dns-prefetch"> tags for
  known third-party origins into every HTML page's <head>.

.EXAMPLE
  pwsh ./inject-preconnect.ps1
#>

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

# Origins to preconnect to. `crossorigin` = true because we use them
# for script/XHR/fetch (which need CORS). Includes:
#  - Google AdSense (pagead2.googlesyndication.com)
#  - Google Tag Manager / GA4 (googletagmanager.com, google-analytics.com)
#  - Cloudflare Web Analytics (static.cloudflareinsights.com)
$origins = @(
  @{ url = "https://pagead2.googlesyndication.com"; cross = $true;  type = "preconnect" },
  @{ url = "https://www.googletagmanager.com";    cross = $true;  type = "preconnect" },
  @{ url = "https://www.google-analytics.com";     cross = $true;  type = "preconnect" },
  @{ url = "https://static.cloudflareinsights.com"; cross = $true; type = "preconnect" }
)

$files = Get-ChildItem -Path $root -Filter "*.html" -Recurse |
         Where-Object { $_.Name -ne "google-site-verification.html" }

$updated = 0
foreach ($f in $files) {
  $content = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
  $original = $content

  # Idempotency check
  if ($content -match 'rel="preconnect"[^>]*pagead2\.googlesyndication\.com') {
    continue
  }

  # Build the link tags
  $links = @()
  foreach ($o in $origins) {
    $cross = if ($o.cross) { ' crossorigin' } else { '' }
    $links += "    <link rel=`"preconnect`" href=`"$($o.url)`"$cross>"
  }
  # Fallback for browsers without preconnect support
  foreach ($o in $origins) {
    $links += "    <link rel=`"dns-prefetch`" href=`"$($o.url)`">"
  }
  $block = $links -join "`n"

  # Inject right after the <meta name="viewport"> line (near the top of <head>)
  $pattern = '(<meta name="viewport"[^>]+>)'
  $content = [regex]::Replace($content, $pattern, "`$1`n$block", 1)

  if ($content -ne $original) {
    [System.IO.File]::WriteAllText($f.FullName, $content, [System.Text.Encoding]::UTF8)
    Write-Host "[+] $($f.Name)" -ForegroundColor Green
    $updated++
  }
}

Write-Host ""
Write-Host "Done. files updated: $updated" -ForegroundColor Cyan
