# Fix ALL remaining trailing-slash service links across all HTML files
# Pattern: href="/services/category/service/" -> href="/services/category/service.html"

$root = "C:\Users\qiaoshan\.openclaw\workspace\weddingai"

$htmlFiles = Get-ChildItem $root -Recurse -Include "*.html"

$replacements = @{
    "/services/video-enhancement/dv-repair/" = "/services/video-enhancement/dv-repair.html"
    "/services/video-enhancement/film-digitization/" = "/services/video-enhancement/film-digitization.html"
    "/services/video-enhancement/slow-motion/" = "/services/video-enhancement/slow-motion.html"
    "/services/absence-compensation/family-tribute/" = "/services/absence-compensation/family-tribute.html"
    "/services/absence-compensation/family-message/" = "/services/absence-compensation/family-message.html"
    "/services/absence-compensation/celebrity-message/" = "/services/absence-compensation/celebrity-message.html"
    "/services/personalization/ai-video-generator/" = "/services/personalization/ai-video-generator.html"
    "/services/personalization/wedding-trailer/" = "/services/personalization/wedding-trailer.html"
    "/services/personalization/pet-wedding/" = "/services/personalization/pet-wedding.html"
    "/services/personalization/multilingual/" = "/services/personalization/multilingual.html"
    "/services/personalization/cartoon-style/" = "/services/personalization/cartoon-style.html"
    "/services/personalization/meme-generator/" = "/services/personalization/meme-generator.html"
    "/services/personalization/wedding-invitation/" = "/services/personalization/wedding-invitation.html"
    "/services/venue/interactive-screen/" = "/services/venue/interactive-screen.html"
    "/services/venue/real-time-cut/" = "/services/venue/real-time-cut.html"
    "/services/venue/live-comments/" = "/services/venue/live-comments.html"
    "/services/" = "/services/"
}

foreach ($file in $htmlFiles) {
    $content = Get-Content $file.FullName -Raw
    $original = $content
    $changed = $false

    foreach ($item in $replacements.GetEnumerator()) {
        if ($content -match [regex]::Escape($item.Key)) {
            $content = $content -replace [regex]::Escape($item.Key), $item.Value
            $changed = $true
        }
    }

    if ($changed) {
        Set-Content $file.FullName $content -NoNewline
        Write-Host "Fixed: $($file.Name)"
    }
}

Write-Host "Done."
