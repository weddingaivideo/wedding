#!/usr/bin/env python3
"""
v3.8.0 (round 2) — Add trailing slashes to internal href values.

The previous migration only handled `.html` references; after v3.6.0 the
internal links were `/about` (no extension, no slash). Pages still 308s
on `/about` even with the directory structure. We need the trailing slash.

Replaces href values for known internal pages with the trailing-slash form:
  href="about"          -> href="about/"
  href="/about"         -> href="/about/"
  href="services/X/Y"   -> href="services/X/Y/"
  href="/services/X/Y"  -> href="/services/X/Y/"

Also rewrites canonical / og:url / schema.org url/item/contentUrl/embedUrl
absolute URLs to the trailing-slash form on weddingai.video.
Also rewrites sitemap.xml <loc>, llms.txt, llms-full.txt, README.md, and
search.html JS INDEX array (same as the v3.6.0 strip script but produces
the slash form instead of the no-suffix form).

Idempotent.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
SKIP = {"google-site-verification.html"}

# Internal page paths (relative or absolute; without trailing slash)
PATHS = [
    "about", "gallery", "order", "privacy", "terms",
    "resources", "search", "success",
    "services",  # /services/ (directory)
    "services/video-enhancement/slow-motion",
    "services/absence-compensation/celebrity-message",
    "services/absence-compensation/family-message",
    "services/absence-compensation/family-tribute",
    "services/personalization/ai-video-generator",
    "services/personalization/cartoon-style",
    "services/personalization/meme-generator",
    "services/personalization/multilingual",
    "services/personalization/pet-wedding",
    "services/personalization/wedding-trailer",
]

# Build a regex that matches any of these paths as an href value
# (with optional leading slash), without trailing slash and without .html
# Examples: href="about", href="/about", href="services/X/Y", href="/services/X/Y"
# Excluded: href="mailto:...", href="#anchor", href="https://...", href="javascript:..."
QUOTED = "|".join(re.escape(p) for p in sorted(PATHS, key=len, reverse=True))
# Negative lookbehind: avoid matching if the char before is a quote
# (i.e. we're inside a different attribute). The href=" prefix already handles this.
# But we also need to make sure we don't double-slash: avoid "/about/" if already slashed.
HREF_RE = re.compile(
    rf'(href=")(/?)({QUOTED})(?=")'  # captures: prefix, slash?, path
)


def iter_html_files():
    for p in ROOT.rglob("*.html"):
        if p.name in SKIP:
            continue
        if "__pycache__" in p.parts or "scripts" in p.parts:
            continue
        yield p


def add_slash(text: str) -> tuple[str, int]:
    """Convert internal href values to trailing-slash form."""
    n = 0
    def sub(m):
        nonlocal n
        n += 1
        return f'{m.group(1)}{m.group(2)}{m.group(3)}/'
    new = HREF_RE.sub(sub, text)
    return new, n


def has_canonical_trailing_slash(text: str) -> bool:
    return '"https://weddingai.video/"' in text and '"https://weddingai.video//"' in text


# Schema/og:url rewrite to trailing-slash form
ABS_REWRITE_RE = re.compile(
    r'(href|content)="(https://weddingai\.video/[^"/]*?)([\?#"])'  # capture: attr, base, terminator
)


def add_slash_to_abs_urls(text: str) -> tuple[str, int]:
    """For weddingai.video absolute URLs, add trailing slash if missing.
    Only for paths that are internal page paths."""
    n = 0

    def sub(m):
        nonlocal n
        attr, base, term = m.group(1), m.group(2), m.group(3)
        # base looks like "https://weddingai.video/about" or "https://weddingai.video"
        path = base.replace("https://weddingai.video", "")
        if path in ("", "/"):
            n += 1
            return f'{attr}="{base}/"' if path == "" else f'{attr}="{base}{term}'
        if path in PATHS or path.startswith("services/"):
            n += 1
            return f'{attr}="{base}/{term}'
        return m.group(0)

    return ABS_REWRITE_RE.sub(sub, text), n


SCHEMA_URL_RE = re.compile(
    r'"(?P<key>url|item|contentUrl|embedUrl)"\s*:\s*"(?P<url>https://weddingai\.video/[^"]*?)(?P<term>["])"'
)


def add_slash_to_schema_urls(text: str) -> tuple[str, int]:
    n = 0

    def sub(m):
        nonlocal n
        key, url, term = m.group("key"), m.group("url"), m.group("term")
        path = url.replace("https://weddingai.video", "")
        if path in ("", "/"):
            return m.group(0)
        if path in PATHS or path.startswith("services/"):
            n += 1
            return f'"{key}": "{url}/{term}"'
        return m.group(0)

    return SCHEMA_URL_RE.sub(sub, text), n


JS_URL_RE = re.compile(
    r'(url\s*:\s*")(/[^"]*?)(?P<term>["])'
)


def add_slash_to_js_urls(text: str) -> tuple[str, int]:
    n = 0

    def sub(m):
        nonlocal n
        prefix, url, term = m.group(1), m.group(2), m.group("term")
        path = url
        # /about -> /about/, /services/X/Y -> /services/X/Y/
        if path == "/" or path.endswith("/"):
            return m.group(0)
        if path.lstrip("/") in PATHS or any(path.lstrip("/").startswith(p) for p in ["services/"]):
            if "." not in path.split("/")[-1]:  # no extension
                n += 1
                return f'{prefix}{url}/{term}'
        return m.group(0)

    return JS_URL_RE.sub(sub, text), n


SITEMAP_LOC_RE = re.compile(
    r'<loc>(?P<url>https://weddingai\.video/[^<]+?)(?P<slash>/?)(</loc>)'
)


def rewrite_sitemap() -> int:
    p = ROOT / "sitemap.xml"
    if not p.exists():
        return 0
    text = p.read_text(encoding="utf-8")
    n = 0

    def sub(m):
        nonlocal n
        url, slash, end = m.group("url"), m.group("slash"), m.group(3)
        path = url.replace("https://weddingai.video", "")
        if path in ("", "/"):
            n += 1
            return f"<loc>{url}/</loc>" if not slash else m.group(0)
        if path in PATHS or path.startswith("services/"):
            if not slash:
                n += 1
                return f"<loc>{url}/</loc>"
        return m.group(0)

    new = SITEMAP_LOC_RE.sub(sub, text)
    if n:
        p.write_text(new, encoding="utf-8")
    return n


MD_LINKS_RE = re.compile(
    r'(\]\()(https://weddingai\.video/[^)]*?)(?P<slash>/?)(\))'
)


def rewrite_llms() -> int:
    total = 0
    for name in ("llms.txt", "llms-full.txt"):
        p = ROOT / name
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        n = 0

        def sub(m):
            nonlocal n
            prefix, url, slash, end = m.group(1), m.group(2), m.group("slash"), m.group(4)
            path = url.replace("https://weddingai.video", "")
            if path in ("", "/"):
                if not slash:
                    n += 1
                    return f"{prefix}{url}/{end}"
                return m.group(0)
            if path in PATHS or path.startswith("services/"):
                if not slash:
                    n += 1
                    return f"{prefix}{url}/{end}"
            return m.group(0)

        new = MD_LINKS_RE.sub(sub, text)
        if n:
            p.write_text(new, encoding="utf-8")
        total += n
    return total


README_RE = re.compile(
    r'(https://weddingai\.video/[\w\-/\.]*?)(?P<slash>/?)(?=[\s\)\,\'"]|$)'
)


def rewrite_readme() -> int:
    p = ROOT / "README.md"
    if not p.exists():
        return 0
    text = p.read_text(encoding="utf-8")
    n = 0

    def sub(m):
        nonlocal n
        url, slash = m.group(1), m.group("slash")
        path = url.replace("https://weddingai.video", "")
        if path in ("", "/"):
            if not slash:
                n += 1
                return f"{url}/"
            return m.group(0)
        # Make sure not to double-slash URLs that are partial
        if path in PATHS or path.startswith("services/"):
            if not slash and not path.endswith("/"):
                # Only add slash if the URL isn't already at end of text
                n += 1
                return f"{url}/"
        return m.group(0)

    new = README_RE.sub(sub, text)
    if n:
        p.write_text(new, encoding="utf-8")
    return n


def main():
    print("=" * 60)
    print("v3.8.0 trailing-slash migration (round 2)")
    print("=" * 60)

    total_h = 0
    total_abs = 0
    total_schema = 0
    total_js = 0
    file_count = 0

    for p in iter_html_files():
        text = p.read_text(encoding="utf-8")
        original = text
        text, n = add_slash(text)
        total_h += n
        text, n = add_slash_to_abs_urls(text)
        total_abs += n
        text, n = add_slash_to_schema_urls(text)
        total_schema += n
        text, n = add_slash_to_js_urls(text)
        total_js += n
        if text != original:
            p.write_text(text, encoding="utf-8")
            file_count += 1

    print(f"\n[1/5] HTML files: {file_count} updated")
    print(f"  href trailing-slash:    {total_h}")
    print(f"  absolute URL trailing:  {total_abs}")
    print(f"  schema URL trailing:    {total_schema}")
    print(f"  JS INDEX url trailing:  {total_js}")

    n = rewrite_sitemap()
    print(f"\n[2/5] sitemap.xml: {n} entries updated")

    n = rewrite_llms()
    print(f"[3/5] llms.txt + llms-full.txt: {n} links updated")

    n = rewrite_readme()
    print(f"[4/5] README.md: {n} URLs updated")

    print("\nDone. Re-running is a no-op.")
    print("Run 'pre-deploy-check' and deploy.")


if __name__ == "__main__":
    main()
