# 给所有HTML的title和meta description加上Google SEO友好的标点
# 规则: title/description 末尾如果没有标点(. ? ! : ; -), 加 !

$root = "C:\Users\qiaoshan\.openclaw\workspace\weddingai"
$files = Get-ChildItem -Path $root -Recurse -Filter "*.html"

# 文件特定的精确替换（针对每个页面定制）
$replacements = @{
    "index.html" = @{
        title = "<title>WeddingAI.video: AI-Powered Wedding Video Services | Enhance, Create & Customize!</title>"
        description = '<meta name="description" content="Transform your wedding memories with AI. From vintage DV repair to AI-generated wedding films, we offer 16+ wedding video services for couples worldwide. Free consultation available — get started today!">'
    }
    "about.html" = @{
        title = "<title>About WeddingAI.video: Our Story & Team — Filmmakers, AI Engineers, Wedding Enthusiasts!</title>"
        description = '<meta name="description" content="Meet the team behind WeddingAI.video. We are filmmakers, AI engineers, and wedding enthusiasts bringing AI-powered video services to couples worldwide. Get to know us!">'
    }
    "gallery.html" = @{
        title = "<title>Wedding Video Portfolio: Real Case Studies & Before/After Examples | WeddingAI.video</title>"
        description = '<meta name="description" content="See real before-and-after examples of our wedding video restoration, AI film generation, and personalization work. Browse our portfolio of 500+ projects — find inspiration for yours!">'
    }
    "order.html" = @{
        title = "<title>Get a Free Wedding Video Quote Today — Contact WeddingAI.video!</title>"
        description = '<meta name="description" content="Ready to restore or create your wedding video? Submit your request and receive a free personalized quote within 24 hours. No commitment required — start now!">'
    }
    "success.html" = @{
        title = "<title>Thank You for Your Request — WeddingAI.video!</title>"
        description = '<meta name="description" content="Your quote request has been received. We will get back to you within 24 hours — thank you for choosing WeddingAI.video!">'
    }
    "privacy.html" = @{
        title = "<title>Privacy Policy: How We Protect Your Data | WeddingAI.video</title>"
        description = '<meta name="description" content="Privacy policy for WeddingAI.video. Learn how we collect, use, and protect your personal data in compliance with GDPR and CCPA — your privacy matters!">'
    }
    "terms.html" = @{
        title = "<title>Terms of Service: Service Terms & Policies | WeddingAI.video</title>"
        description = '<meta name="description" content="Terms of service for WeddingAI.video. Read our service terms, payment policies, and customer obligations — everything you need to know!">'
    }
    "services\index.html" = @{
        title = "<title>Wedding Video Services: AI-Powered Restoration, Creation & Personalization | WeddingAI.video</title>"
        description = '<meta name="description" content="Browse all WeddingAI.video services: video restoration, AI wedding films, pet weddings, multilingual dubbing, and more. 16 services for every wedding video need — explore now!">'
    }
    "services\video-enhancement\slow-motion.html" = @{
        title = "<title>Wedding Video Slow Motion Enhancement: AI Frame Interpolation | WeddingAI.video</title>"
        description = '<meta name="description" content="Transform your wedding video with smooth, natural slow motion. Our AI frame interpolation creates buttery-smooth slow motion from standard frame rates — perfect for your first dance and vow exchange!">'
    }
    "services\personalization\ai-video-generator.html" = @{
        title = "<title>AI Wedding Video Generator: Create Wedding Films from Photos & Text | WeddingAI.video</title>"
        description = '<meta name="description" content="Upload your photos and describe your dream wedding video. Our AI generates a cinematic wedding film automatically. No editing skills needed — perfect for couples, photographers, and planners!">'
    }
    "services\personalization\wedding-trailer.html" = @{
        title = "<title>AI Wedding Trailer: Cinematic Wedding Teaser in 48 Hours | WeddingAI.video</title>"
        description = '<meta name="description" content="Want to share a sneak peek of your wedding? We create stunning cinematic trailers from your wedding footage — perfect for Instagram, TikTok, and sharing with guests before the full film!">'
    }
    "services\personalization\pet-wedding.html" = @{
        title = "<title>Pet Wedding Video: AI-Generated Wedding Films for Your Furry Friends | WeddingAI.video</title>"
        description = '<meta name="description" content="Your pet is family too. Let us create a hilarious and heartwarming wedding video starring your dog, cat, or any pet — perfect for anniversary celebrations, proposals, or just because!">'
    }
    "services\personalization\multilingual.html" = @{
        title = "<title>Multilingual Wedding Video: AI Dubbing & Subtitles in 20+ Languages | WeddingAI.video</title>"
        description = '<meta name="description" content="Share your wedding video with family around the world. We add professional AI voiceovers and subtitles in 20+ languages — English, Spanish, Hindi, Mandarin, Arabic, and more!">'
    }
    "services\personalization\cartoon-style.html" = @{
        title = "<title>Animated Wedding Video: Cartoon Style (Ghibli, Pixar, Anime) | WeddingAI.video</title>"
        description = '<meta name="description" content="Transform your wedding footage into a beautiful animation. Choose from Ghibli, Pixar, anime, or watercolor cartoon styles — perfect for sharing on social media!">'
    }
    "services\personalization\meme-generator.html" = @{
        title = "<title>Wedding GIFs & Memes: Share the Joy | WeddingAI.video</title>"
        description = '<meta name="description" content="Get custom wedding GIFs, memes, and shareable clips — perfect for social media, group chats, and thank-you messages to guests!">'
    }
    "services\absence-compensation\family-tribute.html" = @{
        title = "<title>Honor a Deceased Loved One in Your Wedding Video | WeddingAI.video</title>"
        description = '<meta name="description" content="Keep your loved ones present on your wedding day. We respectfully create tributes using photos and voice recordings to include deceased family members in your wedding video!">'
    }
    "services\absence-compensation\family-message.html" = @{
        title = "<title>Remote Family Wedding Message Integration: Seamlessly Embedded | WeddingAI.video</title>"
        description = '<meta name="description" content="Family could not make it to your wedding? We will film their message separately and seamlessly integrate it into your wedding video — so they feel part of your special day!">'
    }
    "services\absence-compensation\celebrity-message.html" = @{
        title = "<title>Celebrity Wedding Messages: Personalized AI-Generated Greetings | WeddingAI.video</title>"
        description = '<meta name="description" content="Want a celebrity message for your wedding? Our AI creates personalized, realistic wedding greetings in a celebrity aesthetic — perfect for milestone celebrations!">'
    }
}

foreach ($file in $files) {
    $rel = $file.FullName.Substring($root.Length + 1) -replace '\\', '/'
    $relWin = $file.FullName.Substring($root.Length + 1)
    if ($replacements.ContainsKey($relWin)) {
        $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
        $original = $content
        $rep = $replacements[$relWin]

        # 替换 title - 用正则匹配现有的 <title>...</title>
        $content = [regex]::Replace($content, '(?s)<title>.*?</title>', $rep.title)
        # 替换 description
        $content = [regex]::Replace($content, '(?s)<meta name="description"\s+content="[^"]*">', $rep.description)

        if ($content -ne $original) {
            $content | Set-Content -Path $file.FullName -NoNewline -Encoding UTF8
            Write-Host "Updated: $($file.Name)"
        }
    }
}
Write-Host "Done."
