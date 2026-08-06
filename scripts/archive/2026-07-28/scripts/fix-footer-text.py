#!/usr/bin/env python3
"""修复 footer Services 列里指向 film-digitization 但文字是 VHS/DV Restoration 的链接"""
import os
import re

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# 模式1：href 已换但 text 还是 VHS / DV Restoration
PATTERN = re.compile(
    r'<li><a href="[^"]*film-digitization\.html" title="VHS / DV Restoration">VHS / DV Restoration</a></li>\s*\r?\n'
)

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
        new_content = PATTERN.sub('', content)
        if new_content != content:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(new_content)
            rel = os.path.relpath(path, ROOT).replace("\\", "/")
            print(f"Fixed: {rel}")
    print("Done.")


if __name__ == "__main__":
    main()
