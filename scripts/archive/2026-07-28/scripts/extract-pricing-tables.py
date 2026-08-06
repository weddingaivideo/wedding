#!/usr/bin/env python3
"""提取每个服务的价格表（含每档对应的内容）"""
import re
import os

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

SERVICES = [
    ('Slow Motion', 'services/video-enhancement/slow-motion.html'),
    ('Family Tribute', 'services/absence-compensation/family-tribute.html'),
    ('Family Message', 'services/absence-compensation/family-message.html'),
    ('Celebrity Message', 'services/absence-compensation/celebrity-message.html'),
    ('AI Video Generator', 'services/personalization/ai-video-generator.html'),
    ('Wedding Trailer', 'services/personalization/wedding-trailer.html'),
    ('Pet Wedding', 'services/personalization/pet-wedding.html'),
    ('Multilingual', 'services/personalization/multilingual.html'),
    ('Cartoon Style', 'services/personalization/cartoon-style.html'),
    ('Meme Generator', 'services/personalization/meme-generator.html'),
]

for name, rel in SERVICES:
    path = os.path.join(ROOT, rel)
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    print(f'\n========== {name} ==========')

    # Find pricing table section
    pricing_section = re.search(r'<section[^>]*pricing[^>]*>(.*?)</section>', html, re.IGNORECASE | re.DOTALL)
    if not pricing_section:
        # try to find any pricing-related div
        pricing_section = re.search(r'(<div[^>]*class="[^"]*pricing[^"]*"[^>]*>.*?</div>\s*</div>)', html, re.DOTALL | re.IGNORECASE)
    if not pricing_section:
        # find by looking for "$" near label
        m = re.search(r'(pricing|tier|package).*?</section>', html, re.IGNORECASE | re.DOTALL)
        if m:
            pricing_section = m

    # Just extract all pricing-row divs
    rows = re.findall(r'<div class="pricing-row[^"]*">(.*?)</div>', html, re.DOTALL)
    if not rows:
        # Try spans
        rows = re.findall(r'<span class="label[^"]*">(.*?)</span>\s*<span class="value[^"]*">\s*(\$\d+)', html, re.DOTALL)

    for r in rows[:10]:
        clean = re.sub(r'<[^>]+>', ' ', r)
        clean = re.sub(r'\s+', ' ', clean).strip()
        if clean and len(clean) < 200:
            print(f'  - {clean}')

    # Also extract product-price spans
    pp = re.findall(r'<span class="product-price[^"]*">(.*?)</span>', html, re.DOTALL)
    if pp:
        for x in pp[:6]:
            clean = re.sub(r'<[^>]+>', ' ', x).strip()
            print(f'  [product] {clean}')

    # Find any "starting at" or "from" text
    starts = re.findall(r'(?:Starting at|From|starts at|starting at)[^<]{0,80}', html, re.IGNORECASE)
    for s in starts[:3]:
        print(f'  {s.strip()}')
