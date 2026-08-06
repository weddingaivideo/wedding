if ($env:WEDDINGAI_ROOT) { $root = $env:WEDDINGAI_ROOT }
else { $root = Split-Path -Parent $PSScriptRoot }
# ── index.html ──────────────────────────────────────────────────────────────
$index = Get-Content "$root\index.html" -Raw

$index = $index -replace '<span class="img-placeholder">📹 Video Enhancement</span>', '<img src="images/hero-wedding-vineyard.png" alt="Video Enhancement service" loading="lazy">'
$index = $index -replace '<span class="img-placeholder">💛 Absence Compensation</span>', '<img src="images/family-tribute-hologram.png" alt="Absence Compensation service" loading="lazy">'
$index = $index -replace '<span class="img-placeholder">✨ Personalization</span>', '<img src="images/cartoon-ghibli-style.png" alt="Personalization service" loading="lazy">'
$index = $index -replace '<span class="img-placeholder">🎉 Venue Experience</span>', '<img src="images/interactive-screen-mosaic.png" alt="Venue Experience service" loading="lazy">'
$index = $index -replace '<span class="img-placeholder">📼 1987 Restoration</span>', '<img src="images/wedding-restoration-before-after.png" alt="1987 wedding video restoration" loading="lazy">'
$index = $index -replace '<span class="img-placeholder">🎬 Sarah & James</span>', '<img src="images/wedding-trailer-sunset.png" alt="Sarah and James wedding trailer" loading="lazy">'
$index = $index -replace '<span class="img-placeholder">🐕 Bella & Max</span>', '<img src="images/pet-wedding-golden-retrievers.png" alt="Bella and Max pet wedding" loading="lazy">'
Set-Content "$root\index.html" $index -NoNewline
Write-Host "index.html: 7 placeholders replaced"

# ── about.html ──────────────────────────────────────────────────────────────
$about = Get-Content "$root\about.html" -Raw
$about = $about -replace '<span class="img-placeholder">👤 Founder</span>', '<img src="images/about-team-studio.png" alt="WeddingAI team" loading="lazy">'
$about = $about -replace '<span class="img-placeholder">👩💻 AI Lead</span>', '<img src="images/about-team-studio.png" alt="WeddingAI AI team" loading="lazy">'
$about = $about -replace '<span class="img-placeholder">👩💼 Client Lead</span>', '<img src="images/about-team-studio.png" alt="WeddingAI client team" loading="lazy">'
$about = $about -replace '<span class="img-placeholder">🎬 Video Editor</span>', '<img src="images/about-team-studio.png" alt="WeddingAI video editors" loading="lazy">'
Set-Content "$root\about.html" $about -NoNewline
Write-Host "about.html: 4 placeholders replaced"

# ── gallery.html ────────────────────────────────────────────────────────────
$gallery = Get-Content "$root\gallery.html" -Raw
$gallery = $gallery -replace '<span class="img-placeholder">📼 1987 Wedding — VHS Restoration</span>', '<img src="images/wedding-restoration-before-after.png" alt="1987 wedding VHS restoration case study" loading="lazy">'
$gallery = $gallery -replace '<span class="img-placeholder">🎬 Sarah & James — Cinematic Trailer</span>', '<img src="images/wedding-trailer-sunset.png" alt="Sarah and James cinematic wedding trailer" loading="lazy">'
$gallery = $gallery -replace '<span class="img-placeholder">🐕 Bella & Max — Pet Wedding</span>', '<img src="images/pet-wedding-golden-retrievers.png" alt="Bella and Max pet wedding case" loading="lazy">'
$gallery = $gallery -replace '<span class="img-placeholder">🌍 Priya & Arjun — Hindi & English</span>', '<img src="images/multilingual-split-screen.png" alt="Priya and Arjun multilingual wedding" loading="lazy">'
$gallery = $gallery -replace '<span class="img-placeholder">🎉 Mike & Rachel — Interactive Reception</span>', '<img src="images/interactive-screen-mosaic.png" alt="Mike and Rachel interactive wedding reception" loading="lazy">'
$gallery = $gallery -replace '<span class="img-placeholder">🎨 Emily & Tom — Cartoon Style</span>', '<img src="images/cartoon-ghibli-style.png" alt="Emily and Tom cartoon style wedding" loading="lazy">'
$gallery = $gallery -replace '<span class="img-placeholder">⚡ Jessica & Ryan — Same-Day Edit</span>', '<img src="images/realtime-cut-editor.png" alt="Jessica and Ryan same-day wedding edit" loading="lazy">'
Set-Content "$root\gallery.html" $gallery -NoNewline
Write-Host "gallery.html: 9 placeholders replaced"

# ── order.html ──────────────────────────────────────────────────────────────
$order = Get-Content "$root\order.html" -Raw
$order = $order -replace '<span class="img-placeholder">📋 Order Form</span>', '<img src="images/order-form-mockup.png" alt="Wedding video quote request form" loading="lazy">'
Set-Content "$root\order.html" $order -NoNewline
Write-Host "order.html: 1 placeholder replaced"

Write-Host "Core pages done."
