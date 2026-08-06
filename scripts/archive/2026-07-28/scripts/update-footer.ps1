# 更新所有HTML文件的footer:
# 1. 删除 Venue Experiences 引用
# 2. 扩展 Services 列表为完整服务
# 3. 缩小 footer logo height 到 7 (原 28 的 1/4)

$root = "C:\Users\qiaoshan\.openclaw\workspace\weddingai"
$files = Get-ChildItem -Path $root -Recurse -Filter "*.html"

# 完整服务列表（根级链接，从任意页面都可以访问）
$fullServices = @'
                    <div class="footer-col">
                        <h4>Services</h4>
                        <ul>
                            <li><a href="/services/video-enhancement/slow-motion.html">Slow Motion Enhancement</a></li>
                            <li><a href="/services/absence-compensation/family-tribute.html">Family Tribute</a></li>
                            <li><a href="/services/absence-compensation/family-message.html">Family Message</a></li>
                            <li><a href="/services/absence-compensation/celebrity-message.html">Celebrity Message</a></li>
                            <li><a href="/services/personalization/ai-video-generator.html">AI Video Generator</a></li>
                            <li><a href="/services/personalization/wedding-trailer.html">Wedding Trailer</a></li>
                            <li><a href="/services/personalization/pet-wedding.html">Pet Wedding</a></li>
                            <li><a href="/services/personalization/multilingual.html">Multilingual Dubbing</a></li>
                            <li><a href="/services/personalization/cartoon-style.html">Cartoon Style</a></li>
                            <li><a href="/services/personalization/meme-generator.html">Wedding Memes &amp; GIFs</a></li>
                        </ul>
                    </div>
'@

# 简化服务列表（子页面用）
$subServices = @'
                    <div class="footer-col">
                        <h4>Services</h4>
                        <ul>
                            <li><a href="/services/video-enhancement/slow-motion.html">Slow Motion Enhancement</a></li>
                            <li><a href="/services/absence-compensation/family-tribute.html">Family Tribute</a></li>
                            <li><a href="/services/absence-compensation/family-message.html">Family Message</a></li>
                            <li><a href="/services/absence-compensation/celebrity-message.html">Celebrity Message</a></li>
                            <li><a href="/services/personalization/ai-video-generator.html">AI Video Generator</a></li>
                            <li><a href="/services/personalization/wedding-trailer.html">Wedding Trailer</a></li>
                            <li><a href="/services/personalization/pet-wedding.html">Pet Wedding</a></li>
                            <li><a href="/services/personalization/multilingual.html">Multilingual Dubbing</a></li>
                            <li><a href="/services/personalization/cartoon-style.html">Cartoon Style</a></li>
                            <li><a href="/services/personalization/meme-generator.html">Wedding Memes &amp; GIFs</a></li>
                        </ul>
                    </div>
                    <div class="footer-col">
                        <h4>Company</h4>
                        <ul>
                            <li><a href="/about.html">About Us</a></li>
                            <li><a href="/gallery.html">Gallery</a></li>
                            <li><a href="/order.html">Get a Quote</a></li>
                        </ul>
                    </div>
                    <div class="footer-col">
                        <h4>Contact</h4>
                        <ul>
                            <li><a href="mailto:order@weddingai.video">order@weddingai.video</a></li>
                        </ul>
                    </div>
'@

# 简化版footer (内联)
$compactFooter = @'
<footer class="site-footer">
        <div class="container footer-inner">
            <div class="footer-brand">
                <a href="/" class="logo"><img src="../../images/logo-full.jpeg" alt="WeddingAI.video" height="7"></a>
                <p>AI-powered wedding video services for couples worldwide.</p>
            </div>
            <nav class="footer-nav" aria-label="Footer navigation">__SERVICES__</nav>
        </div>
        <div class="footer-bottom">
            <div class="container">
                <p>© 2026 WeddingAI.video. All rights reserved.</p>
                <p><a href="../../privacy.html">Privacy Policy</a> · <a href="../../terms.html">Terms of Service</a></p>
            </div>
        </div>
    </footer>
'@

$compactFooter = $compactFooter.Replace('__SERVICES__', $subServices)

foreach ($file in $files) {
    $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
    $original = $content
    $isSub = $file.FullName -like "*\services\*"

    # 1. 替换footer logo height: 28 -> 7
    $content = $content -replace '(<a href="/" class="logo"><img src="[^"]+logo-full\.jpeg" alt="WeddingAI\.video" )height="28"', '$1height="7"'
    $content = $content -replace '(<img src="[^"]+logo-full\.jpeg" alt="WeddingAI\.video" )height="28"', '$1height="7"'

    # 2. 移除 Venue Experiences 链接
    $content = $content -replace '                        <li><a href="/services/(#venue|)">Venue Experiences</a></li>\s*\r?\n', ''

    # 3. 替换 Services 列
    if ($isSub) {
        # 子页面：替换整个 footer-inner
        $pattern = '(?s)<footer class="site-footer">.*?</footer>'
        $content = [regex]::Replace($content, $pattern, $compactFooter)
    } else {
        # 根级页面：只扩展 Services 列
        $oldServicesBlock = '(?s)<div class="footer-col">\s*<h4>Services</h4>\s*<ul>.*?</ul>\s*</div>'
        $content = [regex]::Replace($content, $oldServicesBlock, $fullServices.Trim(), 1)
    }

    if ($content -ne $original) {
        $content | Set-Content -Path $file.FullName -NoNewline -Encoding UTF8
        Write-Host "Updated: $($file.Name)"
    } else {
        Write-Host "No change: $($file.Name)"
    }
}
