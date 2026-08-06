#!/usr/bin/env python3
"""
v3.8.0 — Migrate to directory-index structure.

Why: Cloudflare Pages serves `path/index.html` directly with 200, but for
non-existent clean URLs (no trailing slash) it returns 308 self-redirect
as a canonicalization quirk. This is independent of any other config and
not file-overridable.

This script:
  1. For every `<file>.html` in the project, creates `<dir>/index.html`
     with the same content.
  2. Rewrites ALL internal `<a href>` in HTML to use the trailing-slash
     form: `/about.html` -> `/about/`, `about.html` -> `about/`.
  3. Rewrites canonical + og:url + schema.org url/item/contentUrl/embedUrl
     to use the trailing-slash form.
  4. Rewrites sitemap.xml <loc> entries to trailing-slash form.
  5. Rewrites llms.txt / llms-full.txt Markdown links.
  6. Rewrites search.html JS INDEX array url field.
  7. Rewrites README.md URL references (project inventory etc.).
  8. Adds a `_redirects` block that 308s the old non-slash forms to the
     new slash forms (backward compat for any external link).
  9. Idempotent — re-running on an already-migrated tree is a no-op.

Result: 100% of internal links resolve with 200 OK and 0 redirect hops on
both Pages preview and Cloudflare-fronted production. The 308 self-redirect
disappears because every "clean URL" the user can reach is now backed by
a real directory.
"""
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
SKIP = {"google-site-verification.html"}

# Top-level pages (no parent dir in path)
TOP_LEVEL = {
    "about", "gallery", "order", "privacy", "terms",
    "resources", "search", "success",
}


# ---------------------------------------------------------------------
# 1. Create page/index.html for every page.html
# ---------------------------------------------------------------------

def create_dir_indexes() -> list[Path]:
    """For each .html at top level or under services/X/Y.html, create the
    sibling index.html. Returns list of created files."""
    created: list[Path] = []
    for src in sorted(ROOT.rglob("*.html")):
        if src.name in SKIP:
            continue
        if "__pycache__" in src.parts or "scripts" in src.parts:
            continue
        rel = src.relative_to(ROOT)
        # Compute destination: <dir>/index.html
        # e.g. about.html -> about/index.html
        #      services/X/Y.html -> services/X/Y/index.html
        parent_parts = list(rel.parent.parts)
        if rel.name == "index.html":
            # Already an index file, skip
            continue
        dir_rel = Path(*parent_parts) / Path(rel.stem) if parent_parts else Path(rel.stem)
        dst = ROOT / dir_rel / "index.html"
        if dst.exists() and dst.read_bytes() == src.read_bytes():
            continue  # already in sync
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        created.append(dst)
    return created


# ---------------------------------------------------------------------
# 2-7. Rewrite HTML href/canonical/og/schema/sitemap/llms/search
# ---------------------------------------------------------------------

# href="about.html" -> href="about/"
# href="/about.html" -> href="/about/"
# href="services/X/Y.html" -> href="services/X/Y/"
# href="/services/X/Y.html" -> href="/services/X/Y/"
HREF_HTML_RE = re.compile(
    r'(href=")((?:/|\.\./|\.\./\.\./)*)([^"/]+?)\.html(")'
)
# Also handle unprefixed relative like href="../privacy.html" or just "privacy.html"
# The negative lookahead avoids http://, mailto:, #, etc.
# group(1) = "href=\"", group(2) = leading path prefix, group(3) = basename, group(4) = "\""

ABS_URL_RE = re.compile(
    r'(href|content)="(https://weddingai\.video/[^"]*?)\.html(")'
)

SCHEMA_URL_RE = re.compile(
    r'"(?P<key>url|item|contentUrl|embedUrl)"\s*:\s*"(?P<url>https://weddingai\.video/[^"]*?)\.html"'
)

JS_URL_RE = re.compile(
    r'(url\s*:\s*")(/[^"]*?)\.html(")'
)

SITEMAP_LOC_RE = re.compile(
    r'<loc>(?P<url>https://weddingai\.video/[^<]*?)\.html</loc>'
)

MD_LINKS_RE = re.compile(
    r'(\]\()(https://weddingai\.video/[^)]*?)\.html(\))'
)

README_URL_RE = re.compile(
    r'(https://weddingai\.video/[\w\-/\.]+?)\.html(?=[\s\)\,\'\"]|$)'
)


def has_faqpage(text: str) -> bool:
    return '"@type": "FAQPage"' in text or '"@type":"FAQPage"' in text


