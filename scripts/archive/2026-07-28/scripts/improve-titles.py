#!/usr/bin/env python3
"""改进 title: 把 'Learn More' 等通用title换成更具体的"""
import os
import re

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# 改进 title 映射
TITLE_IMPROVEMENTS = {
    "Learn More": "Learn more about this service",
    "View All Cases": "View all case studies",
    "Send My Request — Free Quote": "Send my request — get a free quote",
    "Send My Request": "Send my request — get a free quote",
}

# 匹配 title="Learn More" 等
def improve_title(match):
    current_title = match.group(1)
    if current_title in TITLE_IMPROVEMENTS:
        return f'title="{TITLE_IMPROVEMENTS[current_title]}"'
    return match.group(0)


def main():
    files = []
    for root, dirs, names in os.walk(ROOT):
        for name in names:
            if name.endswith(".html") and name != "google-site-verification.html":
                files.append(os.path.join(root, name))

    pattern = re.compile(r'title="([^"]*)"')

    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        new_content = pattern.sub(improve_title, content)
        if new_content != content:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(new_content)
            rel = os.path.relpath(path, ROOT)
            print(f"Improved: {rel}")
    print("Done.")


if __name__ == "__main__":
    main()
