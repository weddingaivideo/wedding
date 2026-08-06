"""Verify the live /blog/ page has no page-hero and goes directly to the list."""
import re
import urllib.request

url = 'https://weddingai.video/blog/'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=15) as r:
    html = r.read().decode('utf-8', errors='ignore')

# Check no page-hero
has_hero = bool(re.search(r'<section class="page-hero', html))
print(f"page-hero present: {has_hero} (want False)")

# Check no visible h2 'All Wedding Video Guides & Tips'
has_visible_h2 = bool(re.search(r'<h2[^>]*>All Wedding Video Guides', html))
print(f"visible h2 'All Wedding Video Guides' present: {has_visible_h2} (want False)")

# Check sr-only h1
sr_h1 = re.search(r'<h1 class="sr-only">([^<]+)</h1>', html)
print(f"sr-only h1: {sr_h1.group(1) if sr_h1 else 'MISSING'}")

# Check first visible content is article card
first_article = re.search(r'<article class="case-card">', html)
print(f"first <article class='case-card'> found: {bool(first_article)}")

# Check heading chain (no skip)
pat = re.compile(r'<h([1-6])[^>]*>(.*?)</h\1>', re.DOTALL)
prev = 0
skips = 0
for lvl, _ in pat.findall(html):
    lvl_i = int(lvl)
    if prev > 0 and lvl_i > prev + 1:
        skips += 1
    prev = lvl_i
print(f"heading skips: {skips} (want 0)")
