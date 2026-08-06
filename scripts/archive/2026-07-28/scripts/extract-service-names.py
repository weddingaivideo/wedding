#!/usr/bin/env python3
"""提取 order.html / index.html / 页脚 的服务显示名对比"""
import re
import os

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# Known service slugs
SLUGS = ['slow-motion', 'family-message', 'family-tribute', 'celebrity-message',
         'ai-video-generator', 'wedding-trailer', 'pet-wedding', 'multilingual',
         'cartoon-style', 'meme-generator']

# 1. Order form options
print('=' * 70)
print('1. ORDER FORM (order.html)')
print('=' * 70)
with open(os.path.join(ROOT, 'order.html'), 'r', encoding='utf-8') as f:
    order = f.read()
m = re.search(r'<select[^>]*id="service"[^>]*>(.*?)</select>', order, re.DOTALL)
if m:
    block = m.group(1)
    for opt in re.finditer(r'<option value="([^"]+)">([^<]+)</option>', block):
        val, label = opt.group(1), opt.group(2).strip()
        if val and val != 'other':
            print(f'  {val:25s} → "{label}"')
    other = re.search(r'<option value="other">([^<]+)</option>', block)
    if other:
        print(f'  {"(other)":25s} → "{other.group(1).strip()}"')

# 2. Footer (sample from about.html, all footers are identical)
print()
print('=' * 70)
print('2. FOOTER (sampled from about.html)')
print('=' * 70)
with open(os.path.join(ROOT, 'about.html'), 'r', encoding='utf-8') as f:
    about = f.read()
# Footer is the <footer>...</footer> block
m = re.search(r'<footer[^>]*>(.*?)</footer>', about, re.DOTALL)
if m:
    footer = m.group(1)
    # Service links: find <a href=".../services/.../SLUG.html" title="...">DISPLAY</a>
    seen = set()
    for link in re.finditer(r'<a href="[^"]*/services/[^"]+/(%s)\.html"[^>]*>([^<]+)</a>' % '|'.join(SLUGS), footer):
        slug, label = link.group(1), link.group(2).strip()
        if slug not in seen:
            print(f'  {slug:25s} → "{label}"')
            seen.add(slug)

# 3. Homepage (index.html) service cards
print()
print('=' * 70)
print('3. HOMEPAGE (index.html) — service cards')
print('=' * 70)
with open(os.path.join(ROOT, 'index.html'), 'r', encoding='utf-8') as f:
    index = f.read()
# Find <h3>DISPLAY NAME</h3> followed by <a href=".../services/.../SLUG.html"
for h3 in re.finditer(r'<h3[^>]*>(.*?)</h3>(.*?)(?=<h3|</article>)', index, re.DOTALL):
    name = re.sub(r'<[^>]+>', '', h3.group(1)).strip()
    if not name:
        continue
    block = h3.group(2)
    link = re.search(r'href="[^"]*/services/[^"]+/([^/"]+)\.html"', block)
    if link:
        slug = link.group(1)
        if slug in SLUGS:
            print(f'  {slug:25s} → "{name}"')

# 4. services/index.html
print()
print('=' * 70)
print('4. SERVICES INDEX (services/index.html) — service cards')
print('=' * 70)
with open(os.path.join(ROOT, 'services', 'index.html'), 'r', encoding='utf-8') as f:
    six = f.read()
for h3 in re.finditer(r'<h3[^>]*>\s*<a[^>]*href="[^"]*/services/[^"]+/([^/"]+)\.html"[^>]*>(.*?)</a>\s*</h3>', six):
    slug = h3.group(1)
    name = re.sub(r'<[^>]+>', '', h3.group(2)).strip()
    if slug in SLUGS:
        print(f'  {slug:25s} → "{name}"')
