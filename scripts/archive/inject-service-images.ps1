# ============================================================
# Service page image injection script
# Maps AI images to service detail page HTML placeholders
# ============================================================

$root = "C:\Users\qiaoshan\.openclaw\workspace\weddingai"

function Inject-Image($file, $searchPattern, $imgSrc, $imgAlt) {
    $path = "$root\$file"
    $content = Get-Content $path -Raw
    if ($content -match [regex]::Escape($searchPattern)) {
        $newImg = "<img src=""$imgSrc"" alt=""$imgAlt"" loading=""lazy"">"
        $content = $content -replace [regex]::Escape($searchPattern), $newImg
        Set-Content $path $content -NoNewline
        Write-Host "OK: $file -> $imgSrc"
    } else {
        Write-Host "MISS: $file (pattern not found): $searchPattern"
    }
}

# ============================================================
# dv-repair.html — has page-hero-bg and split-comparison
# ============================================================
$dv = Get-Content "$root\services\video-enhancement\dv-repair.html" -Raw
$dv = $dv -replace '<div class="page-hero-bg" role="img" aria-label="Before and after wedding video restoration"></div>', '<div class="page-hero-bg" role="img" aria-label="Before and after wedding video restoration"><img src="images/dv-repair-vhs-tv.png" alt="VHS to HD restoration comparison" style="width:100%;height:100%;object-fit:cover;"></div>'
$dv = $dv -replace '<div class="split-half before">\s*<span class="split-label">❌ Before — Damaged VHS</span>', '<div class="split-half before"><img src="images/dv-repair-before-after.png" alt="Damaged VHS wedding video" style="width:100%;height:100%;object-fit:cover;"><span class="split-label">❌ Before — Damaged VHS</span>'
Set-Content "$root\services\video-enhancement\dv-repair.html" $dv -NoNewline
Write-Host "OK: dv-repair.html"

# ============================================================
# film-digitization.html — page-hero-bg
# ============================================================
$film = Get-Content "$root\services\video-enhancement\film-digitization.html" -Raw
$film = $film -replace '<div class="page-hero-bg" role="img" aria-label="8mm film digitization"></div>', '<div class="page-hero-bg" role="img" aria-label="8mm film digitization"><img src="images/film-digitization-projector.png" alt="8mm film to digital conversion" style="width:100%;height:100%;object-fit:cover;"></div>'
Set-Content "$root\services\video-enhancement\film-digitization.html" $film -NoNewline
Write-Host "OK: film-digitization.html"

# ============================================================
# slow-motion.html — page-hero-bg
# ============================================================
$slow = Get-Content "$root\services\video-enhancement\slow-motion.html" -Raw
$slow = $slow -replace '<div class="page-hero-bg" role="img" aria-label="AI slow motion wedding video"></div>', '<div class="page-hero-bg" role="img" aria-label="AI slow motion wedding video"><img src="images/slow-motion-first-dance.png" alt="Slow motion first dance" style="width:100%;height:100%;object-fit:cover;"></div>'
Set-Content "$root\services\video-enhancement\slow-motion.html" $slow -NoNewline
Write-Host "OK: slow-motion.html"

# ============================================================
# family-tribute.html — page-hero-bg
# ============================================================
$fam = Get-Content "$root\services\absence-compensation\family-tribute.html" -Raw
$fam = $fam -replace '<div class="page-hero-bg" role="img" aria-label="Family tribute in wedding video"></div>', '<div class="page-hero-bg" role="img" aria-label="Family tribute in wedding video"><img src="images/family-tribute-hologram.png" alt="Hologram tribute in wedding video" style="width:100%;height:100%;object-fit:cover;"></div>'
Set-Content "$root\services\absence-compensation\family-tribute.html" $fam -NoNewline
Write-Host "OK: family-tribute.html"

