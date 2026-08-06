#!/usr/bin/env python3
"""全站配图审计：
1. 列出所有有 h2 的 section
2. 检查该 section 内是否有 <img>
3. 报告缺图的位置"""
import os
import re

ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"

# Find all HTML files
htmls = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in {'.git', 'node_modules', '.wrangler', 'scripts'}]
    for f in filenames:
        if f.endswith('.html'):
            htmls.append(os.path.join(dirpath, f))


def split_sections(content):
    """Split content into sections by <section> tags."""
    sections = []
    for m in re.finditer(r'<section\b[^>]*>(.*?)</section>', content, re.DOTALL):
        sections.append(m)
    return sections


def audit(path):
    rel = os.path.relpath(path, ROOT)
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Skip hero (it has its own image via class)
    findings = []
    sections = split_sections(html)

    for s in sections:
        body = s.group(1)
        # Skip if section is a hero (has .page-hero-bg or .hero class)
        if re.search(r'class="[^"]*(page-hero|hero)[^"]*"', s.group(0)):
            continue
        # Skip section-dark CTA sections (usually just text + button, no need for image)
        if re.search(r'class="[^"]*section-dark[^"]*"', s.group(0)):
            continue
        # Skip nav and footer
        if re.search(r'<(nav|footer)\b', s.group(0)):
            continue

        # Check if section has a <h2>
        h2_m = re.search(r'<h2[^>]*>(.*?)</h2>', body, re.DOTALL)
        if not h2_m:
            continue
        h2_text = re.sub(r'<[^>]+>', '', h2_m.group(1)).strip()
        if not h2_text:
            continue

        # Count images in this section
        n_imgs = len(re.findall(r'<img\b', body))

        # Find number of distinct cards/rows (heuristic: count h3 OR count divs with class containing "card"/"step"/"delivery"/"product")
        n_h3 = len(re.findall(r'<h3[^>]*>(.*?)</h3>', body, re.DOTALL))
        # Card-like structure count
        n_cards = len(re.findall(r'class="[^"]*(card|product|tile|preset|style-card|meme-card|step-card|delivery-card|product-card|service-card|stat-item|testimonial)[^"]*"', body))

        if n_h3 >= 2 or n_cards >= 2:
            n_items = max(n_h3, n_cards)
            if n_imgs < n_items * 0.5:  # Less than half of items have images
                missing = max(0, n_items - n_imgs)
                findings.append((h2_text, n_items, n_imgs, missing))

    return rel, findings


print(f"{'Page':<55} {'Section h2':<45} {'Cards':>5} {'Imgs':>5} {'Missing':>8}")
print('=' * 120)
for path in sorted(htmls):
    rel, findings = audit(path)
    for h2, items, imgs, missing in findings:
        # Trim rel path
        rel_short = rel if len(rel) < 55 else '...' + rel[-52:]
        h2_short = h2 if len(h2) < 45 else h2[:42] + '...'
        print(f"{rel_short:<55} {h2_short:<45} {items:>5} {imgs:>5} {missing:>8}")
