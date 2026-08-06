$c = Get-Content "C:\Users\qiaoshan\.openclaw\workspace\weddingai\services\index.html" -Raw
$c = $c -replace '<section id="video-enhancement"></section>', ''
$c = $c -replace '<section id="absence-compensation"></section>', ''
$c = $c -replace '<section id="personalization"></section>', ''
$c = $c -replace '<section id="venue"></section>', ''
Set-Content "C:\Users\qiaoshan\.openclaw\workspace\weddingai\services\index.html" $c -NoNewline
Write-Host "Cleaned. Final section IDs:"
$verify = Get-Content "C:\Users\qiaoshan\.openclaw\workspace\weddingai\services\index.html" -Raw
$ids = [regex]::Matches($verify, '<section id="(video-enhancement|absence-compensation|personalization|venue)"') | ForEach-Object { $_.Value } | Select-Object -Unique
$ids | ForEach-Object { Write-Host "  $_" }