# ============================================================
# family-message.html — page-hero-bg
# ============================================================
$famMsg = Get-Content "$root\services\absence-compensation\family-message.html" -Raw
$famMsg = $famMsg -replace '<div class="page-hero-bg" role="img" aria-label="Remote family wedding video message"></div>', '<div class="page-hero-bg" role="img" aria-label="Remote family wedding video message"><img src="images/family-message-videocall.png" alt="Remote family video call integration" style="width:100%;height:100%;object-fit:cover;"></div>'
Set-Content "$root\services\absence-compensation\family-message.html" $famMsg -NoNewline
Write-Host "OK: family-message.html"

# ============================================================
# celebrity-message.html — page-hero-bg
# ============================================================
$cel = Get-Content "$root\services\absence-compensation\celebrity-message.html" -Raw
$cel = $cel -replace '<div class="page-hero-bg" role="img" aria-label="Celebrity wedding message"></div>', '<div class="page-hero-bg" role="img" aria-label="Celebrity wedding message"><img src="images/celebrity-message-screen.png" alt="Celebrity wedding greeting on screen" style="width:100%;height:100%;object-fit:cover;"></div>'
Set-Content "$root\services\absence-compensation\celebrity-message.html" $cel -NoNewline
Write-Host "OK: celebrity-message.html"

# ============================================================
# ai-video-generator.html — page-hero-bg
# ============================================================
$ai = Get-Content "$root\services\personalization\ai-video-generator.html" -Raw
$ai = $ai -replace '<div class="page-hero-bg" role="img" aria-label="AI wedding video generator"></div>', '<div class="page-hero-bg" role="img" aria-label="AI wedding video generator"><img src="images/ai-video-generator-workspace.png" alt="AI wedding video generator workspace" style="width:100%;height:100%;object-fit:cover;"></div>'
Set-Content "$root\services\personalization\ai-video-generator.html" $ai -NoNewline
Write-Host "OK: ai-video-generator.html"

# ============================================================
# wedding-trailer.html — page-hero-bg
# ============================================================
$trailer = Get-Content "$root\services\personalization\wedding-trailer.html" -Raw
$trailer = $trailer -replace '<div class="page-hero-bg" role="img" aria-label="Cinematic wedding trailer"></div>', '<div class="page-hero-bg" role="img" aria-label="Cinematic wedding trailer"><img src="images/wedding-trailer-sunset.png" alt="Cinematic wedding trailer sunset" style="width:100%;height:100%;object-fit:cover;"></div>'
Set-Content "$root\services\personalization\wedding-trailer.html" $trailer -NoNewline
Write-Host "OK: wedding-trailer.html"

# ============================================================
# pet-wedding.html — page-hero-bg
# ============================================================
$pet = Get-Content "$root\services\personalization\pet-wedding.html" -Raw
$pet = $pet -replace '<div class="page-hero-bg" role="img" aria-label="Pet wedding video"></div>', '<div class="page-hero-bg" role="img" aria-label="Pet wedding video"><img src="images/pet-wedding-golden-retrievers.png" alt="Pet wedding video golden retrievers" style="width:100%;height:100%;object-fit:cover;"></div>'
Set-Content "$root\services\personalization\pet-wedding.html" $pet -NoNewline
Write-Host "OK: pet-wedding.html"

# ============================================================
# cartoon-style.html — page-hero-bg
# ============================================================
$cartoon = Get-Content "$root\services\personalization\cartoon-style.html" -Raw
$cartoon = $cartoon -replace '<div class="page-hero-bg" role="img" aria-label="Animated cartoon wedding video"></div>', '<div class="page-hero-bg" role="img" aria-label="Animated cartoon wedding video"><img src="images/cartoon-ghibli-style.png" alt="Ghibli style animated wedding" style="width:100%;height:100%;object-fit:cover;"></div>'
Set-Content "$root\services\personalization\cartoon-style.html" $cartoon -NoNewline
Write-Host "OK: cartoon-style.html"

