$src = "C:\Users\qiaoshan\.openclaw\media\tool-image-generation\"
if ($env:WEDDINGAI_ROOT) { $root = Join-Path $env:WEDDINGAI_ROOT "images" }
else { $root = Join-Path (Split-Path -Parent $PSScriptRoot) "images" }
$mapping = @{
    "hero-wedding-vineyard---1f105497-bbda-4274-80df-dccda519636c.png" = "hero-wedding-vineyard.png"
    "dv-repair-before-after---4be9f690-5d94-4b49-8da1-67a0837e6810.png" = "wedding-restoration-before-after.png"
    "family-tribute-hologram---530c1cee-9d7b-4936-8770-2f9508cb9cb8.png" = "family-tribute-hologram.png"
    "family-tribute-frame---aebb37e6-bf69-4401-8faa-9287bb849082.png" = "family-tribute-frame.png"
    "gallery-collage---3e459d24-978b-433c-bf6c-fba5c4faa891.png" = "gallery-collage.png"
    "dv-repair-vhs-tv---9f4f65b3-544e-402c-89a5-76e165ccb8ef.png" = "wedding-restoration-vhs-tv.png"
    "slow-motion-first-dance---4c9ed81e-2561-4fbf-8bd9-bb4d53a6c8a8.png" = "slow-motion-first-dance.png"
    "ai-video-generator-workspace---98d20282-be60-4194-b02c-2a3f7b64b88f.png" = "ai-video-generator-workspace.png"
    "wedding-trailer-sunset---f9ad3b28-6109-475d-b071-bfe6728533be.png" = "wedding-trailer-sunset.png"
    "pet-wedding-golden-retrievers---42417fd2-1b3f-4db5-90b8-baaa1c729054.png" = "pet-wedding-golden-retrievers.png"
    "cartoon-ghibli-style---d05223e6-1d1f-4873-b8c6-6a775afa1804.png" = "cartoon-ghibli-style.png"
    "interactive-screen-mosaic---54853f1b-cca3-46a2-9664-780f64e1be31.png" = "interactive-screen-mosaic.png"
    "realtime-cut-editor---eb0d577b-fe67-4396-a8b0-4c4df76005f2.png" = "realtime-cut-editor.png"
    "live-comments-screen---61cb0690-c478-4ff0-9b36-cb27f7670428.png" = "live-comments-screen.png"
    "family-message-videocall---9e4f7d11-6e2a-4c33-bfe7-4049afdc39ad.png" = "family-message-videocall.png"
    "meme-generator-gif-collage---13fd3336-c131-4c81-ab67-59f2b067dcca.png" = "meme-generator-gif-collage.png"
    "multilingual-split-screen---197dbb90-9884-4f44-b1c3-524c3b05e610.png" = "multilingual-split-screen.png"
    "celebrity-message-screen---556aea90-41cb-43b5-b60d-605741519592.png" = "celebrity-message-screen.png"
    "pricing-cards---2add94b3-43e7-4923-a877-6d2a4d7ef41b.png" = "pricing-cards.png"
    "order-form-mockup---9670c62e-18cd-453e-af9d-249a8100dd55.png" = "order-form-mockup.png"
    "about-team-studio---f7407d4a-20cb-438e-9510-6fe3bd93737d.png" = "about-team-studio.png"
    "cartoon-realistic-combo---9fcf208a-d291-4c83-822b-a61831f4f845.png" = "cartoon-realistic-combo.png"
}

foreach ($item in $mapping.GetEnumerator()) {
    $srcPath = $src + $item.Key
    $dstPath = $dst + $item.Value
    if (Test-Path $srcPath) {
        Copy-Item $srcPath $dstPath -Force
        Write-Host "OK: $($item.Value)"
    } else {
        Write-Host "MISSING: $($item.Key)"
    }
}
Write-Host "Done."
