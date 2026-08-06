# Check if production serves the key file with the right body
Write-Host '=== Body of production key file ==='
try {
    $r = Invoke-WebRequest -Uri 'https://weddingai.video/bca20c476d04af209950cbf5921e821d.txt' -UseBasicParsing
    Write-Host "Status: $($r.StatusCode)"
    Write-Host "Content-Type: $($r.Headers['Content-Type'])"
    Write-Host "Body: '$($r.Content)'"
    Write-Host "Body length: $($r.Content.Length)"
} catch { Write-Host "FAIL: $($_.Exception.Message)" }

Write-Host ''
Write-Host '=== Test IndexNow host via DNS (which IP does it hit?) ==='
# IndexNow fetches from the host - check what IP DNS resolves to
Resolve-DnsName -Name weddingai.video -Type A | Select-Object IPAddress