# ============================================================
# wedding-invitation.html — page-hero-bg
# ============================================================
$invite = Get-Content "$root\services\personalization\wedding-invitation.html" -Raw
$invite = $invite -replace '<div class="page-hero-bg" role="img" aria-label="Animated wedding invitation"></div>', '<div class="page-hero-bg" role="img" aria-label="Animated wedding invitation"><img src="images/wedding-invitation-phone.png" alt="Animated wedding invitation on phone" style="width:100%;height:100%;object-fit:cover;"></div>'
Set-Content "$root\services\personalization\wedding-invitation.html" $invite -NoNewline
Write-Host "OK: wedding-invitation.html"

# ============================================================
# interactive-screen.html — page-hero-bg
# ============================================================
$screen = Get-Content "$root\services\venue\interactive-screen.html" -Raw
$screen = $screen -replace '<div class="page-hero-bg" role="img" aria-label="Interactive wedding photo screen"></div>', '<div class="page-hero-bg" role="img" aria-label="Interactive wedding photo screen"><img src="images/interactive-screen-mosaic.png" alt="Interactive LED photo mosaic screen" style="width:100%;height:100%;object-fit:cover;"></div>'
Set-Content "$root\services\venue\interactive-screen.html" $screen -NoNewline
Write-Host "OK: interactive-screen.html"

# ============================================================
# real-time-cut.html — page-hero-bg
# ============================================================
$realtime = Get-Content "$root\services\venue\real-time-cut.html" -Raw
$realtime = $realtime -replace '<div class="page-hero-bg" role="img" aria-label="Same-day wedding video editing"></div>', '<div class="page-hero-bg" role="img" aria-label="Same-day wedding video editing"><img src="images/realtime-cut-editor.png" alt="Same-day wedding video editing" style="width:100%;height:100%;object-fit:cover;"></div>'
Set-Content "$root\services\venue\real-time-cut.html" $realtime -NoNewline
Write-Host "OK: real-time-cut.html"

# ============================================================
# live-comments.html — page-hero-bg
# ============================================================
$live = Get-Content "$root\services\venue\live-comments.html" -Raw
$live = $live -replace '<div class="page-hero-bg" role="img" aria-label="Live comment stream at wedding"></div>', '<div class="page-hero-bg" role="img" aria-label="Live comment stream at wedding"><img src="images/live-comments-screen.png" alt="Live comment stream on wedding screen" style="width:100%;height:100%;object-fit:cover;"></div>'
Set-Content "$root\services\venue\live-comments.html" $live -NoNewline
Write-Host "OK: live-comments.html"

# ============================================================
# meme-generator.html — page-hero-bg
# ============================================================
$meme = Get-Content "$root\services\personalization\meme-generator.html" -Raw
$meme = $meme -replace '<div class="page-hero-bg" role="img" aria-label="Wedding GIF and meme generator"></div>', '<div class="page-hero-bg" role="img" aria-label="Wedding GIF and meme generator"><img src="images/meme-generator-gif-collage.png" alt="Wedding GIF and meme collage" style="width:100%;height:100%;object-fit:cover;"></div>'
Set-Content "$root\services\personalization\meme-generator.html" $meme -NoNewline
Write-Host "OK: meme-generator.html"

# ============================================================
# multilingual.html — page-hero-bg
# ============================================================
$multi = Get-Content "$root\services\personalization\multilingual.html" -Raw
$multi = $multi -replace '<div class="page-hero-bg" role="img" aria-label="Multilingual wedding video"></div>', '<div class="page-hero-bg" role="img" aria-label="Multilingual wedding video"><img src="images/multilingual-split-screen.png" alt="Wedding video with multilingual subtitles" style="width:100%;height:100%;object-fit:cover;"></div>'
Set-Content "$root\services\personalization\multilingual.html" $multi -NoNewline
Write-Host "OK: multilingual.html"

Write-Host "`nAll service pages updated."
