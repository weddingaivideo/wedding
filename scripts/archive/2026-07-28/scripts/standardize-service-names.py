#!/usr/bin/env python3
"""统一服务命名（3 个地方）：
1. order.html 的 <option> 标签 → canonical 名
2. 18 个页面的页脚服务链接 → 短名（显示）+ canonical 名（title）
3. services/index.html 的卡片标题 → canonical 名

不动详情页 H1（每页内部上下文自洽，不参与跨页一致性）
"""
import os
import re

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# Canonical name and short name per service slug.
# These are user-facing labels. Page URLs, slugs, form values stay the same.
NAMES = {
    'slow-motion':          ('AI Slow Motion Enhancement',  'Slow Motion'),
    'family-message':       ('Remote Family Video Message','Family Message'),
    'family-tribute':       ('Tribute to Loved Ones',      'Family Tribute'),
    'celebrity-message':    ('Celebrity-Style Wedding Message', 'Celebrity Message'),
    'ai-video-generator':   ('AI Wedding Video Generator', 'AI Video Generator'),
    'wedding-trailer':      ('Cinematic Wedding Trailer',  'Wedding Trailer'),
    'pet-wedding':          ('Pet Wedding Video',          'Pet Wedding'),
    'multilingual':         ('Multilingual Wedding Video', 'Multilingual'),
    'cartoon-style':        ('Cartoon / Animated Style',   'Cartoon Style'),
    'meme-generator':       ('Wedding GIFs & Memes',       'Wedding Memes'),
}


def update_order_form():
    """order.html: change each <option value="SLUG">LABEL</option>"""
    path = os.path.join(ROOT, 'order.html')
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    changes = 0
    for slug, (canonical, _short) in NAMES.items():
        # Match: <option value="SLUG">ANYTHING</option>
        pattern = re.compile(
            rf'(<option value="{re.escape(slug)}">)[^<]+(</option>)'
        )
        new_content, n = pattern.subn(rf'\g<1>{canonical}\g<2>', content)
        if n > 0:
            content = new_content
            changes += n
            print(f'  ✓ order.html: "{slug}" → "{canonical}"')
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    return changes


def update_footers():
    """All HTML pages: change footer service link text + title"""
    total = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in {'.git', 'node_modules', '.wrangler'}]
        for f in filenames:
            if not f.endswith('.html'):
                continue
            path = os.path.join(dirpath, f)
            with open(path, 'r', encoding='utf-8') as fp:
                content = fp.read()
            file_changes = 0
            for slug, (canonical, short) in NAMES.items():
                # Match: <a href=".../SLUG.html" title="X">Y</a>
                # We want title="CANONICAL" and Y=SHORT
                pattern = re.compile(
                    rf'(<a href="[^"]*/{re.escape(slug)}\.html"\s+title=")[^"]+(">)[^<]+(</a>)'
                )
                new_content, n = pattern.subn(
                    rf'\g<1>{canonical}\g<2>{short}\g<3>',
                    content
                )
                if n > 0:
                    content = new_content
                    file_changes += n
            if file_changes:
                with open(path, 'w', encoding='utf-8', newline='') as fp:
                    fp.write(content)
                rel = os.path.relpath(path, ROOT)
                print(f'  ✓ {rel}: {file_changes} footer link(s) updated')
                total += file_changes
    return total


def update_services_index():
    """services/index.html: change card title link text + title to canonical"""
    path = os.path.join(ROOT, 'services', 'index.html')
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    changes = 0
    for slug, (canonical, _short) in NAMES.items():
        # Match: <a href=".../SLUG.html" title="X">Y</a> inside h3
        pattern = re.compile(
            rf'(<a href="[^"]*/{re.escape(slug)}\.html"\s+title=")[^"]+(">)[^<]+(</a>)'
        )
        new_content, n = pattern.subn(
            rf'\g<1>{canonical}\g<2>{canonical}\g<3>',
            content
        )
        if n > 0:
            content = new_content
            changes += n
            print(f'  ✓ services/index.html: "{slug}" → "{canonical}"')
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    return changes


def main():
    print("=" * 60)
    print("STEP 1: order.html <option> labels")
    print("=" * 60)
    n1 = update_order_form()

    print()
    print("=" * 60)
    print("STEP 2: Footer service links in all HTML files")
    print("=" * 60)
    n2 = update_footers()

    print()
    print("=" * 60)
    print("STEP 3: services/index.html card titles")
    print("=" * 60)
    n3 = update_services_index()

    print()
    print(f"=== Total: {n1 + n2 + n3} changes applied ===")


if __name__ == "__main__":
    main()
