#!/usr/bin/env python3
"""移除 footer 社媒图标和 schema.org 里的 sameAs 数组（无账号）"""
import os
import re
import json

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"


def remove_social_block(content):
    """删除 <div class="footer-social">...</div>"""
    pattern = re.compile(
        r'\s*<div class="footer-social" aria-label="Social media links">.*?</div>',
        re.DOTALL
    )
    return pattern.sub('', content)


def remove_sameas_from_schema(content):
    """从所有 JSON-LD 块中删除 sameAs 数组"""
    pattern = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL)

    def process_script(match):
        body = match.group(1)
        try:
            data = json.loads(body)
        except Exception:
            return match.group(0)

        if isinstance(data, dict) and "sameAs" in data:
            del data["sameAs"]
            # 重新序列化（紧凑输出，不让JSON变得太散）
            new_body = json.dumps(data, ensure_ascii=False, indent=4)
            return f'<script type="application/ld+json">{new_body}</script>'

        return match.group(0)

    return pattern.sub(process_script, content)


def main():
    files = []
    for root, dirs, names in os.walk(ROOT):
        for name in names:
            if name.endswith(".html") and name != "google-site-verification.html":
                files.append(os.path.join(root, name))

    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        original = content

        content = remove_social_block(content)
        content = remove_sameas_from_schema(content)

        if content != original:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(content)
            rel = os.path.relpath(path, ROOT).replace("\\", "/")
            print(f"Cleaned: {rel}")

    print("Done.")


if __name__ == "__main__":
    main()
