#!/usr/bin/env python3
"""快速验证定价改动"""
import re

files = {
    'Slow Motion': 'services/video-enhancement/slow-motion.html',
    'Family Tribute': 'services/absence-compensation/family-tribute.html',
    'Family Message': 'services/absence-compensation/family-message.html',
    'Meme Generator': 'services/personalization/meme-generator.html',
    'Services Index': 'services/index.html',
}

for name, f in files.items():
    with open(f, 'r', encoding='utf-8') as fp:
        html = fp.read()
    prices = re.findall(r'\$\d{1,3}(?:,\d{3})*', html)
    print(f'\n{name}:')
    print(f'  All prices found: {sorted(set(prices))}')
