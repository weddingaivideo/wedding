# Re-insert the GA4 inner script that was accidentally removed
# This fixes the broken state where the page has the gtag.js loader but no gtag() calls.

$root = "C:\Users\qiaoshan\.openclaw\workspace\weddingai"
$htmlFiles = Get-ChildItem $root -Recurse -Filter "*.html" -File | Where-Object { $_.Name -ne "google-site-verification.html" }

$fixed = 0
$skipped = 0
foreach ($file in $htmlFiles) {
    $c = Get-Content $file.FullName -Raw
    $origC = $c

    # Detect broken state: has the new comment + async script, but NO inner script with gtag('config', ...)
    $hasComment = $c -match '<!-- Google tag \(gtag\.js\) -->'
    $hasAsync = $c -match 'googletagmanager\.com/gtag/js\?id=G-[A-Z0-9]+"></script>'
    $hasInnerConfig = $c -match "gtag\('config', 'G-[A-Z0-9]+'\);"

    if ($hasComment -and $hasAsync -and -not $hasInnerConfig) {
        # Need to insert the inner script after the async </script> tag
        $innerScript = @'

    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());

      gtag('config', 'G-4FE7KSJDNB');
    </script>
'@

        # Find the async script and insert after its closing tag
        $asyncPattern = '(<script async src="https://www\.googletagmanager\.com/gtag/js\?id=G-[A-Z0-9]+"></script>)'
        $c = [regex]::Replace($c, $asyncPattern, "`$1$innerScript", 1)

        Set-Content $file.FullName $c -NoNewline
        Write-Host "FIXED: $($file.Name)"
        $fixed++
    } elseif ($hasInnerConfig) {
        Write-Host "OK:    $($file.Name) (already has inner config)"
        $skipped++
    } else {
        Write-Host "SKIP:  $($file.Name) (unrecognized state)"
        $skipped++
    }
}

Write-Host "---"
Write-Host "Fixed: $fixed"
Write-Host "Skipped/OK: $skipped"

# Verify
Write-Host ""
Write-Host "=== Verification ==="
$withInnerConfig = 0
$withoutPagePath = 0
foreach ($file in $htmlFiles) {
    $c = Get-Content $file.FullName -Raw
    if ($c -match "gtag\('config', 'G-4FE7KSJDNB'\);") { $withInnerConfig++ }
    if ($c -notmatch 'page_path:') { $withoutPagePath++ }
}
Write-Host "Pages with canonical inner config: $withInnerConfig / $($htmlFiles.Count)"
Write-Host "Pages without page_path:           $withoutPagePath / $($htmlFiles.Count)"
