# Fix remaining hero-bg images — some pages had different aria-labels
# This script replaces ANY <div class="page-hero-bg" ...></div> that is empty

$root = "C:\Users\qiaoshan\.openclaw\workspace\weddingai\services"

$replacements = @{
    "personalization\pet-wedding.html" = "images/pet-wedding-golden-retrievers.png|Pet wedding scene with golden retrievers"
    "personalization\ai-video-generator.html" = "images/ai-video-generator-workspace.png|AI wedding video generator"
    "personalization\cartoon-style.html" = "images/cartoon-ghibli-style.png|Animated cartoon wedding video"
    "personalization\wedding-invitation.html" = "images/wedding-invitation-phone.png|Animated wedding invitation"
    "venue\interactive-screen.html" = "images/interactive-screen-mosaic.png|Interactive wedding photo screen"
    "venue\real-time-cut.html" = "images/realtime-cut-editor.png|Same-day wedding video editing"
    "venue\live-comments.html" = "images/live-comments-screen.png|Live comment stream at wedding"
    "video-enhancement\film-digitization.html" = "images/film-digitization-projector.png|8mm film digitization"
    "video-enhancement\slow-motion.html" = "images/slow-motion-first-dance.png|AI slow motion wedding video"
    "absence-compensation\family-message.html" = "images/family-message-videocall.png|Remote family wedding video message"
}

foreach ($item in $replacements.GetEnumerator()) {
    $file = $item.Key
    $parts = $item.Value -split '\|'
    $imgSrc = $parts[0]
    $ariaText = $parts[1]

    $path = "$root\$file"
    $content = Get-Content $path -Raw

    # Pattern: <div class="page-hero-bg" role="img" aria-label="..."></div>
    # Replace with img inside
    $pattern = '(<div class="page-hero-bg"[^>]*>)\s*(</div>)'
    $replacement = "`$1<img src=""$imgSrc"" alt=""$ariaText"" style=""width:100%;height:100%;object-fit:cover;"">`$2"

    if ($content -match $pattern) {
        $content = $content -replace $pattern, $replacement
        Set-Content $path $content -NoNewline
        Write-Host "OK: $file"
    } else {
        # Try without aria-label variation
        $simplePattern = '<div class="page-hero-bg"[^>]*></div>'
        if ($content -match $simplePattern) {
            $simpleReplacement = "<div class=""page-hero-bg""><img src=""$imgSrc"" alt=""$ariaText"" style=""width:100%;height:100%;object-fit:cover;""></div>"
            $content = $content -replace $simplePattern, $simpleReplacement
            Set-Content $path $content -NoNewline
            Write-Host "OK (simple): $file"
        } else {
            Write-Host "MISS: $file (pattern not found)"
        }
    }
}

Write-Host "Done."
