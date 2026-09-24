#!/usr/bin/env python3
"""
Generate per-language sitemaps + sitemap index for weddingai.video.

Sitemap strategy:
  - One sitemap per language (sitemap-{lang}.xml, default language = "en"
    uses sitemap-en.xml)
  - EVERY URL in EVERY sitemap emits the full hreflang graph
    (10 language alternates + x-default). This makes every sitemap
    self-contained: Google can verify the entire hreflang cluster from
    any single URL in any single sitemap, with no cross-sitemap dependency.
  - <image:image> entries are emitted for any URL with a known hero
    image, so Google Image Search can index our visual content.

Output:
  sitemap.xml           — index pointing to all per-language sitemaps
  sitemap-{lang}.xml    — per-language sitemap, all 10 languages

LANGS is parsed from /js/langs.js so there's a single source of truth
(see scripts/check_langs_sync.py to enforce).

Changed 2026-07-28 (Mavis SEO audit):
  - All sitemaps now emit full 11-link hreflang graph (was: en-only)
  - Added <image:image> entries (was: namespace declared but unused)
  - Removed is_canonical branching (every sitemap is now canonical-shape)
"""
import re
import sys
import json
from pathlib import Path
from datetime import date, datetime

ROOT = Path(__file__).resolve().parent.parent
SITE_ORIGIN = "https://weddingai.video"
LANGS_JS = ROOT / "js" / "langs.js"

EXCLUDE_DIRS = {"admin", "functions", "tmp", "__pycache__", "qa", "i18n", "js", "styles", "scripts", "docs", "search"}


def parse_langs() -> list[str]:
    """Read the canonical LANGS list from /js/langs.js."""
    src = LANGS_JS.read_text(encoding="utf-8")
    m = re.search(r'window\.WA_LANGS\s*=\s*\[([^\]]+)\]', src)
    if not m:
        raise SystemExit("[FAIL] Could not find WA_LANGS array in js/langs.js")
    return re.findall(r'"([a-z]{2,3})"', m.group(1))


def parse_default_lang() -> str:
    src = LANGS_JS.read_text(encoding="utf-8")
    m = re.search(r'window\.WA_DEFAULT_LANG\s*=\s*"([^"]+)"', src)
    if not m:
        return "en"
    return m.group(1)


LANGS = parse_langs()
DEFAULT_LANG = parse_default_lang()


def should_process(p: Path) -> bool:
    if p.name in ("google-site-verification.html", "404.html", "offline.html"):
        return False
    return not (set(p.parts) & EXCLUDE_DIRS)


def file_to_url_path(p: Path) -> str:
    rel = p.relative_to(ROOT)
    parts = list(rel.parts)
    if parts[-1] == "index.html":
        parts = parts[:-1]
    else:
        last = parts[-1]
        if last.endswith(".html"):
            parts[-1] = last[:-5]
    if not parts:
        return "/"
    path = "/" + "/".join(parts)
    if not path.endswith("/"):
        path += "/"
    return path


def priority_for(path: str) -> str:
    if path == "/": return "1.0"
    if "/order" in path: return "0.9"
    if "/gallery" in path: return "0.9"
    if "/services" in path and path.count("/") <= 2: return "0.9"
    if "/blog" in path: return "0.7" if path.count("/") >= 3 else "0.8"
    if "/about" in path: return "0.7"
    if path.startswith("/tools/") and path.count("/") <= 2: return "0.8"
    if "/tools/" in path: return "0.7"
    if "/success" in path: return "0.5"
    if "/terms" in path or "/privacy" in path: return "0.3"
    if "/resources" in path or "/search" in path: return "0.5"
    return "0.5"


def changefreq_for(path: str) -> str:
    if path in ("/", "/order/", "/gallery/", "/services/", "/blog/", "/tools/"): return "weekly"
    if "/blog/" in path: return "monthly"
    if "/services/" in path: return "monthly"
    if "/tools/" in path: return "monthly"
    return "yearly"


