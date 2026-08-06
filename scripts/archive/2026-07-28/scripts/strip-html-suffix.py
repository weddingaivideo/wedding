#!/usr/bin/env python3
"""
One-shot script: strip `.html` suffix from all internal links across the
WeddingAI.video project so every internal navigation uses clean URLs.

Why: previously, every internal <a href> pointed to a .html file, and the
server returned 308 from .html to no-suffix form. That wasted one HTTP
round-trip per navigation and burned crawl budget. After this script,
all internal links use clean URLs directly.

Scope of changes:
  - HTML files: <a href>, <link rel="canonical">, <meta property="og:url">,
                and Schema.org JSON-LD url/item/contentUrl/embedUrl fields
  - sitemap.xml: <loc> entries
  - llms.txt / llms-full.txt: any (https://weddingai.video/X.html) link
  - search.html: client-side INDEX array url field
  - functions/api/quote.js: SUCCESS_PATH (form -> thank-you)
  - scripts/generate-sitemap.py: url_for() so future sitemap runs are clean
  - netlify.toml: 308 backward-compat rules (legacy)
  - README.md: page inventory and sample URLs

Does NOT touch:
  - External URLs (weddingai.video is the only domain rewritten)
  - Non-HTML resources (.xml, .txt, .json, .svg, .png, .jpg, .webp, .avif, .js, .css, .ico, .gz)
  - google-site-verification.html (Google verification file)
  - Image src paths
  - Mailto: links
  - API endpoints (/api/quote)
  - /search?q=... (form action already clean)
  - /services/  (already clean — directory index)

Idempotent: safe to re-run.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")

# Pages whose `.html` is part of the filename and must NEVER be rewritten
SKIP_FILES = {"google-site-verification.html"}

# Filenames (without directory) to skip entirely
SKIP_FILENAMES = SKIP_FILES

# HTML files to scan
def iter_html_files():
    for p in ROOT.rglob("*.html"):
        if p.name in SKIP_FILENAMES:
            continue
        if "__pycache__" in p.parts:
            continue
        yield p


# ----------------------------------------------------------------------------
# Regexes for the various places `.html` shows up
# ----------------------------------------------------------------------------

# 1. href="X.html" / href="/X.html" / href="../../X.html" / href="services/X.html"
#    (internal navigation, not external — no protocol, no domain)
HREF_HTML = re.compile(
    r'(href=")(?!https?://|#|mailto:|tel:|/api/)([^"]*?)\.html(")'
)

# 2. Canonical / og:url / twitter:url — full absolute URLs on weddingai.video
ABS_HTML = re.compile(
    r'(href|content)="(https://weddingai\.video/[^"]*?)\.html(")'
)

# 3. Schema.org JSON-LD string values inside "...": "url" / "item" / "contentUrl" / "embedUrl"
#    Match: "url": "https://weddingai.video/X.html"  or  "item": "https://weddingai.video/X.html"
SCHEMA_URL = re.compile(
    r'"(?P<key>url|item|contentUrl|embedUrl)"\s*:\s*"(?P<url>https://weddingai\.video/[^"]*?)\.html"'
)

# 4. llms.txt/llms-full.txt: Markdown links [text](https://weddingai.video/X.html)
MD_LINKS = re.compile(
    r'(\]\()(https://weddingai\.video/[^)]*?)\.html(\))'
)

# 5. sitemap.xml <loc> entries
SITEMAP_LOC = re.compile(
    r'<loc>(?P<url>https://weddingai\.video/[^<]*?)\.html</loc>'
)

# 6. JS object literal: url: "/X.html" (search.html INDEX array, etc.)
JS_URL = re.compile(
    r'(url\s*:\s*")(/[^"]*?)\.html(")'
)


def strip_href(match):
    prefix, path, suffix = match.group(1), match.group(2), match.group(3)
    return f'{prefix}{path}{suffix}'


def strip_abs(match):
    attr, url, suffix = match.group(1), match.group(2), match.group(3)
    return f'{attr}="{url}{suffix}"'


def strip_schema(match):
    return f'"{match.group("key")}": "{match.group("url")}"'


def process_html(path: Path) -> tuple[int, str]:
    """Rewrite all internal .html references in a single HTML file."""
    text = path.read_text(encoding="utf-8")
    original = text
    n = 0

    # href="X.html" — but ONLY if X is a real path (not in a script, comment, etc.)
    # Strategy: only match href="..." where the value is a relative or site-rooted
    # path ending in .html. The regex already excludes http(s):// and other schemes.
    new_text, count = HREF_HTML.subn(strip_href, text)
    n += count
    text = new_text

    # canonical / og:url / twitter:url with absolute URL
    new_text, count = ABS_HTML.subn(strip_abs, text)
    n += count
    text = new_text

    # Schema.org JSON-LD
    new_text, count = SCHEMA_URL.subn(strip_schema, text)
    n += count
    text = new_text

    # JavaScript object literal: url: "/X.html"  (used in search.html INDEX)
    new_text, count = JS_URL.subn(
        lambda m: f'{m.group(1)}{m.group(2)}{m.group(3)}',
        text,
    )
    n += count
    text = new_text

    if text != original:
        path.write_text(text, encoding="utf-8")
    return n, text


def process_text_file(path: Path) -> int:
    """Rewrite .html references in plain-text files (sitemap, llms)."""
    text = path.read_text(encoding="utf-8")
    original = text
    n = 0

    if path.name == "sitemap.xml":
        text, n = SITEMAP_LOC.subn(
            lambda m: f'<loc>{m.group("url")}</loc>',
            text,
        )
    else:
        text, n = MD_LINKS.subn(
            lambda m: f'{m.group(1)}{m.group(2)}{m.group(3)}',
            text,
        )

    if text != original:
        path.write_text(text, encoding="utf-8")
    return n


def update_quote_js() -> int:
    p = ROOT / "functions" / "api" / "quote.js"
    text = p.read_text(encoding="utf-8")
    new = text.replace('const SUCCESS_PATH = "/success.html";',
                       'const SUCCESS_PATH = "/success";')
    if new != text:
        p.write_text(new, encoding="utf-8")
        return 1
    return 0


def update_generate_sitemap() -> int:
    p = ROOT / "scripts" / "generate-sitemap.py"
    text = p.read_text(encoding="utf-8")
    # url_for: also strip `.html` for non-index top-level files
    old = '''def url_for(rel):
    """Convert 'services/index.html' to 'services/' and 'index.html' to '/'."""
    if rel == "index.html":
        return f"{BASE_URL}/"
    if rel.endswith("/index.html"):
        return f"{BASE_URL}/{rel[:-10]}"  # strip 'index.html'
    return f"{BASE_URL}/{rel}"'''
    new = '''def url_for(rel):
    """Convert 'X.html' -> 'X', 'services/index.html' -> 'services/', 'index.html' -> '/'."""
    if rel == "index.html":
        return f"{BASE_URL}/"
    if rel.endswith("/index.html"):
        return f"{BASE_URL}/{rel[:-10]}"  # strip 'index.html'
    if rel.endswith(".html"):
        return f"{BASE_URL}/{rel[:-5]}"  # strip '.html' (clean URL — no server redirect)
    return f"{BASE_URL}/{rel}"'''
    if old in text:
        text = text.replace(old, new)
        p.write_text(text, encoding="utf-8")
        return 1
    return 0


def update_netlify_toml() -> int:
    """Replace existing clean->.html rules with .html->clean rules, so the file
    matches the new strategy and works if the project ever moves back to Netlify."""
    p = ROOT / "netlify.toml"
    text = p.read_text(encoding="utf-8")
    original = text

    # Replace the /services/* -> .html rules with the inverse
    text = text.replace(
        '''# Append .html to any extensionless URL (single wildcard covers all service pages)
# Note: only the FIRST matching rule wins, so this is more specific than the above.
[[redirects]]
  from = "/services/*"
  to = "/services/:splat.html"
  status = 301
  force = false''',
        '''# Remove .html suffix from any URL ending in .html (single wildcard covers all service pages).
# Result: /services/slow-motion.html -> /services/slow-motion (308, no caching by intermediaries).
# Internal links are already clean; this is a backward-compat safety net for external links.
[[redirects]]
  from = "/services/*.html"
  to = "/services/:splat"
  status = 308
  force = false'''
    )

    # Replace /services -> /services/index.html with /services/index.html -> /services
    text = text.replace(
        '''# /services (no trailing path) -> /services/index.html
[[redirects]]
  from = "/services"
  to = "/services/index.html"
  status = 301''',
        '''# /services/index.html -> /services (backward compat)
[[redirects]]
  from = "/services/index.html"
  to = "/services/"
  status = 308'''
    )

    # Replace /search -> /search.html with /search.html -> /search
    text = text.replace(
        '''# /search -> /search.html (for sitelinks searchbox)
[[redirects]]
  from = "/search"
  to = "/search.html"
  status = 301''',
        '''# /search.html -> /search (backward compat for any external .html links)
[[redirects]]
  from = "/search.html"
  to = "/search"
  status = 308'''
    )

    # Replace /success/ -> /success.html with /success.html -> /success/
    text = text.replace(
        '''# Form submission redirect (legacy URL from previous form setup)
[[redirects]]
  from = "/success/"
  to = "/success.html"
  status = 301''',
        '''# Form submission redirect — backward compat: /success.html -> /success/
# (current code redirects to /success from the form POST handler)
[[redirects]]
  from = "/success.html"
  to = "/success/"
  status = 308'''
    )

    # Add a wildcard catch-all: any top-level *.html -> no suffix
    # Placed after the more specific rules above
    new_block = '''# Catch-all: any remaining top-level *.html -> no-suffix form.
# (Specific rules above handle /services/, /search, /success; this covers
# /about.html, /gallery.html, /order.html, /privacy.html, /terms.html,
# /resources.html, /index.html stays as /)
[[redirects]]
  from = "/:page.html"
  to = "/:page"
  status = 308
  force = false

'''
    # Insert before the "Security Headers" section
    if "[[headers]]" in text and new_block.strip() not in text:
        text = text.replace("# =============================================\n# Security Headers",
                            new_block + "# =============================================\n# Security Headers")

    if text != original:
        p.write_text(text, encoding="utf-8")
        return 1
    return 0


def update_readme() -> int:
    p = ROOT / "README.md"
    text = p.read_text(encoding="utf-8")
    original = text

    # Update example URLs in the changelog and examples — only .html on weddingai.video
    text = re.sub(
        r'(https://weddingai\.video/[\w\-/\.]+?)\.html',
        r'\1',
        text,
    )

    if text != original:
        p.write_text(text, encoding="utf-8")
        return 1
    return 0


def add_changelog_entry() -> int:
    """Add v3.6.0 changelog line documenting this cleanup."""
    p = ROOT / "README.md"
    text = p.read_text(encoding="utf-8")
    if "Clean URL migration" in text:
        return 0  # already documented (use the stable phrase, not the version number)
    new_row = "| 2026-07-23 | v3.6.0 | **Clean URL migration** — stripped `.html` from all internal links (nav, footer, breadcrumbs, schema.org JSON-LD, sitemap, llms.txt, search index). Updated `netlify.toml` and `generate-sitemap.py` to emit and serve clean URLs. Each internal navigation now costs 1 HTTP round-trip instead of 2. |"
    text = text.replace(
        "| 2026-07-23 | v3.5.0 |",
        new_row + "\n| 2026-07-23 | v3.5.0 |"
    )
    p.write_text(text, encoding="utf-8")
    return 1


def main():
    total = 0
    print(f"Scanning HTML files in {ROOT}...")

    # 1. All HTML files
    for p in iter_html_files():
        n, _ = process_html(p)
        if n:
            print(f"  {p.relative_to(ROOT)}: {n} replacements")
        total += n

    # 2. sitemap.xml
    sm = ROOT / "sitemap.xml"
    if sm.exists():
        n = process_text_file(sm)
        if n:
            print(f"  sitemap.xml: {n} URL rewrites")
        total += n

    # 3. llms.txt and llms-full.txt
    for name in ("llms.txt", "llms-full.txt"):
        p = ROOT / name
        if p.exists():
            n = process_text_file(p)
            if n:
                print(f"  {name}: {n} link rewrites")
            total += n

    # 4. functions/api/quote.js
    n = update_quote_js()
    if n:
        print("  functions/api/quote.js: SUCCESS_PATH -> /success")
    total += n

    # 5. scripts/generate-sitemap.py
    n = update_generate_sitemap()
    if n:
        print("  scripts/generate-sitemap.py: url_for now strips .html")
    total += n

    # 6. netlify.toml
    n = update_netlify_toml()
    if n:
        print("  netlify.toml: rules inverted (backward-compat .html -> clean URL)")
    total += n

    # 7. README.md
    n = update_readme()
    if n:
        print("  README.md: sample URLs cleaned")
    total += n

    # 8. Changelog
    n = add_changelog_entry()
    if n:
        print("  README.md: changelog entry v3.6.0 added")
    total += n

    print(f"\nTotal replacements: {total}")
    print("Done. Run 'python scripts\\generate-sitemap.py' to regenerate sitemap if needed.")


if __name__ == "__main__":
    main()
