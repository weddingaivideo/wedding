$path = "C:\Users\qiaoshan\.openclaw\workspace\weddingai\services\index.html"
$content = Get-Content $path -Raw

# Fix: Move misplaced section IDs from inside <header> to after <section> opening tag
# Remove wrongly placed section IDs inside header
$content = $content -replace '<section id="video-enhancement"></section><h2>🎞️ Video Enhancement', '<h2>🎞️ Video Enhancement'
$content = $content -replace '<section id="absence-compensation"></section><h2>💛 Never Miss a Moment', '<h2>💛 Never Miss a Moment'
$content = $content -replace '<section id="personalization"></section><h2>✨ Personalization', '<h2>✨ Personalization'
$content = $content -replace '<section id="venue"></section><h2>🎉 Live Venue', '<h2>🎉 Live Venue'

# Add section IDs properly right after the opening <section ...> tag of each service group
# Pattern: <section class="section service-group" ...>
# We need to add id="xxx" to the section tag

# Video Enhancement section (has style="background: var(--color-bg);")
$content = $content -replace '(<section class="section service-group" style="background: var\(--color-bg\);">)', '$1' -replace '(<section class="section service-group" style="background: var\(--color-bg\);">)(\s*<div class="container">\s*<header class="service-group-header">\s*<h2>🎞️ Video Enhancement)', '<section id="video-enhancement" class="section service-group" style="background: var(--color-bg);">$2'

# Absence Compensation section
$content = $content -replace '(<section class="section service-group" style="background: var\(--color-white\);">)', '$1' -replace '(<section class="section service-group" style="background: var\(--color-white\);">)(\s*<div class="container">\s*<header class="service-group-header">\s*<h2>💛 Never Miss a Moment)', '<section id="absence-compensation" class="section service-group" style="background: var(--color-white);">$2'

# Personalization section (has style="background: var(--color-bg-alt);")
$content = $content -replace '(<section class="section service-group" style="background: var\(--color-bg-alt\);">)', '$1' -replace '(<section class="section service-group" style="background: var\(--color-bg-alt\);">)(\s*<div class="container">\s*<header class="service-group-header">\s*<h2>✨ Personalization)', '<section id="personalization" class="section service-group" style="background: var(--color-bg-alt);">$2'

# Venue section
$content = $content -replace '(<section class="section service-group" style="background: var\(--color-white\);">)', '$1' -replace '(<section class="section service-group" style="background: var\(--color-white\);">)(\s*<div class="container">\s*<header class="service-group-header">\s*<h2>🎉 Live Venue)', '<section id="venue" class="section service-group" style="background: var(--color-white);">$2'

Set-Content $path $content -NoNewline

# Verify
$new = Get-Content $path -Raw
$ids = [regex]::Matches($new, 'id="(video-enhancement|absence-compensation|personalization|venue)"') | ForEach-Object { $_.Value } | Select-Object -Unique
Write-Host "Section IDs: $ids"

$stillInHeader = $new -match 'header.*id="(video-enhancement|absence-compensation|personalization|venue)"'
Write-Host "Still in header: $stillInHeader"