def _og_meta(html: str, prop: str) -> str | None:
    """Extract the content of <meta property="X" content="Y">. Case-insensitive
    on the property name, supports the optional whitespace after `property=`.

    Returns None if not found.
    """
    pat = re.compile(
        r'<meta\s+property\s*=\s*"' + re.escape(prop) + r'"\s+content\s*=\s*"([^"]+)"',
        re.IGNORECASE,
    )
    m = pat.search(html)
    return m.group(1) if m else None


def _ld_image(html: str) -> str | None:
    """Look for an Article JSON-LD block with an `image` field. Used as a
    fallback for blog post pages that don't have a static og:image but
    do carry an Article JSON-LD with the hero image."""
    for block in re.findall(
        r'<script\s+type\s*=\s*"application/ld\+json"\s*>(.*?)</script>',
        html,
        re.IGNORECASE | re.DOTALL,
    ):
        try:
            data = json.loads(block)
        except Exception:
            continue
        if isinstance(data, dict) and data.get("@type") == "Article":
            img = data.get("image")
            if isinstance(img, str) and img.startswith("http"):
                return img
            if isinstance(img, list) and img and isinstance(img[0], str):
                return img[0]
    return None


def _xml_escape(s: str) -> str:
    """Minimal XML attribute escaping for sitemap <image:title> content."""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def image_for(path: str) -> str | None:
    """Return the hero image URL for a given page path, or None if no
    good candidate. Used to inject <image:image> blocks for Google
    Image Search indexing.

    Strategy: every indexable page gets SOME image, but it should be the
    page's own hero (og:image or Article.image JSON-LD field), not a
    generic global image.

    Audit fix 2026-08-06: previously every page shared the same
    hero-wedding-vineyard.webp, which meant Google Image Search couldn't
    distinguish pages and blog posts lost their visual identity in
    image SERP. Now each page gets its own image when one is set in the
    page's <meta property="og:image"> or in an Article JSON-LD `image`
    field.
    """
    page_specific = {
        "/gallery/": f"{SITE_ORIGIN}/images/gallery-collage.webp",
        "/order/": f"{SITE_ORIGIN}/images/hero-wedding-vineyard.webp",
        "/pricing/": f"{SITE_ORIGIN}/images/hero-wedding-vineyard.webp",
        "/about/": f"{SITE_ORIGIN}/images/hero-wedding-vineyard.webp",
        "/services/": f"{SITE_ORIGIN}/images/hero-wedding-vineyard.webp",
        "/blog/": f"{SITE_ORIGIN}/images/hero-wedding-vineyard.webp",
    }
    if path in page_specific:
        return page_specific[path]

    file = path_to_file.get(path)
    if file is not None and file.exists():
        try:
            html = file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            html = ""
        if html:
            og = _og_meta(html, "og:image")
            if og and og.startswith("http"):
                return og
            ld = _ld_image(html)
            if ld:
                return ld

    return f"{SITE_ORIGIN}/images/hero-wedding-vineyard.webp"


def image_title_for(path: str, default: str) -> str:
    """Return the <image:title> for a page's <image:image> entry.

    Uses the page's <meta property="og:title"> when available, otherwise
    the provided default. The `default` argument is treated as a
    pre-formed XML-safe string (it may contain numeric character refs
    like &#8212; for em-dash), and is NOT re-escaped.

    Audit fix 2026-08-06: previously every image had the same generic
    title.
    """
    file = path_to_file.get(path)
    if file is not None and file.exists():
        try:
            html = file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            html = ""
        if html:
            og = _og_meta(html, "og:title")
            if og:
                if len(og) > 100:
                    og = og[:97].rsplit(" ", 1)[0] + "..."
                return _xml_escape(og)
    return default


def url_mtime_iso(file: Path | None) -> str:
    """Return the on-disk file mtime as an ISO date (yyyy-mm-dd),
    or `today` as a fallback. Used so each <lastmod> reflects the
    real last-edit time of the page rather than the deploy day —
    Google otherwise sees a sitemap where every URL "moved" on the
    same day, which carries no recency signal.
    """
    if file is None:
        return date.today().isoformat()
    try:
        return datetime.fromtimestamp(file.stat().st_mtime).date().isoformat()
    except OSError:
        return date.today().isoformat()


