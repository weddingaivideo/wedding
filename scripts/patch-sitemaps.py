"""
Add 3 new parent category URLs to all 10 sitemaps:
  /services/video-enhancement/
  /services/absence-compensation/
  /services/personalization/

Each sitemap entry has 11 hreflang alternates (10 langs + x-default) following
the same shape as the existing /services/ entry. Insertion order matches the
existing sitemap flow: each parent goes immediately before its first child.
"""
from pathlib import Path

ROOT = Path(".")

# (slug, parent_loc_suffix) — same in every language sitemap
PARENT_SLUGS = ["video-enhancement", "absence-compensation", "personalization"]

# 10 language codes matching the existing sitemap structure
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th"]


def url_entry(slug: str) -> str:
    """Render the <url> block for a parent category in the en sitemap. Other
    langs differ only in the hreflang values (which are language-agnostic in
    the sitemap — they always list all 10 langs)."""
    hreflang_lines = "\n".join(
        f'        <xhtml:link rel="alternate" hreflang="{code}" '
        f'href="https://weddingai.video/{code}/services/{slug}/"/>'
        for code in LANGS
    )
    return f"""    <url>
        <loc>https://weddingai.video/services/{slug}/</loc>
        <lastmod>2026-08-04</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
        {hreflang_lines}
        <xhtml:link rel="alternate" hreflang="x-default" href="https://weddingai.video/services/{slug}/"/>
        <image:image>
            <image:loc>https://weddingai.video/images/hero-wedding-vineyard.webp</image:loc>
            <image:title>WeddingAI.video &#8212; AI-powered wedding video services</image:title>
        </image:image>
    </url>"""


def patch_sitemap(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    # Detect the language prefix: sitemap-en.xml uses /services/... (no prefix
    # since en is canonical), sitemap-zh.xml uses /zh/services/..., etc. The
    # filename pattern is "sitemap-{lang}.xml" → prefix = "/{lang}/" for
    # non-en, "" for en. The x-default entry however is always /services/.../
    # regardless of the lang (per existing sitemap convention).
    lang = path.stem.replace("sitemap-", "")
    url_prefix = "" if lang == "en" else f"/{lang}"

    inserted = 0
    for slug in PARENT_SLUGS:
        # Skip if already present.
        loc_check = f'<loc>https://weddingai.video{url_prefix}/services/{slug}/</loc>'
        if loc_check in text:
            continue
        first_child = f'<loc>https://weddingai.video{url_prefix}/services/{slug}/'
        idx = text.find(first_child)
        if idx < 0:
            print(f"  [WARN] {path.name}: no children found for {slug}, skipping")
            continue
        # Backtrack to start of the <url> block (4-space indent + '    <url>')
        url_start = text.rfind("    <url>", 0, idx)
        # Build the entry in this language's namespace
        hreflang_lines = "\n".join(
            f'        <xhtml:link rel="alternate" hreflang="{code}" '
            f'href="https://weddingai.video/{code}/services/{slug}/"/>'
            for code in LANGS
        )
        new_entry = f"""    <url>
        <loc>https://weddingai.video{url_prefix}/services/{slug}/</loc>
        <lastmod>2026-08-04</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
        {hreflang_lines}
        <xhtml:link rel="alternate" hreflang="x-default" href="https://weddingai.video/services/{slug}/"/>
        <image:image>
            <image:loc>https://weddingai.video/images/hero-wedding-vineyard.webp</image:loc>
            <image:title>WeddingAI.video &#8212; AI-powered wedding video services</image:title>
        </image:image>
    </url>"""
        new_text = text[:url_start] + new_entry + "\n" + text[url_start:]
        text = new_text
        inserted += 1
    if inserted:
        path.write_text(text, encoding="utf-8")
    return inserted


def main() -> int:
    sitemaps = sorted(ROOT.glob("sitemap-*.xml"))
    for sm in sitemaps:
        n = patch_sitemap(sm)
        print(f"  {sm.name}: inserted {n} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
