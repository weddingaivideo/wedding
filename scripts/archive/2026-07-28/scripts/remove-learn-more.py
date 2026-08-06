#!/usr/bin/env python3
"""删除所有页面的 'Learn More' 外链块。
匹配: <section ...> ... <h2 ...>Learn More</h2> ... </section>
"""
import os
import re

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# Match the entire <section>...</section> block containing 'Learn More' heading.
# Capture: the leading whitespace before <section>
PATTERN = re.compile(
    r'[ \t]*<section class="section" style="background: var\(--color-bg-alt\);">\s*'
    r'<div class="container" style="max-width: 800px;">\s*'
    r'<h2 style="text-align:center; font-size:1\.25rem;[^>]*>Learn More</h2>.*?</section>\s*',
    re.DOTALL
)

# Idempotency
ALREADY_REMOVED = re.compile(r'>Learn More</h2>')


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
    if not ALREADY_REMOVED.search(content):
        return 0
    new_content, n = PATTERN.subn('', content)
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
            print(f"  ✓ {rel}: removed {n} block(s)")
            n_total += n
    print(f"\nTotal: {n_total} blocks removed")


if __name__ == "__main__":
    main()
