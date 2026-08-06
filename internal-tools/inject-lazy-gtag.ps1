<#
.SYNOPSIS
  Replace the synchronous <script async src="googletagmanager.com/gtag/js?..."> 
  tag in every HTML page with a lazy-loading version. Mirrors the AdSense
  pattern. The 158.9 KiB gtag library (~64.6 KiB of which is unused code)
  gets deferred until first user interaction or browser idle, removing it
  from the critical render path AND skipping download entirely on bouncers.

.EXAMPLE
  pwsh ./inject-lazy-gtag.ps1
#>

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

$gaId = "G-4FE7KSJDNB"

$oldPattern = '(?s)<!--\s*Google tag \(gtag\.js\)\s*-->\s*<script async src="https://www\.googletagmanager\.com/gtag/js\?id=' + [regex]::Escape($gaId) + '"></script>\s*<script>\s*window\.dataLayer = window\.dataLayer \|\| \[\];\s*function gtag\(\)\{dataLayer\.push\(arguments\);\}\s*gtag\(.js., new Date\(\)\);\s*gtag\(.config., .' + [regex]::Escape($gaId) + '.\);\s*</script>'

$newSnippet = @"
<!-- Google tag (gtag.js) — deferred to first interaction or idle (avoids wasted bytes on bouncers) -->
    <script>
    // dataLayer must be set BEFORE gtag.js loads so queued events are captured
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', '$gaId', { send_page_view: false, transport_type: 'beacon' });

    window.__loadGtag = function() {
      if (window.__gtagLoaded) return;
      window.__gtagLoaded = true;
      var s = document.createElement('script');
      s.src = 'https://www.googletagmanager.com/gtag/js?id=$gaId';
      s.async = true;
      s.onload = function() {
        gtag('event', 'page_view', {
          page_title: document.title,
          page_location: location.href,
          page_path: location.pathname + location.search
        });
      };
      s.setAttribute('data-gtag-lazy', '1');
      document.head.appendChild(s);
    };

    // Engaged users: load on first interaction (scroll/click/touch/keydown).
    ['scroll','click','touchstart','keydown'].forEach(function(evt){
      window.addEventListener(evt, window.__loadGtag, { once: true, passive: true, capture: true });
    });
    // Passive readers / non-interactors: fallback to idle / load+3s.
    window.addEventListener('load', function() {
      if ('requestIdleCallback' in window) {
        requestIdleCallback(window.__loadGtag, { timeout: 4000 });
      } else {
        setTimeout(window.__loadGtag, 3000);
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

  # "Already lazy" detection covers BOTH the old idle-only block and the new
  # interaction+idle block (both stamp data-gtag-lazy="1" on the appended <script>).
  if ($content -match 'data-gtag-lazy="1"' -or $content -match 'window\.__loadGtag') {
    $already++
    continue
  }

  if ($content -match $oldPattern) {
    $content = [regex]::Replace($content, $oldPattern, $newSnippet.TrimEnd("`n"), 1)
  } else {
    # Generic fallback (handles formatting variations)
    $generic = '(?s)<!--\s*Google tag[^>]*-->\s*<script async src="https://www\.googletagmanager\.com/gtag/js\?id=' + [regex]::Escape($gaId) + '"></script>\s*<script>.*?</script>'
    if ($content -match $generic) {
      $content = [regex]::Replace($content, $generic, $newSnippet.TrimEnd("`n"), 1)
    } else {
      Write-Host "[skip] $($f.Name) - no gtag block found" -ForegroundColor DarkGray
      continue
    }
  }

  if ($content -ne $original) {
    [System.IO.File]::WriteAllText($f.FullName, $content, [System.Text.Encoding]::UTF8)
    Write-Host "[+] $($f.Name)" -ForegroundColor Green
    $updated++
  }
}

Write-Host ""
Write-Host "Done. updated: $updated, already lazy: $already" -ForegroundColor Cyan
