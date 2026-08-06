#!/usr/bin/env python3
"""
Add proper canonical + hreflang alternates for all 10 supported languages
to every HTML file.

For a page at /about/ (no lang prefix), the canonical should be /about/ (English)
and hreflang alternates point to /en/about/, /zh/about/, etc.

When the browser URL is /zh/about/ (after i18n rewrite), the served HTML
still has the English canonical, but the browser URL shows /zh/about/ which
Google indexes. The hreflang signals tell Google which URL is which language.
"""
import re
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
SITE_ORIGIN = "https://weddingai.video"
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th"]
DEFAULT_LANG = "en"

EXCLUDE_DIRS = {"admin", "functions", "tmp", "__pycache__", "qa", "i18n", "js", "styles", "scripts", "docs"}

def should_process(p):
    if p.name == "google-site-verification.html": return False
    return not (set(p.parts) & {Path(d) for d in EXCLUDE_DIRS})

def page_to_url_path(p: Path) -> str:
    """Convert file path to URL path (no lang prefix)."""
    rel = p.relative_to(ROOT)
    parts = list(rel.parts)
    if parts[-1] == "index.html":
        parts = parts[:-1]
    else:
        # e.g. about.html → /about
        last = parts[-1]
        if last.endswith(".html"):
            parts[-1] = last[:-5]
    if not parts:
        return "/"
    return "/" + "/".join(parts) + ("/" if not parts[-1].endswith(".html") and not parts[-1].endswith("/") else "")

def normalize_path(url_path: str) -> str:
    """Ensure trailing slash for directory-style URLs."""
    if not url_path.endswith("/") and "." not in url_path.split("/")[-1]:
        return url_path + "/"
    return url_path

def build_hreflang_block(rest):
    """Build the canonical + hreflang links block."""
    rest = normalize_path(rest)
    canonical = f'<link rel="canonical" href="{SITE_ORIGIN}{rest}">'
    alternates = []
    for lang in LANGS:
        if lang == DEFAULT_LANG:
            alt = f'{SITE_ORIGIN}{rest}'
        else:
            alt = f'{SITE_ORIGIN}/{lang}{rest}'
        alternates.append(f'<link rel="alternate" hreflang="{lang}" href="{alt}">')
    alternates.append(f'<link rel="alternate" hreflang="x-default" href="{SITE_ORIGIN}{rest}">')
    return canonical + "\n    " + "\n    ".join(alternates)

def fix_html_file(p: Path):
    text = p.read_text(encoding='utf-8', errors='ignore')
    # Compute the canonical URL path for this file
    url_path = page_to_url_path(p)
    url_path = normalize_path(url_path)
    new_block = build_hreflang_block(url_path)

    # Remove existing canonical and hreflang lines
    text = re.sub(r'<link\s+rel="canonical"\s+href="[^"]*"\s*>\n?\s*', '', text)
    text = re.sub(r'<link\s+rel="alternate"\s+hreflang="[^"]*"\s+href="[^"]*"\s*>\n?\s*', '', text, flags=re.IGNORECASE)

    # Insert new block after <title> or after <head>
    if '<title' in text:
        # Find end of <title>...</title>
        m = re.search(r'(</title>)', text)
        if m:
            text = text[:m.end()] + '\n    ' + new_block + text[m.end():]
    elif '<head>' in text:
        text = text.replace('<head>', '<head>\n    ' + new_block, 1)
    else:
        return text  # no head, skip

    p.write_text(text, encoding='utf-8')
    return new_block

total = 0
for p in sorted(ROOT.rglob("*.html")):
    if not should_process(p): continue
    fix_html_file(p)
    total += 1
print(f"Updated {total} HTML files with full hreflang + canonical")
