# Add GA4 to all HTML files in weddingai folder
# Replace G-XXXXXXXXXX with actual GA4 Measurement ID before running.
# Uses the same deferred-load pattern as the main pages (interaction + idle fallback)
# so gtag.js (~159 KiB) never blocks the critical render path and never loads at
# all on bounce-only visits.

$gaId = "G-XXXXXXXXXX"

$ga4Snippet = @"

    <!-- Google tag (gtag.js) — deferred to first interaction or idle (avoids wasted bytes on bouncers) -->
    <script>
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

$files = Get-ChildItem -Path "C:\Users\qiaoshan\.openclaw\workspace\weddingai" -Recurse -Include "*.html"
$count = 0

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw
    
    # Skip if GA4 already exists
    if ($content -match 'googletagmanager.com/gtag') {
        Write-Host "SKIP (already has GA4): $($file.Name)"
        continue
    }
    
    # Find the </head> tag and insert GA4 before it
    if ($content -match '(</head>)') {
        $newContent = $content -replace '(</head>)', "$ga4Snippet`n`$1"
        Set-Content -Path $file.FullName -Value $newContent -NoNewline
        Write-Host "ADDED: $($file.Name)"
        $count++
    }
}

Write-Host "`nTotal files updated: $count"
