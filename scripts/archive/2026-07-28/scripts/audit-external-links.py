"""Audit blog posts for external links (href starting with http/https to non-weddingai.video domains).

Tally by domain and list each link with the file + text so we can see whether
they're intentional (viddo.ai etc.) or possibly injected.
"""
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
BLOG = ROOT / "blog"
OWN = "weddingai.video"
SELF = "weddingai.video"

# Anchor href values
HREF_RE = re.compile(r'<a\s+[^>]*href="([^"]+)"', re.IGNORECASE)
# Also <a> with single-quoted href
HREF_RE2 = re.compile(r"<a\s+[^>]*href='([^']+)'", re.IGNORECASE)
# Title attribute
TITLE_RE = re.compile(r'\btitle="([^"]+)"')
# Anchor text (rough)
def anchor_text(html: str, start: int) -> str:
    end = html.find('</a>', start)
    if end == -1:
        return ''
    inner = html[start:end]
    return re.sub(r'<[^>]+>', '', inner).strip()

per_domain = Counter()
per_file = defaultdict(list)

count = 0
for html_file in sorted(BLOG.glob("*/index.html")):
    text = html_file.read_text(encoding='utf-8')
    rel = html_file.parent.name
    # Strip script and style to avoid matching href in JS strings
    text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL)
    for m in HREF_RE.finditer(text) or HREF_RE2.finditer(text):
        href = m.group(1).strip()
        # External only
        if href.startswith(('http://', 'https://')):
            domain_m = re.match(r'https?://([^/]+)/?', href)
            if not domain_m:
                continue
            domain = domain_m.group(1)
            if domain == SELF or domain.endswith('.' + SELF):
                continue
            atext = anchor_text(text, m.end())
            per_domain[domain] += 1
            per_file[rel].append((href, atext))
            count += 1

print(f"Total external links across {len(per_file)} blog posts: {count}\n")
print("=== Top domains ===")
for dom, n in per_domain.most_common():
    print(f"  {n:3d}  {dom}")

print("\n=== Per-file breakdown (top files by link count) ===")
for rel, links in sorted(per_file.items(), key=lambda x: -len(x[1]))[:15]:
    print(f"  {len(links):2d}  {rel}")
    for href, atext in links[:5]:
        print(f"      {href}  ({atext[:60]!r})")
