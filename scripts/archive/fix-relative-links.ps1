# Fix relative path trailing slashes in service detail pages
# and update footer nav links to use .html extensions

$root = "C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# 1. Fix relative links in dv-repair.html
$dv = Get-Content "$root\services\video-enhancement\dv-repair.html" -Raw
$dv = $dv -replace 'href="\.\./film-digitization/"', 'href="film-digitization.html"'
$dv = $dv -replace 'href="\.\./slow-motion/"', 'href="slow-motion.html"'
$dv = $dv -replace 'href="\.\./\.\./absence-compensation/family-tribute/"', 'href="../../absence-compensation/family-tribute.html"'
Set-Content "$root\services\video-enhancement\dv-repair.html" $dv -NoNewline
Write-Host "dv-repair.html relative links fixed"

# 2. Fix footer nav links in ALL service detail pages
# Pattern: href="https://weddingai.video/services/category/service"
# These are in the footer of each service page - replace with relative .html links

$servicePages = Get-ChildItem "$root\services" -Recurse -Filter "*.html" | Where-Object { $_.Name -ne "index.html" }

foreach ($page in $servicePages) {
    $content = Get-Content $page.FullName -Raw
    $original = $content

    # Fix https://weddingai.video/services/ URLs to relative paths
    $content = $content -replace 'href="https://weddingai\.video/services/video-enhancement/dv-repair/"', 'href="dv-repair.html"'
    $content = $content -replace 'href="https://weddingai\.video/services/video-enhancement/film-digitization/"', 'href="film-digitization.html"'
    $content = $content -replace 'href="https://weddingai\.video/services/video-enhancement/slow-motion/"', 'href="slow-motion.html"'
    $content = $content -replace 'href="https://weddingai\.video/services/absence-compensation/family-tribute/"', 'href="../../absence-compensation/family-tribute.html"'
    $content = $content -replace 'href="https://weddingai\.video/services/absence-compensation/family-message/"', 'href="../../absence-compensation/family-message.html"'
    $content = $content -replace 'href="https://weddingai\.video/services/absence-compensation/celebrity-message/"', 'href="../../absence-compensation/celebrity-message.html"'
    $content = $content -replace 'href="https://weddingai\.video/services/personalization/ai-video-generator/"', 'href="../../personalization/ai-video-generator.html"'
    $content = $content -replace 'href="https://weddingai\.video/services/personalization/wedding-trailer/"', 'href="../../personalization/wedding-trailer.html"'
    $content = $content -replace 'href="https://weddingai\.video/services/personalization/pet-wedding/"', 'href="../../personalization/pet-wedding.html"'
    $content = $content -replace 'href="https://weddingai\.video/services/personalization/multilingual/"', 'href="../../personalization/multilingual.html"'
    $content = $content -replace 'href="https://weddingai\.video/services/personalization/cartoon-style/"', 'href="../../personalization/cartoon-style.html"'
    $content = $content -replace 'href="https://weddingai\.video/services/personalization/meme-generator/"', 'href="../../personalization/meme-generator.html"'
    $content = $content -replace 'href="https://weddingai\.video/services/personalization/wedding-invitation/"', 'href="../../personalization/wedding-invitation.html"'
    $content = $content -replace 'href="https://weddingai\.video/services/venue/interactive-screen/"', 'href="../../venue/interactive-screen.html"'
    $content = $content -replace 'href="https://weddingai\.video/services/venue/real-time-cut/"', 'href="../../venue/real-time-cut.html"'
    $content = $content -replace 'href="https://weddingai\.video/services/venue/live-comments/"', 'href="../../venue/live-comments.html"'

    if ($content -ne $original) {
        Set-Content $page.FullName $content -NoNewline
        Write-Host "Fixed footer links: $($page.Name)"
    }
}

Write-Host "Done."
