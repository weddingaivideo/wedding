try {
    $r = Invoke-WebRequest -Uri 'https://weddingai.video/bca20c476d04af209950cbf5921e821d.txt' -UseBasicParsing
    Write-Host "PROD: $($r.Content) (status $($r.StatusCode))"
} catch { Write-Host "PROD FAIL: $($_.Exception.Message)" }
try {
    $r2 = Invoke-WebRequest -Uri 'https://ef787380.weddingai-video.pages.dev/bca20c476d04af209950cbf5921e821d.txt' -UseBasicParsing
    Write-Host "PREVIEW: $($r2.Content) (status $($r2.StatusCode))"
} catch { Write-Host "PREVIEW FAIL: $($_.Exception.Message)" }
