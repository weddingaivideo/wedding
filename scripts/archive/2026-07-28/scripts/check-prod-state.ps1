# Wait a moment for cache to settle
Start-Sleep -Seconds 5

Write-Host '=== Production domain ==='
try {
    $code = (Invoke-WebRequest -Uri 'https://weddingai.video' -UseBasicParsing -Method Head -TimeoutSec 15).StatusCode
    Write-Host "prod: $code"
} catch { Write-Host "prod FAIL: $($_.Exception.Message)" }

Write-Host '=== Production key file ==='
try {
    $r = Invoke-WebRequest -Uri 'https://weddingai.video/bca20c476d04af209950cbf5921e821d.txt' -UseBasicParsing -TimeoutSec 15
    Write-Host "key: $($r.Content) (status $($r.StatusCode))"
} catch { Write-Host "key FAIL: $($_.Exception.Message)" }

Write-Host '=== Production avatar ==='
try {
    $code = (Invoke-WebRequest -Uri 'https://weddingai.video/images/avatar-carolina.jpg' -UseBasicParsing -Method Head -TimeoutSec 15).StatusCode
    Write-Host "avatar: $code"
} catch { Write-Host "avatar FAIL: $($_.Exception.Message)" }
