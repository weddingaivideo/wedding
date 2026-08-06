$images = @('tribute-photo-activation.jpg','tribute-voice-reconstruction.jpg','tribute-memorial-montage.jpg','trailer-standard.jpg','trailer-premium.jpg','trailer-social.jpg')
$ok = 0; $fail = 0
foreach ($f in $images) {
    try {
        $r = Invoke-WebRequest -Uri "https://weddingai-video.pages.dev/images/$f" -UseBasicParsing -Method Head -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $ok++ } else { $fail++; Write-Host "FAIL $f`: $($r.StatusCode)" }
    } catch { $fail++; Write-Host "FAIL $f`: $($_.Exception.Message)" }
}
Write-Host "Total: $ok OK, $fail fail"
