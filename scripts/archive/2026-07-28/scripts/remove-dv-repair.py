#!/usr/bin/env python3
"""删除 dv-repair 页面后的全面清理"""
import os
import re

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# 1. 替换所有指向 dv-repair 的链接为 film-digitization (或对应服务)
LINK_REPLACEMENTS = [
    # (old_href, new_href)
    ("/services/video-enhancement/dv-repair.html", "/services/video-enhancement/film-digitization.html"),
    ("services/video-enhancement/dv-repair.html", "services/video-enhancement/film-digitization.html"),
    ("video-enhancement/dv-repair.html", "video-enhancement/film-digitization.html"),
    # 锚点版本
    ("https://weddingai.video/services/video-enhancement/dv-repair/", "https://weddingai.video/services/video-enhancement/film-digitization.html"),
    ("/services/video-enhancement/dv-repair/", "/services/video-enhancement/film-digitization.html"),
]

# 2. 删除 footer Services 列里的 "VHS / DV Restoration" 行
FOOTER_LINKS_TO_REMOVE = [
    '<li><a href="/services/video-enhancement/dv-repair.html" title="VHS / DV Restoration">VHS / DV Restoration</a></li>',
    '<li><a href="/services/video-enhancement/dv-repair.html" title="VHS / DV Restoration" >VHS / DV Restoration</a></li>',
]

# 3. 删除 services/index.html 中 dv-repair 整张卡片
DV_REPAIR_CARD = re.compile(
    r'\s*<div class="service-sub-card">\s*<h3><a href="video-enhancement/dv-repair\.html"[^>]*>VHS / DV Tape Restoration</a></h3>\s*<p>Repair damaged VHS, DV, Hi8 tapes with AI upscaling, denoising, and color correction\.</p>\s*<span class="price-hint">From \$99</span>\s*</div>',
    re.DOTALL
)

# 4. 删除 order.html 的 <option value="dv-repair">
ORDER_OPTION = re.compile(r'\s*<option value="dv-repair">[^<]+</option>')

# 5. 修改 index.html 中 Video Enhancement service card 指向 film-digitization
# 这个手动处理

def process_html(content):
    original = content
    # 1. 替换链接
    for old, new in LINK_REPLACEMENTS:
        content = content.replace(old, new)

    # 2. 删除 footer Services 列里的 "VHS / DV Restoration" 链接
    for line in FOOTER_LINKS_TO_REMOVE:
        content = content.replace(line + "\n", "")
        content = content.replace(line, "")

    # 3. 删除 dv-repair 卡片 (在 services/index.html)
    content = DV_REPAIR_CARD.sub('', content)

    # 4. 删除 order.html 的 option
    content = ORDER_OPTION.sub('', content)

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
