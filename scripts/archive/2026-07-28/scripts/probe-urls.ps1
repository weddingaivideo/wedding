# Try /about (no extension) with redirect following, to see if the *final* content is right
$u = 'https://weddingai-video.pages.dev/about'
try {
    $r = Invoke-WebRequest -Uri $u -UseBasicParsing -ErrorAction Stop
    Write-Host "Status: $($r.StatusCode)"
    Write-Host "Has 'Service' schema: $($r.Content -match '"@type": "Service"')"
    Write-Host "Has 'Product' schema: $($r.Content -match '"@type": "Product"')"
    Write-Host "Has 'FAQPage' schema: $($r.Content -match '"@type": "FAQPage"')"
    Write-Host "Has 'BreadcrumbList': $($r.Content -match '"@type": "BreadcrumbList"')"
    Write-Host "Page title: $(if ($r.Content -match '<title>([^<]+)') { $Matches[1] } else { '?' })"
} catch {
    Write-Host "Error: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        Write-Host "Status: $($_.Exception.Response.StatusCode.value__)"
    }
}