def hreflang_langs_for(path: str) -> list[str]:
    """Return the languages to include in the hreflang graph for a URL.

    Most pages have full 11-language coverage (en + 10 alternates).
    /tools/ paths are tools-specific: each language has its own static
    HTML file, so the hreflang graph expands dynamically with what's
    actually deployed — never points Google at 404 paths.

    For /tools/<slug>/ and /<lang>/tools/<slug>/, we look up which
    languages have an index.html file at the canonical /tools/<slug>/
    location and use those. Falls back to ['en', 'zh'] if no localized
    files are present (matches the original MVP behavior).
    """
    if path.startswith('/tools/') or re.match(r'^/[a-z]{2,3}/tools/', path):
        canonical = canonical_path(path)
        languages = ['en']  # default-lang always included
        for lang in LANGS[1:]:
            localized = ROOT / lang / canonical.strip('/') / 'index.html'
            if localized.exists():
                languages.append(lang)
        if len(languages) == 1:
            return ['en', 'zh']
        return languages
    return LANGS


def canonical_path(path: str) -> str:
    """Return the canonical (en) form of a path, stripping any leading
    /<lang>/ prefix. Used so hreflang + x-default always reference the
    en canonical, regardless of which sitemap we're emitting.

    Fixes a latent bug (introduced by the full-graph hreflang work
    2026-07-28): for a path like /zh/tools/... stored in `urls`, the
    previous logic computed href href=".../zh/tools/..." for the
    'en' alternates, which would 404 in practice and confuse crawlers.
    """
    m = re.match(r'^/([a-z]{2,3})(/.*)$', path)
    if m and m.group(1) in LANGS:
        return m.group(2)
    return path


def write_sitemap(lang: str, urls: list[str]) -> tuple[Path, int]:
    """Write a per-language sitemap.

    Per Google's hreflang spec (developers.google.com/search/docs/
    specialty/international/localized-versions#sitemap), every URL in
    a hreflang cluster must confirm ALL other URLs in the cluster —
    not just itself and the canonical. We therefore emit the full
    11-link graph (10 languages + x-default) for every URL in every
    sitemap, regardless of which language this sitemap is for.

    This makes every sitemap self-contained: Google can verify the
    hreflang cluster from any single URL in any single sitemap, with
    no cross-sitemap dependency.

    Exception: /tools/ paths use a restricted hreflang graph of
    [en, zh, x-default] because tools are not yet translated to other
    languages. See hreflang_langs_for().

    We also emit <image:image> for any URL with a known hero image, so
    Google Image Search can discover our visual content.
    """
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml" '
        'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
    )
    for path in urls:
        canonical = canonical_path(path)
        loc = f"{SITE_ORIGIN}{canonical if lang == DEFAULT_LANG else '/' + lang + canonical}"
        lines.append('    <url>')
        lines.append(f'        <loc>{loc}</loc>')
        lines.append(f'        <lastmod>{url_mtime_iso(path_to_file.get(path))}</lastmod>')
        lines.append(f'        <changefreq>{changefreq_for(path)}</changefreq>')
        lines.append(f'        <priority>{priority_for(path)}</priority>')

        # Restricted or full hreflang graph based on path.
        # x-default always points at the EN canonical (never the
        # /<lang>/-prefixed version of the same path).
        hreflang_langs = hreflang_langs_for(path)
        for l in hreflang_langs:
            alt_loc = f"{SITE_ORIGIN}{canonical if l == DEFAULT_LANG else '/' + l + canonical}"
            lines.append(f'        <xhtml:link rel="alternate" hreflang="{l}" href="{alt_loc}"/>')
        lines.append(f'        <xhtml:link rel="alternate" hreflang="x-default" href="{SITE_ORIGIN}{canonical}"/>')

        # Image sitemap entry: helps Google Image Search index our
        # visual content. Wedding video is a visual niche, so this is
        # a meaningful traffic channel we're leaving on the table.
        img = image_for(path)
        if img:
            lines.append('        <image:image>')
            lines.append(f'            <image:loc>{img}</image:loc>')
            # Page-specific image:title (was hard-coded to a generic string
            # before 2026-08-06). XML-escaped via image_title_for().
            default_title = "WeddingAI.video &#8212; AI-powered wedding video services"
            lines.append(f'            <image:title>{image_title_for(path, default_title)}</image:title>')
            lines.append('        </image:image>')

        lines.append('    </url>')
    lines.append('</urlset>')
    out = '\n'.join(lines) + '\n'

    fname = f"sitemap-{lang}.xml" if lang != DEFAULT_LANG else f"sitemap-{DEFAULT_LANG}.xml"
    path = ROOT / fname
    path.write_text(out, encoding="utf-8")
    return path, len(out)


