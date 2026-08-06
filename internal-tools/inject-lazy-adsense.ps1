<#
.SYNOPSIS
  Replace the synchronous AdSense <script async ...> tag in every HTML page
  with a lazy-loading version that runs ~3s after the page is idle.

  This avoids the 43ms forced reflow caused by show_ads_impl_fy2021.js
  during initial layout. We can't modify Google's script, but we can defer
  its insertion until after the main content has rendered.

.EXAMPLE
  pwsh ./inject-lazy-adsense.ps1
#>

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

# The current AdSense tag (verbatim across all pages)
$adClient = "ca-pub-1670381960525419"
$oldScript = '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=' + $adClient + '"' + "`r?`n         crossorigin=`"anonymous`"></script>"
$oldScriptLf = '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=' + $adClient + '"' + "`n         crossorigin=`"anonymous`"></script>"

# The replacement: a tiny inline script that schedules the AdSense load
# after the page is idle. requestIdleCallback with a 3s timeout fallback.
$newSnippet = @"
<!-- Google AdSense (lazy-loaded to avoid forced reflow during initial paint) -->
    <script>
    window.addEventListener('load', function() {
      var loadAds = function() {
        var s = document.createElement('script');
        s.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=$adClient';
        s.async = true;
        s.crossOrigin = 'anonymous';
        s.setAttribute('data-ad-lazy', '1');
        document.head.appendChild(s);
      };
      // Prefer requestIdleCallback; fall back to setTimeout for Safari / older browsers
      if ('requestIdleCallback' in window) {
        requestIdleCallback(loadAds, { timeout: 4000 });
      } else {
        setTimeout(loadAds, 3000);
      }
    });
    </script>
"@

$files = Get-ChildItem -Path $root -Filter "*.html" -Recurse |
         Where-Object { $_.Name -ne "google-site-verification.html" }

$updated = 0; $already = 0
foreach ($f in $files) {
  $content = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
  $original = $content

  # Idempotency check
  if ($content -match 'data-ad-lazy="1"') {
    $already++
    continue
  }

  # Try both CRLF and LF variants of the old script tag
  $changed = $false
  if ($content -match [regex]::Escape($oldScript)) {
    $content = $content -replace [regex]::Escape($oldScript), $newSnippet
    $changed = $true
  } elseif ($content -match [regex]::Escape($oldScriptLf)) {
    $content = $content -replace [regex]::Escape($oldScriptLf), $newSnippet
    $changed = $true
  } else {
    # Generic fallback: regex match any adsbygoogle.js script tag
    $pat = '(?s)<!--\s*Google\s+AdSense[^>]*-->\s*<script[^>]*adsbygoogle\.js[^>]*></script>'
    if ($content -match $pat) {
      $content = [regex]::Replace($content, $pat, $newSnippet.TrimEnd("`n"))
      $changed = $true
    }
  }

  if ($changed -and $content -ne $original) {
    [System.IO.File]::WriteAllText($f.FullName, $content, [System.Text.Encoding]::UTF8)
    Write-Host "[+] $($f.Name)" -ForegroundColor Green
    $updated++
  } elseif (-not $changed) {
    Write-Host "[skip] $($f.Name) - no AdSense script found" -ForegroundColor DarkGray
  }
}

Write-Host ""
Write-Host "Done. updated: $updated, already lazy: $already" -ForegroundColor Cyan
