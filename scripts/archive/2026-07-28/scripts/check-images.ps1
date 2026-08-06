# Check if preset images are accessible
$images = @('preset-cinematic.jpg','preset-romantic-soft.jpg','preset-modern-minimal.jpg','preset-vintage-retro.jpg','preset-destination-beach.jpg','preset-destination-vineyard.jpg')
foreach ($f in $images) {
    try {
        $r = Invoke-WebRequest -Uri "https://weddingai-video.pages.dev/images/$f" -UseBasicParsing -Method Head -ErrorAction Stop
        Write-Host "$f`: $($r.StatusCode) ($($r.Headers['Content-Length'] -join ',') bytes)"
    } catch {
        Write-Host "$f`: ERROR - $($_.Exception.Message)"
    }
}
