# Fix 16 <h3>...</h4> typos in 8 service pages (the related-card block).
#
# Context: 2026-08-04 user reported "Pair It With..." is mangled on non-EN
# service pages. Root cause: opening <h3> tag has a closing </h4> in the
# source HTML. The i18n regex /<(\w+)...<\/1>/ skips mismatched pairs, so the
# EN title leaks through. The next data-i18n match (the <p> card1_desc) uses
# a non-greedy quantifier that gobbles content up to the next </h3> (in the
# footer) — replacing card2 / card1_desc / section-close with a single
# translated string. End result: one mangled card with German title, no
# description, second card gone.
#
# Fix: the OPENING tag is already correct (h3). Just close it correctly
# (</h3> instead of </h4>). The data-i18n KEY name h4_text is harmless
# (it's just a dict key; the i18n lookup doesn't care what number it is), so
# we leave the key names alone to minimize churn.
#
# Idempotent: re-running on already-fixed files is a no-op (the source no
# longer contains </h4>).

if ($env:WEDDINGAI_ROOT) { $root = $env:WEDDINGAI_ROOT }
else { $root = Split-Path -Parent $PSScriptRoot }
$fixes = @(
    # (file, from, to)
    # 1) celebrity-message — card1
    @{ Path = "$root\services\absence-compensation\celebrity-message\index.html"
      From = 'data-i18n="services.absence-compensation.celebrity-message.h4_text.card1_title.b8c9d0e1">Remote Family Video Message</h4>'
      To   = 'data-i18n="services.absence-compensation.celebrity-message.h4_text.card1_title.b8c9d0e1">Remote Family Video Message</h3>' }
    # 2) celebrity-message — card2
    @{ Path = "$root\services\absence-compensation\celebrity-message\index.html"
      From = 'data-i18n="services.absence-compensation.celebrity-message.h4_text.card2_title.b8c9d0e1">Pet Wedding Video</h4>'
      To   = 'data-i18n="services.absence-compensation.celebrity-message.h4_text.card2_title.b8c9d0e1">Pet Wedding Video</h3>' }
    # 3) family-message — card1
    @{ Path = "$root\services\absence-compensation\family-message\index.html"
      From = 'data-i18n="services.absence-compensation.family-message.h4_text.card1_title.a7b8c9d0">Tribute to Loved Ones</h4>'
      To   = 'data-i18n="services.absence-compensation.family-message.h4_text.card1_title.a7b8c9d0">Tribute to Loved Ones</h3>' }
    # 4) family-message — card2
    @{ Path = "$root\services\absence-compensation\family-message\index.html"
      From = 'data-i18n="services.absence-compensation.family-message.h4_text.card2_title.a7b8c9d0">Multilingual Wedding Video</h4>'
      To   = 'data-i18n="services.absence-compensation.family-message.h4_text.card2_title.a7b8c9d0">Multilingual Wedding Video</h3>' }
    # 5) ai-video-generator — card1
    @{ Path = "$root\services\personalization\ai-video-generator\index.html"
      From = 'data-i18n="services.personalization.ai-video-generator.h4_text.card1_title.a1b2c3d4">Cinematic Wedding Trailer</h4>'
      To   = 'data-i18n="services.personalization.ai-video-generator.h4_text.card1_title.a1b2c3d4">Cinematic Wedding Trailer</h3>' }
    # 6) ai-video-generator — card2
    @{ Path = "$root\services\personalization\ai-video-generator\index.html"
      From = 'data-i18n="services.personalization.ai-video-generator.h4_text.card2_title.a1b2c3d4">Wedding GIFs &amp; Memes</h4>'
      To   = 'data-i18n="services.personalization.ai-video-generator.h4_text.card2_title.a1b2c3d4">Wedding GIFs &amp; Memes</h3>' }
    # 7) cartoon-style — card1
    @{ Path = "$root\services\personalization\cartoon-style\index.html"
      From = 'data-i18n="services.personalization.cartoon-style.h4_text.card1_title.d4e5f6a7">AI Wedding Video Generator</h4>'
      To   = 'data-i18n="services.personalization.cartoon-style.h4_text.card1_title.d4e5f6a7">AI Wedding Video Generator</h3>' }
    # 8) cartoon-style — card2
    @{ Path = "$root\services\personalization\cartoon-style\index.html"
      From = 'data-i{
    BUG: this line is truncated. Look at actual source for exact text.
    @{ Path = "$root\services\personalization\meme-generator\index.html"
      From = 'data-i18n="services.personalization.meme-generator.h4_text.card1_title.e5f6a7b8">Pet Wedding Video</h4>'
      To   = 'data-i18n="services.personalization.meme-generator.h4_text.card1_title.e5f6a7b8">Pet Wedding Video</h3>' }
    @{ Path = "$root\services\personalization\meme-generator\index.html"
      From = 'data-i18n="services.personalization.meme-generator.h4_text.card2_title.e5f6a7b8">Cinematic Wedding Trailer</h4>'
      To   = 'data-i18َ
  Path = "C:\Users\qiaoshan\.openclaw\workspace\weddingai\qa\fix-related-card-h4-typo.ps1"
