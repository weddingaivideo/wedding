#!/usr/bin/env python3
"""
Pass 4: C6 (trust badges) + C12 (blog cross-linking) + B8 (remove search nav) + D5 cont.
"""
import re
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
BLOG = ROOT / "blog"

# ---- C12: blog cross-linking ----
print("=== C12: blog cross-linking (Related Articles) ===")
posts = sorted([p for p in BLOG.iterdir() if p.is_dir() and p.name != "blog"],
               key=lambda p: p.name)
print(f"  Total blog posts: {len(posts)}")

# Extract title for each post
def get_title(post_dir):
    raw = (post_dir / "index.html").read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"<h1[^>]*>([^<]+)</h1>", raw)
    return m.group(1).strip() if m else post_dir.name

titles = {p.name: get_title(p) for p in posts}
print(f"  Sample titles:")
for name in list(titles.keys())[:3]:
    print(f"    {name}: {titles[name]}")

# Add "Related Articles" section to each blog post
def find_faq_section(raw):
    """Find the FAQ <details>...</details> block to insert after."""
    # Find the last </details> in the FAQ area
    last = raw.rfind("</details>")
    if last == -1:
        # No <details> in this page; insert before footer or before </main>
        m = re.search(r"</main>", raw)
        return m.start() if m else -1
    return last + len("</details>")

RELATED_BLOCK = """
        <section class="section" style="background: var(--color-bg-alt);">
            <div class="container" style="max-width: 820px;">
                <header class="section-header" style="text-align: left; margin-bottom: var(--spacing-md);">
                    <h2 style="text-align: left;">Related Articles</h2>
                </header>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: var(--spacing-md);">
{related_links}
                </div>
            </div>
        </section>
"""

# For each post, link to 3 "next" posts (cyclic)
# To make this deterministic but look organic: post N links to N+1, N+2, N+3 (mod 50)
n = len(posts)
added = 0
for i, p in enumerate(posts):
    idx = p / "index.html"
    raw = idx.read_text(encoding="utf-8")
    if "<!-- RELATED ARTICLES BLOCK -->" in raw:
        continue  # already added
    # Pick 3 related posts (next 3 in the sorted list, wrapping around)
    rels = []
    for offset in [1, 2, 3]:
        rp = posts[(i + offset) % n]
        rels.append((rp.name, titles[rp.name]))
    # Build related link cards
    related_links = ""
    for slug, title in rels:
        related_links += f'                    <a href="/blog/{slug}/" class="related-card" style="display:block;background:var(--color-white);border:1px solid var(--color-border);border-radius:var(--radius-md);padding:var(--spacing-md);text-decoration:none;color:inherit;">\n                        <h4 style="font-family:var(--font-heading);color:var(--color-secondary);font-size:0.9375rem;margin:0 0 0.4rem 0;line-height:1.3;">{title}</h4>\n                        <span style="color:var(--color-primary);font-size:0.8125rem;font-weight:600;">Read article &rarr;</span>\n                    </a>\n'
    block = "<!-- RELATED ARTICLES BLOCK -->\n" + RELATED_BLOCK.format(related_links=related_links)
    # Find insertion point: after the FAQ section (last </details>), or before </main>
    insert_pos = find_faq_section(raw)
    if insert_pos == -1:
        # try before footer
        m = re.search(r"<footer", raw)
        insert_pos = m.start() if m else len(raw) - 100
    raw = raw[:insert_pos] + block + "\n        " + raw[insert_pos:]
    idx.write_text(raw, encoding="utf-8", newline="")
    added += 1
print(f"  Added Related Articles to {added} blog posts")

# ---- C6: trust badges ----
print("\n=== C6: trust badges on homepage ===")
TRUST_STRIP = """
        <!-- TRUST BADGES -->
        <section class="section" style="background: var(--color-bg-alt); padding: 1.5rem 0; border-top: 1px solid var(--color-border); border-bottom: 1px solid var(--color-border);">
            <div class="container">
                <div style="display: flex; flex-wrap: wrap; justify-content: center; align-items: center; gap: 2rem; font-size: 0.875rem; color: var(--color-text-light);">
                    <span style="display: inline-flex; align-items: center; gap: 0.5rem;">
                        <span style="font-size: 1.25rem;" aria-hidden="true">&#128274;</span>
                        <strong style="color: var(--color-secondary);">SSL Secured</strong>
                    </span>
                    <span style="display: inline-flex; align-items: center; gap: 0.5rem;">
                        <span style="font-size: 1.25rem;" aria-hidden="true">&#9989;</span>
                        <strong style="color: var(--color-secondary);">GDPR Compliant</strong>
                    </span>
                    <span style="display: inline-flex; align-items: center; gap: 0.5rem;">
                        <span style="font-size: 1.25rem;" aria-hidden="true">&#128179;</span>
                        <strong style="color: var(--color-secondary);">Stripe &amp; PayPal</strong>
                    </span>
                    <span style="display: inline-flex; align-items: center; gap: 0.5rem;">
                        <span style="font-size: 1.25rem;" aria-hidden="true">&#11088;</span>
                        <strong style="color: var(--color-secondary);">4.9/5 from 6 verified reviews</strong>
                    </span>
                    <span style="display: inline-flex; align-items: center; gap: 0.5rem;">
                        <span style="font-size: 1.25rem;" aria-hidden="true">&#128666;</span>
                        <strong style="color: var(--color-secondary);">100% Money-Back</strong>
                    </span>
                </div>
            </div>
        </section>
"""

# Insert trust strip after the hero on the homepage
homepage = ROOT / "index.html"
raw = homepage.read_text(encoding="utf-8")
if "<!-- TRUST BADGES -->" not in raw:
    # Insert after the hero section's closing </section> (the </section> after hero-overlay)
    # Find the first </section> after the hero CTA buttons
    marker = "    <!-- ========== SERVICES OVERVIEW ========== -->"
    if marker in raw:
        raw = raw.replace(marker, TRUST_STRIP + "\n" + marker, 1)
        homepage.write_text(raw, encoding="utf-8", newline="")
        print("  Added trust strip to homepage")
    else:
        print("  Hero/services marker not found")
else:
    print("  Trust strip already present")

# ---- B8: remove Search from main nav (keep /search/ page) ----
print("\n=== B8: remove /search/ from main nav (the 16-entry fake search) ===")
SEARCH_NAV_PATTERNS = [
    '<li><a href="/search/" title="Find specific topics or services" data-i18n="404.a_text.search.27130699"></a></li>\n                    ',
    '<li><a href="/search/" title="Find specific topics or services" data-i18n="404.a_text.search.27130699">Search</a></li>\n                    ',
]
total_removed = 0
for p in ROOT.rglob("*.html"):
    if any(seg in p.parts for seg in ("i18n", "qa", "tmp")):
        continue
    raw = p.read_text(encoding="utf-8")
    original = raw
    for pat in SEARCH_NAV_PATTERNS:
        raw = raw.replace(pat, "", 1)
    if raw != original:
        p.write_text(raw, encoding="utf-8", newline="")
        total_removed += 1
print(f"  Removed search nav link from {total_removed} HTML files")

print("\n=== Done ===")
