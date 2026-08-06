$tmp = "C:\Users\qiaoshan\AppData\Local\Temp\verify-index.html"
curl.exe -sL --max-redirs 3 "https://weddingai-video.pages.dev/" -o $tmp 2>&1
$len = (Get-Item $tmp).Length
Write-Host "Downloaded: $len bytes"
if ($len -gt 100) {
    $hasSearch = Select-String -Path $tmp -Pattern '"@type":\s*"SearchAction"' -SimpleMatch
    $hasMarker = Select-String -Path $tmp -Pattern '_removed_SearchAction' -SimpleMatch
    Write-Host "Has SearchAction: $($hasSearch.Count) match(es)"
    Write-Host "Has _removed_SearchAction marker: $($hasMarker.Count) match(es)"
    if ($hasSearch.Count -eq 0 -and $hasMarker.Count -gt 0) {
        Write-Host "OK: SearchAction removed, marker in place"
    }
} else {
    Write-Host "Failed to download (likely 308 issue, not related to SearchAction)"
}
