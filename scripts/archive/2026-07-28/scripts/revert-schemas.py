#!/usr/bin/env python3
"""移除已添加的 schema 块以便重新生成"""
import os
import re
import json

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

TYPES_TO_REMOVE = {"FAQPage", "Review", "Service", "BreadcrumbList", "Product"}


def process_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    original = content

    # 找到 <script type="application/ld+json">...</script>
    pattern = re.compile(r'\s*<script type="application/ld\+json">(.*?)</script>', re.DOTALL)

    def remove_if_targeted(match):
        body = match.group(1)
        # 解析 JSON
        try:
            data = json.loads(body)
            t = data.get("@type", "")
            if t in TYPES_TO_REMOVE:
                return ''
        except Exception:
            pass
        return match.group(0)

    new_content = pattern.sub(remove_if_targeted, content)
    if new_content != content:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new_content)
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        print(f"Cleaned: {rel}")


def main():
    for root, dirs, names in os.walk(ROOT):
        for name in names:
            if name.endswith(".html") and name != "google-site-verification.html":
                path = os.path.join(root, name)
                process_file(path)
    print("Done.")


if __name__ == "__main__":
    main()
