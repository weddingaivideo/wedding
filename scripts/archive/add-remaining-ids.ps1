$path = "C:\Users\qiaoshan\.openclaw\workspace\weddingai\services\index.html"
$content = Get-Content $path -Raw

# Fix video-enhancement section (color-bg)
$content = $content -replace '(<section class="section service-group" style="background: var\(--color-bg\);">)', '<section id="video-enhancement" class="section service-group" style="background: var(--color-bg);">'

# Fix personalization section (color-bg-alt)
$content = $content -replace '(<section class="section service-group" style="background: var\(--color-bg-alt\);">)', '<section id="personalization" class="section service-group" style="background: var(--color-bg-alt);">'

Set-Content $path $content -NoNewline

# Verify all 4 IDs are present
$verify = Get-Content $path -Raw
$ids = [regex]::Matches($verify, '<section id="(video-enhancement|absence-compensation|personalization|venue)"') | ForEach-Object { $_.Value }
Write-Host "All section IDs:"
$ids | ForEach-Object { Write-Host "  $_" }
