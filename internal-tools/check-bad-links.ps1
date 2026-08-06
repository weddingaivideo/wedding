Get-ChildItem "C:\Users\qiaoshan\.openclaw\workspace\weddingai" -Recurse -Include "*.html" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    $badLinks = [regex]::Matches($content, 'href="([^"# ]*)/"') | Where-Object {
        $_.Groups[1].Value -notmatch '\.(css|js|png|jpg|svg|woff|ico)' -and
        $_.Groups[1].Value -notmatch '^https?://' -and
        $_.Groups[1].Value -notmatch '^#'
    } | ForEach-Object { $_.Groups[1].Value } | Select-Object -Unique
    if ($badLinks) {
        Write-Host "$($_.Name):"
        $badLinks | ForEach-Object { Write-Host "  $_" }
    }
}
Write-Host "Check complete."
