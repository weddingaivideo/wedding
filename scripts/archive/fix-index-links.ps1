$path = "C:\Users\qiaoshan\.openclaw\workspace\weddingai\index.html"
$c = Get-Content $path -Raw

# Fix trailing-slash service links in index.html
$c = $c -replace 'href="/services/video-enhancement/dv-repair/"', 'href="/services/video-enhancement/dv-repair.html"'
$c = $c -replace 'href="/services/absence-compensation/family-message/"', 'href="/services/absence-compensation/family-message.html"'
$c = $c -replace 'href="/services/personalization/ai-video-generator/"', 'href="/services/personalization/ai-video-generator.html"'
$c = $c -replace 'href="/services/venue/interactive-screen/"', 'href="/services/venue/interactive-screen.html"'
$c = $c -replace 'href="/services/personalization/pet-wedding/"', 'href="/services/personalization/pet-wedding.html"'
$c = $c -replace 'href="/services/personalization/wedding-trailer/"', 'href="/services/personalization/wedding-trailer.html"'
$c = $c -replace 'href="/services/venue/"', 'href="/services/"'
$c = $c -replace 'href="https://weddingai\.video/services/"', 'href="/services/"'

Set-Content $path $c -NoNewline
Write-Host "index.html links fixed"