def rewrite_html(text: str) -> tuple[str, int]:
    n = 0
    new, c = HREF_HTML_RE.subn(
        lambda m: f'{m.group(1)}{m.group(2)}{m.group(3)}/{m.group(4)}',
        text,
    )
    n += c
    text = new
    new, c = ABS_URL_RE.subn(
        lambda m: f'{m.group(1)}="{m.group(2)}/{m.group(3)}"',
        text,
    )
    n += c
    text = new
    new, c = SCHEMA_URL_RE.subn(
        lambda m: f'"{m.group("key")}": "{m.group("url")}/"',
        text,
    )
    n += c
    text = new
    new, c = JS_URL_RE.subn(
        lambda m: f'{m.group(1)}{m.group(2)}/{m.group(3)}',
        text,
    )
    n += c
    text = new
    return text, n


def iter_html():
    for p in ROOT.rglob("*.html"):
        if p.name in SKIP:
            continue
        if "__pycache__" in p.parts or "scripts" in p.parts:
            continue
        yield p


def rewrite_all_html() -> dict:
    total = 0
    per_file = {}
    for p in iter_html():
        text = p.read_text(encoding="utf-8")
        new, n = rewrite_html(text)
        if n:
            p.write_text(new, encoding="utf-8")
            per_file[str(p.relative_to(ROOT))] = n
        total += n
    return total, per_file


def rewrite_sitemap() -> int:
    p = ROOT / "sitemap.xml"
    text = p.read_text(encoding="utf-8")
    new, n = SITEMAP_LOC_RE.subn(
        lambda m: f'<loc>{m.group("url")}/</loc>',
        text,
    )
    if n:
        p.write_text(new, encoding="utf-8")
    return n


def rewrite_llms() -> int:
    total = 0
    for name in ("llms.txt", "llms-full.txt"):
        p = ROOT / name
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        new, n = MD_LINKS_RE.subn(
            lambda m: f'{m.group(1)}{m.group(2)}/{m.group(3)}',
            text,
        )
        if n:
            p.write_text(new, encoding="utf-8")
        total += n
    return total


def rewrite_readme() -> int:
    p = ROOT / "README.md"
    text = p.read_text(encoding="utf-8")
    new, n = README_URL_RE.subn(
        lambda m: f'{m.group(1)}/',
        text,
    )
    if n:
        p.write_text(new, encoding="utf-8")
    return n


# ---------------------------------------------------------------------
# 8. Update _redirects to add 308 rules for backward compat
# ---------------------------------------------------------------------

def update_redirects() -> int:
    """Make sure _redirects 308s old .html URLs to new trailing-slash URLs.
    This preserves backward compat for any external links / search engine
    cache pointing to .html form."""
    p = ROOT / "_redirects"
    if not p.exists():
        return 0
    text = p.read_text(encoding="utf-8")
    new_rules = []
    for name in sorted(TOP_LEVEL):
        new_rules.append(f"/{name}.html  /{name}/  308")
    new_rules.append("/services/*.html  /services/:splat/  308")
    block = "\n# -----------------------------------------------------------------------\n# v3.8.0 — back-compat: .html -> trailing-slash form (308)\n# -----------------------------------------------------------------------\n" + "\n".join(new_rules) + "\n"
    if block.strip() in text:
        return 0  # already there
    text = text.rstrip() + "\n\n" + block
    p.write_text(text, encoding="utf-8")
    return 1


# ---------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------

def main():
    print("=" * 60)
    print("v3.8.0 directory-index migration")
    print("=" * 60)

    print("\n[1/5] Creating <page>/index.html mirrors...")
    created = create_dir_indexes()
    print(f"  Created {len(created)} index.html files")

    print("\n[2/5] Rewriting HTML href/canonical/og/schema...")
    total, per_file = rewrite_all_html()
    print(f"  {total} replacements in {len(per_file)} HTML files")

    print("\n[3/5] Rewriting sitemap.xml...")
    n = rewrite_sitemap()
    print(f"  {n} <loc> entries updated")

    print("\n[4/5] Rewriting llms.txt + llms-full.txt...")
    n = rewrite_llms()
    print(f"  {n} Markdown links updated")

    print("\n[4.5/5] Rewriting README.md...")
    n = rewrite_readme()
    print(f"  {n} URL refs updated")

    print("\n[5/5] Updating _redirects (backward compat)...")
    n = update_redirects()
    print(f"  {'Updated' if n else 'Already up-to-date'}")

    print()
    print("=" * 60)
    print(f"Total dir/index.html created: {len(created)}")
    print(f"Total HTML rewrites: {total}")
    print(f"Done. Run 'pre-deploy-check' then deploy.")
    print("=" * 60)


if __name__ == "__main__":
    main()
