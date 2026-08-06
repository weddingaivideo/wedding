$urls = @(
    'services/video-enhancement/vintage-restoration/gallery/',
    'services/video-enhancement/vintage-restoration/about/',
    'diy-wedding-video-phone.md',
    'wedding-video-cost-2026-new/',
    'weddingai-video-guide/',
    'make-first-ai-wedding-video/',
    'wedding-video-music-guide-new/',
    'blog/wedding-video-under-500/',
    'wedding-highlight-video.md',
    'couple-slideshow-video.md',
    'services/personalization/wedding-invitation/',
    'wedding-video-trends-2026.md',
    'ai-tools-for-photographers.md',
    'photographer-upsell-video.md',
    'weddingai-video-case-studies',
    'ai-wont-replace-photographers.md',
    'wedding-slideshow-guide.md',
    'blog/destination-wedding-video-guide/',
    'ai-editor-vs-traditional-editing/',
    'how-to-make-wedding-video',
    'wedding-video-captions',
    'wedding-video-music-guide-new',
    'weddingai-video-case-studies/',
    'services/video-enhancement/',
    'bride-wedding-video-checklist.md',
    'destination-wedding-video-guide.md',
    'wedding-video-without-videographer.md',
    'small-wedding-video-ideas.md',
    'wedding-package-video-upsell.md',
    'wedding-video-photo-checklist',
    'services/personalization/'
)
$results = @()
foreach ($u in $urls) {
    $full = "https://weddingai.video/$u"
    try {
        $r = Invoke-WebRequest -Uri $full -Method Head -UseBasicParsing -TimeoutSec 12 -MaximumRedirection 0 -ErrorAction Stop
        $code = $r.StatusCode
        $loc = ($r.Headers['Location'] -join ',')
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        $loc = ($_.Exception.Response.Headers['Location'] -join ',')
        if (-not $code) { $code = 'ERR' }
    }
    $results += [PSCustomObject]@{ URL = $u; Status = $code; Location = $loc }
    Start-Sleep -Milliseconds 200
}
$ok    = ($results | Where-Object { $_.Status -eq 200 }).Count
$redir = ($results | Where-Object { $_.Status -in @(301,308) }).Count
$bad   = ($results | Where-Object { $_.Status -eq 404 }).Count
Write-Host ""
Write-Host "===== RESULT: 200=$ok  301/308=$redir  404=$bad  (of $($results.Count)) ====="
Write-Host ""
$results | Format-Table -AutoSize -Wrap
