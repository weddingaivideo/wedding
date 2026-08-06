"""Verify the blog detail page hero is no longer a flat gray."""
import re
import urllib.request

URLS = [
    'https://weddingai.video/blog/01-restore-old-wedding-videos/',
    'https://weddingai.video/blog/25-wedding-video-gift-ideas/',
    'https://weddingai.video/blog/50-weddingai-success-stories/',
]

for url in URLS:
    print(f"==== {url} ====")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  ERR: {e}")
        continue
    # Find page-hero section
    m = re.search(r'<section class="page-hero[^"]*">.*?</section>', html, re.DOTALL)
    if not m:
        print("  no page-hero section")
        continue
    sec = m.group(0)
    # Check page-hero-bg content
    bg = re.search(r'<div class="page-hero-bg">(.*?)</div>', sec, re.DOTALL)
    if bg and '<img' in bg.group(1):
        img = re.search(r'<img[^>]+src="([^"]+)"', bg.group(1))
        print(f"  page-hero-bg HAS <img>: {img.group(1) if img else '?'}")
    else:
        print(f"  page-hero-bg is empty (still gray!)")
    # Check for duplicate blog-hero figure
    if 'class="blog-hero"' in html:
        # check if it's a CSS class ref or actual element
        figure_count = len(re.findall(r'<figure class="blog-hero">', html))
        if figure_count:
            print(f"  WARN: {figure_count} duplicate blog-hero figure(s) remain")
