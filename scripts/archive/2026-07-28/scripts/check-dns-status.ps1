Write-Host '=== Preview URL ==='
try {
    $code = (Invoke-WebRequest -Uri 'https://ef787380.weddingai-video.pages.dev' -UseBasicParsing -Method Head).StatusCode
    Write-Host "preview: $code"
} catch { Write-Host "preview FAIL: $($_.Exception.Message)" }

Write-Host '=== Production domain ==='
try {
    $code = (Invoke-WebRequest -Uri 'https://weddingai.video' -UseBasicParsing -Method Head -TimeoutSec 10).StatusCode
    Write-Host "prod: $code"
} catch { Write-Host "prod FAIL: $($_.Exception.Message)" }

Write-Host '=== DNS ==='
Resolve-DnsName -Name weddingai.video -ErrorAction SilentlyContinue | Format-Table Name, Type, IPAddress, NameHost -AutoSize

Write-Host '=== Avatar image on preview ==='
try {
    $code = (Invoke-WebRequest -Uri 'https://ef787380.weddingai-video.pages.dev/images/avatar-carolina.jpg' -UseBasicParsing -Method Head).StatusCode
    Write-Host "carolina: $code"
} catch { Write-Host "FAIL" }
