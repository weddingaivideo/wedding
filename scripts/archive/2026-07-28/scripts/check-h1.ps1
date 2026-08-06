$pages = @('about.html', 'gallery.html', 'services/absence-compensation/family-tribute.html', 'services/personalization/cartoon-style.html', 'services/personalization/pet-wedding.html')
foreach ($rel in $pages) {
    $path = Join-Path 'C:\Users\qiaoshan\.openclaw\workspace\weddingai' $rel
    $content = Get-Content $path -Raw
    $title = (Select-String -InputObject $content -Pattern '<title>(.*?)</title>').Matches[0].Groups[1].Value
    $h1Matches = Select-String -InputObject $content -Pattern '<h1[^>]*>(.*?)</h1>' -AllMatches
    $h1 = ($h1Matches.Matches | ForEach-Object { $_.Groups[1].Value -replace '<[^>]+>', '' }) -join ' | '
    Write-Host "--- $rel ---"
    Write-Host "  title: $title"
    Write-Host "  h1:    $h1"
}
