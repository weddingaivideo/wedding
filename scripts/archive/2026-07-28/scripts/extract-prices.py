#!/usr/bin/env python3
"""提取所有服务页的报价信息"""
import re
import os

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

SERVICES = [
    'services/video-enhancement/slow-motion.html',
    'services/absence-compensation/family-tribute.html',
    'services/absence-compensation/family-message.html',
    'services/absence-compensation/celebrity-message.html',
    'services/personalization/ai-video-generator.html',
    'services/personalization/wedding-trailer.html',
    'services/personalization/pet-wedding.html',
    'services/personalization/multilingual.html',
    'services/personalization/cartoon-style.html',
    'services/personalization/meme-generator.html',
]

for s in SERVICES:
    path = os.path.join(ROOT, s)
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
    title_m = re.search(r'<title>(.*?)</title>', html)
    title = title_m.group(1) if title_m else "N/A"

    # Find all $N or $N,NNN
    prices = sorted(set(re.findall(r'\$\d{1,3}(?:,\d{3})*', html)))

    # Find lines with price
    price_lines = []
    for line in html.split('\n'):
        if '$' in line and re.search(r'\$\d', line):
            stripped = re.sub(r'\s+', ' ', line.strip())
            if len(stripped) < 250:
                price_lines.append(stripped)

    print(f'\n== {s} ==')
    print(f'  Title: {title}')
    print(f'  All dollar values: {prices}')
    print(f'  Price-related lines:')
    for pl in price_lines[:6]:
        print(f'    {pl[:200]}')
