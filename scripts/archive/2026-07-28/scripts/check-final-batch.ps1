$images = @(
    'catalog-slow-motion.jpg','catalog-family-tribute.jpg','catalog-family-message.jpg','catalog-celebrity-message.jpg',
    'catalog-ai-video-generator.jpg','catalog-wedding-trailer.jpg','catalog-pet-wedding.jpg','catalog-multilingual.jpg',
    'catalog-cartoon-style.jpg','catalog-meme-generator.jpg',
    'petwedding-step1-upload.jpg','petwedding-step2-ai.jpg','petwedding-step3-review.jpg','petwedding-step4-delivery.jpg',
    'familymsg-step1-record.jpg','familymsg-step2-embed.jpg','familymsg-step3-delivery.jpg',
    'trailer-feat-color.jpg','trailer-feat-music.jpg','trailer-feat-transitions.jpg','trailer-feat-formats.jpg',
    'trailer-feat-text.jpg','trailer-feat-revision.jpg'
)
$ok = 0; $fail = 0
foreach ($f in $images) {
    try {
        $r = Invoke-WebRequest -Uri "https://weddingai-video.pages.dev/images/$f" -UseBasicParsing -Method Head -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $ok++ } else { $fail++; Write-Host "FAIL $f`: $($r.StatusCode)" }
    } catch { $fail++; Write-Host "FAIL $f`: $($_.Exception.Message)" }
}
Write-Host "Total: $ok OK, $fail fail (out of $($images.Count))"
