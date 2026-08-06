$resp = Invoke-WebRequest -Uri 'https://weddingai.video' -UseBasicParsing -MaximumRedirection 5 -ErrorAction Continue
Write-Host 'Final status:' $resp.StatusCode
Write-Host 'Has Featured Case Studies section:' ($resp.Content -match 'Featured Case Studies')
Write-Host 'Has Kim Family case:' ($resp.Content -match 'The Kim Family')
Write-Host 'Has Carolina case:' ($resp.Content -match 'Carolina R')
Write-Host 'Has View All 25 button:' ($resp.Content -match 'View All 25 Case Studies')
