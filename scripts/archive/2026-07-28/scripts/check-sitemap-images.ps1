$content = (Invoke-WebRequest -Uri 'https://weddingai-video.pages.dev/sitemap.xml' -UseBasicParsing).Content
$lines = $content -split "`n"
$imageLines = $lines | Where-Object { $_ -match 'image:loc' -and ($_ -match 'catalog-|petwedding-|familymsg-|trailer-feat-') }
Write-Host "New images found in sitemap:"
$imageLines | ForEach-Object { $_.Trim() }
Write-Host ""
Write-Host "Total image entries: $(($lines | Where-Object { $_ -match 'image:loc' }).Count)"
Write-Host "New images (catalog/petwedding/familymsg/trailer-feat): $($imageLines.Count)"
