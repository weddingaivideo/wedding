$root = "C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# Fix trailing-slash footer nav links in core pages
$corePages = @(
    "$root\about.html",
    "$root\gallery.html",
    "$root\order.html",
    "$root\success.html"
)

foreach ($page in $corePages) {
    $c = Get-Content $page -Raw
    $original = $c

    # Fix absolute https://weddingai.video URLs with trailing slashes
    $c = $c -replace 'href="https://weddingai\.video/about/"', 'href="/about.html"'
    $c = $c -replace 'href="https://weddingai\.video/gallery/"', 'href="/gallery.html"'
    $c = $c -replace 'href="https://weddingai\.video/order/"', 'href="/order.html"'
    $c = $c -replace 'href="https://weddingai\.video/success/"', 'href="/success.html"'
    $c = $c -replace 'href="https://weddingai\.video/services/"', 'href="/services/"'
    $c = $c -replace 'href="https://weddingai\.video/services"', 'href="/services"'

    # Fix relative /services/ links with trailing slashes in nav
    $c = $c -replace 'href="/services/video-enhancement/dv-repair/"', 'href="/services/video-enhancement/dv-repair.html"'
    $c = $c -replace 'href="/services/personalization/ai-video-generator/"', 'href="/services/personalization/ai-video-generator.html"'
    $c = $c -replace 'href="/services/personalization/pet-wedding/"', 'href="/services/personalization/pet-wedding.html"'
    $c = $c -replace 'href="/services/venue/"', 'href="/services/"'

    if ($c -ne $original) {
        Set-Content $page $c -NoNewline
        Write-Host "Fixed: $page"
    } else {
        Write-Host "No changes: $page"
    }
}

Write-Host "Done."
