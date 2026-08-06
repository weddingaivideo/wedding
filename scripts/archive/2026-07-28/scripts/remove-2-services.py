#!/usr/bin/env python3
"""删除 film-digitization 和 wedding-invitation 服务后的全面清理"""
import os
import re

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# 1. 删除 footer Services 列里的 Film Digitization 和 Animated Invitation 链接
FOOTER_LINKS = [
    '<li><a href="/services/video-enhancement/film-digitization.html" title="Film Digitization">Film Digitization</a></li>\n',
    '<li><a href="/services/personalization/wedding-invitation.html" title="Animated Invitation">Animated Invitation</a></li>\n',
    # 不同的缩进版本
    '                                                        <li><a href="/services/video-enhancement/film-digitization.html" title="Film Digitization">Film Digitization</a></li>\n',
    '                                                        <li><a href="/services/personalization/wedding-invitation.html" title="Animated Invitation">Animated Invitation</a></li>\n',
    '                            <li><a href="/services/video-enhancement/film-digitization.html" title="Film Digitization">Film Digitization</a></li>\n',
    '                            <li><a href="/services/personalization/wedding-invitation.html" title="Animated Invitation">Animated Invitation</a></li>\n',
]

# 2. 删除 services/index.html 中 film-digitization 卡片
FILM_DIGITIZATION_CARD = re.compile(
    r'\s*<div class="service-sub-card">\s*<h3><a href="video-enhancement/film-digitization\.html"[^>]*>8mm &amp; 16mm Film Digitization</a></h3>\s*<p>Convert vintage film reels to digital with AI color reconstruction\.</p>\s*<span class="price-hint">From \$149</span>\s*</div>',
    re.DOTALL
)

# 3. 删除 services/index.html 中 wedding-invitation 卡片
WEDDING_INVITATION_CARD = re.compile(
    r'\s*<div class="service-sub-card">\s*<h3><a href="personalization/wedding-invitation\.html"[^>]*>Animated Wedding Invitation</a></h3>\s*<p>Digital save-the-date video with optional H5 RSVP microsite\.</p>\s*<span class="price-hint">From \$79</span>\s*</div>',
    re.DOTALL
)

# 4. 删除 order.html 的 option
ORDER_OPTIONS = [
    re.compile(r'\s*<option value="film-digitization">[^<]+</option>'),
    re.compile(r'\s*<option value="wedding-invitation">[^<]+</option>'),
]


def process_html(content):
    original = content

    # 1. 删除 footer 链接（多种缩进形式）
    for line in FOOTER_LINKS:
        content = content.replace(line, "")

    # 2. 删除 services/index.html 的卡片
    content = FILM_DIGITIZATION_CARD.sub('', content)
    content = WEDDING_INVITATION_CARD.sub('', content)

    # 3. 删除 order.html 的 option
    for pat in ORDER_OPTIONS:
        content = pat.sub('', content)

    return content, content != original


def main():
    files = []
    for root, dirs, names in os.walk(ROOT):
        if "scripts\\archive" in root or "scripts/archive" in root:
            continue
        for name in names:
            if name.endswith(".html") and name != "google-site-verification.html":
                files.append(os.path.join(root, name))

    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        new_content, changed = process_html(content)
        if changed:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(new_content)
            rel = os.path.relpath(path, ROOT).replace("\\", "/")
            print(f"Updated: {rel}")
    print("Done.")


if __name__ == "__main__":
    main()
