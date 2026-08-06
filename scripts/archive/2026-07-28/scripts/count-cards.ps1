$resp = Invoke-WebRequest -Uri 'https://weddingai.video/gallery' -UseBasicParsing -MaximumRedirection 5 -ErrorAction Continue
$content = $resp.Content
Write-Host "Final URL: $($resp.BaseResponse.RequestMessage.RequestUri)"
$count = ([regex]::Matches($content, 'data-category=')).Count
$filters = ([regex]::Matches($content, 'data-filter=')).Count
Write-Host "Total case cards on page: $count"
Write-Host "Total filter buttons: $filters"
