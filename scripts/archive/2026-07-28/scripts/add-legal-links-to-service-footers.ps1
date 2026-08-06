# Add Privacy/Terms links to service page footer-bottom
$root = "C:\Users\qiaoshan\.openclaw\workspace\weddingai"
$serviceDirs = @("video-enhancement","absence-compensation","personalization")
$fixed = 0

foreach ($d in $serviceDirs) {
    $htmls = Get-ChildItem "$root\services\$d" -Filter "*.html" -File
    foreach ($h in $htmls) {
        $c = Get-Content $h.FullName -Raw
        $origC = $c
        $oldFooter = '<div class="footer-bottom"><div class="container"><p>© 2026 WeddingAI.video. All rights reserved.</p></div></div>'
        $newFooter = '<div class="footer-bottom"><div class="container"><p>© 2026 WeddingAI.video. All rights reserved.</p><p><a href="../../privacy.html">Privacy Policy</a> · <a href="../../terms.html">Terms of Service</a></p></div></div>'
        $c = $c -replace [regex]::Escape($oldFooter), $newFooter
        if ($c -ne $origC) {
            Set-Content $h.FullName $c -NoNewline
            Write-Host "FIXED: $($h.Name)"
            $fixed++
        }
    }
}

Write-Host "---"
Write-Host "Total fixed: $fixed"