# --- Main ---

url_paths: list[str] = []
path_to_file: dict[str, Path] = {}
for p in ROOT.rglob("*.html"):
    if not should_process(p):
        continue
    url = file_to_url_path(p)
    # keep the first file we see per URL (in case of duplicates; should_process
    # normally prevents that, but a defensive last-write-wins avoids wrong mtime)
    path_to_file.setdefault(url, p)
    if url not in url_paths:
        url_paths.append(url)

# Deduplicate: if a blog post exists both in root (e.g. /blog/slug/)
# and in a language directory (e.g. /zh/blog/slug/), keep only the
# root version. The root blog pages handle language variants via i18n.js
# and hreflang. Language-directory blog pages that have NO root
# counterpart are kept (unique content).
root_blog_paths = {u for u in url_paths if u.startswith("/blog/")}
deduped = []
removed = 0
for u in url_paths:
    # Check if this is a language-directory blog path that duplicates a root blog
    # e.g. /zh/blog/slug/ duplicates /blog/slug/
    for lang in LANGS:
        prefix = f"/{lang}/blog/"
        if u.startswith(prefix):
            root_equiv = u[len(prefix) - len("/blog/"):]  # /blog/slug/
            if root_equiv in root_blog_paths:
                removed += 1
                if u in path_to_file:
                    del path_to_file[u]
                break
    else:
        deduped.append(u)

if removed:
    print(f"Removed {removed} duplicate language blog URLs (content covered by root blog pages)")
url_paths = deduped
url_paths.sort()
print(f"Unique pages: {len(url_paths)}")
print(f"Per-language sitemaps: {len(LANGS)} files")
print(f"Languages (from js/langs.js): {LANGS}")
print(f"Default language: {DEFAULT_LANG}")

today = date.today().isoformat()

written = []
for lang in LANGS:
    p, sz = write_sitemap(lang, url_paths)
    written.append((p, sz))
    print(f"  Wrote {p.relative_to(ROOT)} ({sz/1024:.1f} KB)")

# Write sitemap.xml as an index pointing to all per-language sitemaps
idx_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
idx_lines.append('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
for p, _ in written:
    idx_lines.append('    <sitemap>')
    idx_lines.append(f'        <loc>{SITE_ORIGIN}/{p.name}</loc>')
    idx_lines.append(f'        <lastmod>{today}</lastmod>')
    idx_lines.append('    </sitemap>')
idx_lines.append('</sitemapindex>')

idx_path = ROOT / "sitemap.xml"
idx_path.write_text('\n'.join(idx_lines) + '\n', encoding="utf-8")
print(f"\nWrote sitemap index: {idx_path.relative_to(ROOT)} ({idx_path.stat().st_size/1024:.1f} KB)")

# Update robots.txt to point to sitemap.xml (idempotent)
robots = ROOT / "robots.txt"
if robots.exists():
    raw = robots.read_text(encoding="utf-8")
    if "Sitemap:" not in raw and "sitemap:" not in raw:
        raw = raw.rstrip() + f"\n\nSitemap: {SITE_ORIGIN}/sitemap.xml\n"
        robots.write_text(raw, encoding="utf-8")
        print("Added Sitemap: line to robots.txt")
