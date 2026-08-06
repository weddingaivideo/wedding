"""
Inject hero + inline images into blog article HTML.

Idempotent — skips files that already have the hero image.

Layout per article:
  - page-hero (kept)
  - <picture class="blog-hero"> (NEW: hero image right after page-hero, before body)
  - <div class="blog-article">
      - first paragraph
      - inline-1 <figure> (NEW)
      - <h2> ... </h2>
      - inline-2 <figure> (NEW)
      - ... rest of body ...
      - inline-5 <figure> (NEW, after last paragraph)

The inline images are placed roughly at: after the 1st paragraph, after the
2nd H2, after the 4th H2, after the 6th H2, and at the end of the body.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"
PROMPTS = json.loads((ROOT / "scripts" / "blog-image-prompts.json").read_text(encoding="utf-8"))


def has_hero(html: str) -> bool:
    return 'class="blog-hero"' in html


def has_inline(html: str) -> bool:
    return 'class="inline-figure"' in html


def hero_block(slug: str, alt: str) -> str:
    return f"""        <figure class="blog-hero">
            <img src="/images/blog/hero/{slug}.jpg" alt="{alt}" loading="eager" width="1280" height="720" />
        </figure>
"""


def inline_block(filename: str, alt: str) -> str:
    return f"""        <figure class="inline-figure">
            <img src="/{filename}" alt="{alt}" loading="lazy" width="1280" height="720" />
        </figure>
"""


def inject_hero(html: str, slug: str, alt: str) -> str:
    if has_hero(html):
        return html
    # Insert right after the page-hero section close, before the <div class="container blog-article">
    block = hero_block(slug, alt)
    # Use the page-hero section as anchor
    pat = re.compile(r'(</section>\s*<section class="section" style="background: var\(--color-white\);">)', re.DOTALL)
    m = pat.search(html)
    if not m:
        # Fallback: insert before blog-article
        m2 = re.search(r'(<div class="container blog-article")', html)
        if not m2:
            return html
        return html[: m2.start()] + "    " + block + "\n" + html[m2.start():]
    return html[: m.end()] + "\n" + block + html[m.end():]


def inject_inline(html: str, slug: str) -> str:
    if has_inline(html):
        return html
    entry = PROMPTS.get(slug)
    if not entry:
        return html
    inlines = entry["inline"]
    if len(inlines) < 5:
        return html

    # Find the body
    m = re.search(r'<div class="container blog-article"[^>]*>', html)
    if not m:
        return html
    body_start = m.end()
    # Find the end of the body
    body_end_m = re.search(r'</div>\s*</div>\s*</section>', html[body_start:])
    if not body_end_m:
        return html
    body_end = body_start + body_end_m.start()
    body = html[body_start:body_end]

    # Insertion plan: place 5 figures at positions
    # 0: after first <p>
    # 1-4: after 2nd/4th/6th/8th <h2>
    # (or end if not enough h2s)
    insertions: list[tuple[int, str]] = []

    # First: find first <p>
    p_m = re.search(r"<p>.*?</p>", body, re.DOTALL)
    if p_m:
        insertions.append((p_m.end(), inline_block(inlines[0]["filename"], inlines[0]["alt"])))

    # H2 positions
    h2_positions = [m.start() for m in re.finditer(r"<h2>.*?</h2>", body, re.DOTALL)]
    # Insert after 2nd, 4th, 6th, 8th h2 (indices 1,3,5,7)
    h2_targets = [1, 3, 5, 7]
    inline_idx = 1
    for h2i in h2_targets:
        if inline_idx >= 5:
            break
        if h2i < len(h2_positions):
            # Find end of h2 block (closing h2 + any immediate <p> after?)
            # Just insert right after the h2 tag close for simplicity
            h2_end_m = re.search(r"<h2>.*?</h2>", body[h2_positions[h2i]:], re.DOTALL)
            if h2_end_m:
                pos = h2_positions[h2i] + h2_end_m.end()
                insertions.append((pos, inline_block(inlines[inline_idx]["filename"], inlines[inline_idx]["alt"])))
                inline_idx += 1

    # If we still have unfilled inlines, append at end
    while inline_idx < 5:
        insertions.append((len(body), inline_block(inlines[inline_idx]["filename"], inlines[inline_idx]["alt"])))
        inline_idx += 1

    # Sort insertions by position descending so we don't shift indexes
    insertions.sort(key=lambda x: -x[0])
    new_body = body
    for pos, block in insertions:
        new_body = new_body[:pos] + "\n" + block + new_body[pos:]

    return html[:body_start] + new_body + html[body_end:]


def main() -> int:
    n_hero = 0
    n_inline = 0
    for art_dir in sorted(BLOG.iterdir()):
        if not art_dir.is_dir():
            continue
        slug = art_dir.name
        html_path = art_dir / "index.html"
        if not html_path.exists():
            continue
        html = html_path.read_text(encoding="utf-8")
        entry = PROMPTS.get(slug)
        if not entry:
            continue
        new_html = html
        if not has_hero(new_html):
            new_html = inject_hero(new_html, slug, entry["hero"]["alt"])
            n_hero += 1
        if not has_inline(new_html):
            new_html = inject_inline(new_html, slug)
            n_inline += 1
        if new_html != html:
            html_path.write_text(new_html, encoding="utf-8")
            print(f"[ok] {slug}: hero+inline injected")
    print(f"\nDone. hero injections: {n_hero}, inline injections: {n_inline}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
