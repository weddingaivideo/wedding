#!/usr/bin/env python3
"""在所有页面的 WebSite schema 中加 SearchAction。
让 Google 在搜索结果里显示 sitelinks searchbox。
"""
import os
import re

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# Match the WebSite schema block (5 lines after "@type": "WebSite",)
# We insert potentialAction before the closing brace
SCHEMA_PATTERN = re.compile(
    r'(        "@type": "WebSite",\n'
    r'        "@id": "https://weddingai\.video/#website",\n'
    r'        "url": "https://weddingai\.video",\n'
    r'        "name": "WeddingAI\.video",\n'
    r'        "description": "AI-powered wedding video services for couples worldwide\.",\n'
    r'        "publisher": \{"@id": "https://weddingai\.video/#organization"\},\n)'
    r'(        "inLanguage": "en-US"\n    \})',
    re.MULTILINE
)

SEARCH_ACTION = '''        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": "https://weddingai.video/search?q={search_term_string}"
            },
            "query-input": "required name=search_term_string"
        },
        "inLanguage": "en-US"
    }'''

# Idempotency check
ALREADY_ADDED = re.compile(r'"@type": "SearchAction"')


def find_html_files():
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in {'.git', 'node_modules', '.wrangler'}]
        for f in filenames:
            if f.endswith('.html'):
                out.append(os.path.join(dirpath, f))
    return sorted(out)


def process(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if ALREADY_ADDED.search(content):
        return 0

    def replace(m):
        return m.group(1) + SEARCH_ACTION

    new_content, n = SCHEMA_PATTERN.subn(replace, content)
    if n == 0:
        return 0
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(new_content)
    return n


def main():
    n_total = 0
    for path in find_html_files():
        rel = os.path.relpath(path, ROOT)
        n = process(path)
        if n:
            print(f"  ✓ {rel}: added SearchAction to {n} WebSite schema(s)")
            n_total += n
    print(f"\nTotal: {n_total} schemas updated")


if __name__ == "__main__":
    main()
