# Standardize GA4 snippet across all HTML files.
# Uses the same deferred-load pattern as inject-lazy-gtag.ps1:
#   - gtag.js (G-4FE7KSJDNB, ~159 KiB) deferred to first user interaction or
#     browser idle; never loads at all on bouncers.
#   - send_page_view: false + manual pageview via s.onload
#   - transport_type: 'beacon' (off-thread send)
param(
    [string]$NewId = "G-4FE7KSJDNB"
)

$root = "C:\Users\qiaoshan\.openclaw\workspace\weddingai"
$htmlFiles = Get-ChildItem $root -Recurse -Filter "*.html" -File | Where-Object { $_.Name -ne "google-site-verification.html" }

# Build the canonical lazy-load snippet (here-string keeps single-quote escaping sane).
$canonical = @"
    <!-- Google tag (gtag.js) — deferred to first interaction or idle (avoids wasted bytes on bouncers) -->
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', '$NewId', { send_page_view: false, transport_type: 'beacon' });

      window.__loadGtag = function() {
        if (window.__gtagLoaded) return;
        window.__gtagLoaded = true;
        var s = document.createElement('script');
        s.src = 'https://www.googletagmanager.com/gtag/js?id=$NewId';
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

      ['scroll','click','touchstart','keydown'].forEach(function(evt){
        window.addEventListener(evt, window.__loadGtag, { once: true, passive: true, capture: true });
      });
      window.addEventListener('load', function() {
        if ('requestIdleCallback' in window) {
          requestIdleCallback(window.__loadGtag, { timeout: 4000 });
        } else {
          setTimeout(window.__loadGtag, 3000);
        }
      });
    </script>
"@

$fixed = 0
$skipped = 0
foreach ($file in $htmlFiles) {
    $c = Get-Content $file.FullName -Raw
    $origC = $c

    # Find the start of the GA4 comment (any variant) OR the orphan <script> if
    # the comment was already removed by an earlier pass.
    $startIdx = $c.IndexOf('<!-- Google Analytics 4')
    $isOrphan = $false
    if ($startIdx -lt 0) {
        $startIdx = $c.IndexOf('<!-- Google tag (gtag.js)')
    }
    if ($startIdx -lt 0) {
        # Orphan block: the old "queue only" pattern that set up dataLayer+config
        # but never loaded gtag.js. Replace it with the canonical lazy-load.
        $orphanMatch = [regex]::Match($c, '(?s)<script>\s*window\.dataLayer = window\.dataLayer \|\| \[\];\s*function gtag\(\)\{dataLayer\.push\(arguments\);\}\s*gtag\(.js., new Date\(\)\);\s*gtag\(.config., .*?\);\s*</script>')
        if ($orphanMatch.Success) {
            $startIdx = $orphanMatch.Index
            $isOrphan = $true
        }
    }

    if ($startIdx -lt 0) {
        Write-Host "SKIP:  $($file.Name) (no GA4 comment or orphan block found)"
        $skipped++
        continue
    }

    # Skip files that already use the new lazy-load pattern. This covers both
    # the nonce-protected main pages (have __loadGtag) and any page where the
    # canonical was already applied with the same __loadGtag marker.
    if ($c -match 'window\.__loadGtag') {
        Write-Host "SKIP:  $($file.Name) (already has lazy-load gtag)"
        $skipped++
        continue
    }

    if ($isOrphan) {
        $endIdx = $startIdx + $orphanMatch.Length
    } else {
        # Find the LAST </script> in the GA4 block (the inner one — not the async src tag)
        $searchFrom = $startIdx
        $endIdx = -1
        while ($true) {
            $next = $c.IndexOf('</script>', $searchFrom)
            if ($next -lt 0) { break }
            $endIdx = $next
            $searchFrom = $next + 1
        }
        if ($endIdx -lt 0) {
            Write-Host "SKIP:  $($file.Name) (no </script> found)"
            $skipped++
            continue
        }
        $endIdx += '</script>'.Length
    }

    $before = $c.Substring(0, $startIdx)
    $after = $c.Substring($endIdx)

    if ($isOrphan) {
        $before = $before -replace '(\r?\n)+\s*$', "`n"
        $newC = $before + "`n" + $canonical + "`n" + $after
        Set-Content $file.FullName $newC -NoNewline
        Write-Host "FIXED ORPHAN -> LAZY: $($file.Name)"
        $fixed++
    } else {
        $newC = $before + $canonical + $after
        Set-Content $file.FullName $newC -NoNewline
        Write-Host "FIXED: $($file.Name)"
        $fixed++
    }
}

Write-Host "---"
Write-Host "Total fixed: $fixed"
Write-Host "Total skipped: $skipped"

# Verify
Write-Host ""
Write-Host "=== Verification ==="
$usesLazy = 0
$usesCorrectId = 0
$hasManualPageview = 0
$noPagePath = 0
foreach ($file in $htmlFiles) {
    $c = Get-Content $file.FullName -Raw
    if ($c -match 'window\.__loadGtag') { $usesLazy++ }
    if ($c -match "gtag/js\?id=$NewId") { $usesCorrectId++ }
    if ($c -match "gtag\('event', 'page_view'") { $hasManualPageview++ }
    if ($c -notmatch 'page_path:') { $noPagePath++ }
}
Write-Host "Pages with lazy-load gtag (window.__loadGtag): $usesLazy / $($htmlFiles.Count)"
Write-Host "Pages with gtag.js id=${NewId}:                $usesCorrectId / $($htmlFiles.Count)"
Write-Host "Pages with manual pageview event:              $hasManualPageview / $($htmlFiles.Count)"
Write-Host "Pages WITHOUT page_path:                       $noPagePath / $($htmlFiles.Count)"
