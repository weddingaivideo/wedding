#!/usr/bin/env python3
"""同步 schema.org 价格到新的最低档：
- Meme Generator: schema 49 → 79
- Slow Motion: schema 99 → 49
"""
import os
import re

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

CHANGES = [
    ("services/personalization/meme-generator.html", "79"),
    ("services/video-enhancement/slow-motion.html", "49"),
]

for rel, new_price in CHANGES:
    path = os.path.join(ROOT, rel)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # Find the service offer block and replace
    # Pattern: "price": "X", followed by "minPrice": "X", "price": "X"
    pattern = re.compile(
        r'("price"\s*:\s*")\d+(",\s*"priceSpecification"\s*:\s*\{\s*"@type"\s*:\s*"PriceSpecification"\s*,\s*"priceCurrency"\s*:\s*"USD"\s*,\s*"minPrice"\s*:\s*")\d+("\s*,\s*"price"\s*:\s*")\d+(")',
        re.DOTALL
    )
    m = pattern.search(content)
    if not m:
        print(f"  ✗ {rel}: pattern not found")
        continue
    new_content = pattern.sub(lambda m: m.group(1) + new_price + m.group(2) + new_price + m.group(3) + new_price + m.group(4), content)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(new_content)
    print(f"  ✓ {rel}: schema price updated to {new_price}")
