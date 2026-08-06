#!/usr/bin/env python3
"""恢复之前错误插入的title (在 </a> 之后)"""
import os
import re

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# 匹配 </a title="..."> (包括多行内容) - title=".*?" 不能跨行，所以简单
# 但 title 中可能有 &quot; 之类
BAD_PATTERN = re.compile(r'</a\s+title="[^"]*">')

def main():
    files = []
    for root, dirs, names in os.walk(ROOT):
        for name in names:
            if name.endswith(".html") and name != "google-site-verification.html":
                files.append(os.path.join(root, name))

    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        new_content = BAD_PATTERN.sub('</a>', content)
        if new_content != content:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(new_content)
            rel = os.path.relpath(path, ROOT)
            print(f"Reverted: {rel}")
    print("Done.")

if __name__ == "__main__":
    main()
