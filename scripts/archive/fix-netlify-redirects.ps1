$content = Get-Content "C:\Users\qiaoshan\.openclaw\workspace\weddingai\netlify.toml" -Raw

# Add redirect rules for all service detail pages (no extension -> .html)
# These handle trailing-slash redirects AND extensionless URLs

$extraRedirects = @"

# Service page redirects (extensionless URL -> .html)
[[redirects]]
  from = "/services/video-enhancement/dv-repair"
  to = "/services/video-enhancement/dv-repair.html"
  status = 301

[[redirects]]
  from = "/services/video-enhancement/film-digitization"
  to = "/services/video-enhancement/film-digitization.html"
  status = 301

[[redirects]]
  from = "/services/video-enhancement/slow-motion"
  to = "/services/video-enhancement/slow-motion.html"
  status = 301

[[redirects]]
  from = "/services/absence-compensation/family-tribute"
  to = "/services/absence-compensation/family-tribute.html"
  status = 301

[[redirects]]
  from = "/services/absence-compensation/family-message"
  to = "/services/absence-compensation/family-message.html"
  status = 301

[[redirects]]
  from = "/services/absence-compensation/celebrity-message"
  to = "/services/absence-compensation/celebrity-message.html"
  status = 301

[[redirects]]
  from = "/services/personalization/ai-video-generator"
  to = "/services/personalization/ai-video-generator.html"
  status = 301

[[redirects]]
  from = "/services/personalization/wedding-trailer"
  to = "/services/personalization/wedding-trailer.html"
  status = 301

[[redirects]]
  from = "/services/personalization/pet-wedding"
  to = "/services/personalization/pet-wedding.html"
  status = 301

[[redirects]]
  from = "/services/personalization/multilingual"
  to = "/services/personalization/multilingual.html"
  status = 301

[[redirects]]
  from = "/services/personalization/cartoon-style"
  to = "/services/personalization/cartoon-style.html"
  status = 301

[[redirects]]
  from = "/services/personalization/meme-generator"
  to = "/services/personalization/meme-generator.html"
  status = 301

[[redirects]]
  from = "/services/personalization/wedding-invitation"
  to = "/services/personalization/wedding-invitation.html"
  status = 301

[[redirects]]
  from = "/services/venue/interactive-screen"
  to = "/services/venue/interactive-screen.html"
  status = 301

[[redirects]]
  from = "/services/venue/real-time-cut"
  to = "/services/venue/real-time-cut.html"
  status = 301

[[redirects]]
  from = "/services/venue/live-comments"
  to = "/services/venue/live-comments.html"
  status = 301

[[redirects]]
  from = "/services"
  to = "/services/index.html"
  status = 301

[[redirects]]
  from = "/services/"
  to = "/services/index.html"
  status = 301
"@

# Insert before the first [[headers]] block
if ($content -match '(\n\n# SPA fallback)') {
    $content = $content -replace '(\n\n# SPA fallback)', "$extraRedirects`n`n# SPA fallback"
} else {
    # Insert before security headers
    $content = $content -replace '(\n\n# Security Headers)', "$extraRedirects`n`n# Security Headers"
}

Set-Content "C:\Users\qiaoshan\.openclaw\workspace\weddingai\netlify.toml" $content -NoNewline
Write-Host "netlify.toml updated with service page redirects."
