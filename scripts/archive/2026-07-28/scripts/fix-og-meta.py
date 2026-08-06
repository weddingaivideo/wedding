#!/usr/bin/env python3
"""为所有 HTML 页面补上 og:title 和 og:description（从 <title> 和 meta description 取）。"""
import os
import re

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# 已有的页面（index.html, terms.html）跳过
SKIP = {"index.html", "terms.html"}


def escape_attr(s):
    return s.replace("&", "&amp;").replace('"', "&quot;")


def get_meta(html, name):
    m = re.search(rf'<meta\s+name="{name}"\s+content="([^"]+)"', html, re.IGNORECASE)
    return m.group(1) if m else None


def process(path):
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    if rel in SKIP:
        return False
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    title_m = re.search(r"<title>(.*?)</title>", content, re.DOTALL)
    desc = get_meta(content, "description")
    if not title_m or not desc:
        return False

    title = title_m.group(1)
    # If already has og:title, skip
    if 'property="og:title"' in content:
        return False

    og_title = title
    # Trim "| WeddingAI.video" off for og:title (cleaner social card)
    og_title = re.sub(r"\s*\|\s*WeddingAI\.video\s*$", "", og_title)
    # Trim trailing "!"
    og_title = og_title.rstrip("!")

    og_block = (
        f'    <meta property="og:title" content="{escape_attr(og_title)}">\n'
        f'    <meta property="og:description" content="{escape_attr(desc)}">\n'
    )

    # Insert before </head>
    new_content = content.replace("</head>", og_block + "</head>", 1)
    if new_content == content:
        return False
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(new_content)
    return True


def main():
    files = []
    for root, dirs, names in os.walk(ROOT):
        if "scripts\\archive" in root or "scripts/archive" in root:
            continue
        for name in names:
            if name.endswith(".html") and name != "google-site-verification.html":
                files.append(os.path.join(root, name))

    for path in files:
        if process(path):
            rel = os.path.relpath(path, ROOT).replace("\\", "/")
            print(f"  ✓ {rel}")


if __name__ == "__main__":
    main()
