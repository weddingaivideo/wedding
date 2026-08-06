# Check all new images are accessible
$images = @(
    'pet-wedding-ceremony.jpg','pet-save-the-date.jpg','pet-anniversary.jpg','pet-proposal.jpg',
    'cartoon-ghibli.jpg','cartoon-pixar.jpg','cartoon-anime.jpg','cartoon-watercolor.jpg','cartoon-pencil.jpg','cartoon-comic.jpg',
    'meme-i-do-reaction.jpg','meme-champagne-toast.jpg','meme-ring-exchange.jpg','meme-bride-entrance.jpg',
    'meme-cake-cutting.jpg','meme-first-dance.jpg','meme-best-man-speech.jpg','meme-reception-party.jpg'
)
$ok = 0; $fail = 0
foreach ($f in $images) {
    try {
        $r = Invoke-WebRequest -Uri "https://weddingai-video.pages.dev/images/$f" -UseBasicParsing -Method Head -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $ok++ } else { $fail++; Write-Host "FAIL $f`: $($r.StatusCode)" }
    } catch { $fail++; Write-Host "FAIL $f`: $($_.Exception.Message)" }
}
Write-Host ""
Write-Host "Total: $ok OK, $fail fail"
