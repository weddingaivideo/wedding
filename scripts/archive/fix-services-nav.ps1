# Fix services/index.html:
# 1. Add id attributes to section headers for anchor links
# 2. Remove trailing slashes from all relative service links

$path = "C:\Users\qiaoshan\.openclaw\workspace\weddingai\services\index.html"
$content = Get-Content $path -Raw

# 1. Add section IDs before each service group header
$content = $content -replace '(<!-- Video Enhancement -->.*?<section class="section service-group".*?>.*?<header class="service-group-header">)', '$1'
$content = $content -replace '(<h2>🎞️ Video Enhancement)', '<section id="video-enhancement"></section>$1'
$content = $content -replace '(<h2>💛 Never Miss a Moment)', '<section id="absence-compensation"></section>$1'
$content = $content -replace '(<h2>✨ Personalization)', '<section id="personalization"></section>$1'
$content = $content -replace '(<h2>🎉 Live Venue)', '<section id="venue"></section>$1'

# 2. Remove trailing slashes from relative service links (but keep absolute /services/ links)
# Replace patterns like: href="category/service/" -> href="category/service.html"
$content = $content -replace 'href="(video-enhancement|absence-compensation|personalization|venue)/([^/"]+)/"', 'href="$1/$2.html"'

Set-Content $path $content -NoNewline
Write-Host "services/index.html updated"

# Verify result
$newContent = Get-Content $path -Raw
$linksWithSlash = [regex]::Matches($newContent, 'href="[^"]+/([^"/]+)/"') | ForEach-Object { $_.Value } | Select-Object -First 5
if ($linksWithSlash) {
    Write-Host "WARNING: Still found trailing slash links:"
    $linksWithSlash | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host "All trailing slashes removed from relative links."
}

$sectionIds = [regex]::Matches($newContent, 'id="(video-enhancement|absence-compensation|personalization|venue)"') | ForEach-Object { $_.Value } | Select-Object -Unique
Write-Host "Section IDs found: $sectionIds"
