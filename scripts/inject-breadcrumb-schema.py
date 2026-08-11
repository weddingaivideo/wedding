#!/usr/bin/env python3
"""
inject-breadcrumb-schema.py

Add BreadcrumbList JSON-LD to every blog post (EN + 8 i18n languages).
Idempotent: skips files that already have a BreadcrumbList schema.

Blog post location: <root>/<lang>/blog/<slug>/index.html (lang='en' for /blog/)
BreadcrumbList is inserted right BEFORE the existing Article JSON-LD script
so the two schemas sit together; both are picked up by Google Rich Results.

Labels per language (Home / Blog):
    en Home/Blog  zh 首页/博客  es Inicio/Blog  fr Accueil/Blog
    de Startseite/Blog  pt Início/Blog  ja ホーム/ブログ
    ru Главная/Блог  ar الرئيسية/المدونة  th หน้าแรก/บล็อก

Usage: python inject-breadcrumb-schema.py [--root <path>] [--dry-run]
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

# Localized breadcrumb labels (Home, Blog) per language.
# Match the visible nav language where it exists; otherwise use a widely-accepted
# rendering. Google accepts any label; these are what users see in SERPs.
LANG_LABELS: dict[str, tuple[str, str]] = {
    "en": ("Home", "Blog"),
    "zh": ("首页", "博客"),
    "es": ("Inicio", "Blog"),
    "fr": ("Accueil", "Blog"),
    "de": ("Startseite", "Blog"),
    "pt": ("Início", "Blog"),
    "ja": ("ホーム", "ブログ"),
    "ru": ("Главная", "Блог"),
    "ar": ("الرئيسية", "المدونة"),
    "th": ("หน้าแรก", "บล็อก"),
}

# Blog root path segments per language.
# /en/        → /blog/
# /<other>/   → /<lang>/blog/
def blog_segment(lang: str) -> str:
    return f"/{lang}/blog/" if lang != "en" else "/blog/"

CANONICAL_RE = re.compile(
    r'<link\s+rel="canonical"\s+href="(?P<url>https?://[^"]+)"',
    re.IGNORECASE,
)
TITLE_RE = re.compile(r"<title[^>]*>(?P<t>[^<]+)</title>", re.IGNORECASE)
# Match the Article JSON-LD opening tag (we insert BreadcrumbList right before it)
ARTICLE_LD_RE = re.compile(
    r'<script\s+type="application/ld\+json"[^>]*>[\s\S]*?</script>',
    re.IGNORECASE,
)
# Detect existing BreadcrumbList (anywhere in file)
HAS_BREADCRUMB_RE = re.compile(r'"@type"\s*:\s*"BreadcrumbList"', re.IGNORECASE)


def detect_lang(rel_path: Path) -> str:
    """EN pages live at /blog/...; i18n at /<lang>/blog/..."""
    parts = rel_path.parts
    # rel_path is like 'blog/foo/index.html' (en) or 'zh/blog/foo/index.html'
    if parts[0] == "blog":
        return "en"
    return parts[0]


def canonical_to_post_title(canonical: str) -> str:
    """Extract the slug and convert to a title-case placeholder if needed.
    We use the <title> tag directly when present, since it's the visible
    SERP title. This function is a fallback."""
    slug = canonical.rstrip("/").rsplit("/", 1)[-1]
    return slug.replace("-", " ").title()


def build_breadcrumb_ld(canonical: str, post_title: str, lang: str) -> str:
    home_label, blog_label = LANG_LABELS.get(lang, LANG_LABELS["en"])
    seg = blog_segment(lang)
    # Home URL: strip the /<lang>/blog/<slug>/ portion, keep the root with optional lang prefix.
    # canonical like: https://weddingai.video/blog/foo/  → home = https://weddingai.video/
    # canonical like: https://weddingai.video/zh/blog/foo/ → home = https://weddingai.video/zh/
    if lang == "en":
        home_url = "https://weddingai.video/"
    else:
        home_url = f"https://weddingai.video/{lang}/"
    blog_url = f"https://weddingai.video{seg}"

    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": home_label,
                "item": home_url,
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": blog_label,
                "item": blog_url,
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": post_title,
                "item": canonical,
            },
        ],
    }
    json_str = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f'<script type="application/ld+json">{json_str}</script>\n'


def process_file(path: Path, root: Path, dry: bool) -> tuple[str, str]:
    """Returns (status, message). status: 'updated' | 'skipped' | 'error'."""
    rel = path.relative_to(root)
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return "error", f"{rel}: read failed: {e}"

    # Skip 0-byte / empty files (pre-existing issue, not breadcrumb-related)
    if not text.strip():
        return "skipped", f"{rel}: empty file (0 bytes), skipped"

    if HAS_BREADCRUMB_RE.search(text):
        return "skipped", f"{rel}: already has BreadcrumbList"

    cm = CANONICAL_RE.search(text)
    if not cm:
        return "error", f"{rel}: no canonical link found"
    canonical = cm.group("url").rstrip("/") + "/"

    tm = TITLE_RE.search(text)
    if tm:
        # Strip the trailing " | WeddingAI.video" suffix (and similar) for cleanliness
        raw_title = tm.group("t").strip()
        post_title = re.sub(r"\s*[|·•–—\-]\s*WeddingAI.*$", "", raw_title).strip()
        if not post_title:
            post_title = raw_title
    else:
        post_title = canonical_to_post_title(canonical)

    lang = detect_lang(rel)
    if lang not in LANG_LABELS:
        return "error", f"{rel}: unknown lang '{lang}'"

    ld_block = build_breadcrumb_ld(canonical, post_title, lang)

    # Insert right before the first Article JSON-LD script; if not found,
    # insert before <script src="/js/langs.js"> as a fallback.
    new_text, n = ARTICLE_LD_RE.subn(ld_block + r"\g<0>", text, count=1)
    if n == 0:
        # Fallback anchor
        langs_re = re.compile(
            r'(<script\s+src="/js/langs\.js"[^>]*></script>)', re.IGNORECASE
        )
        new_text, n2 = langs_re.subn(ld_block + r"\1", text, count=1)
        if n2 == 0:
            return "error", f"{rel}: no insertion anchor found (no Article JSON-LD and no /js/langs.js)"

    if dry:
        return "updated", f"{rel}: (dry) would insert BreadcrumbList for '{post_title}' [{lang}]"

    try:
        path.write_text(new_text, encoding="utf-8")
    except Exception as e:
        return "error", f"{rel}: write failed: {e}"
    return "updated", f"{rel}: inserted BreadcrumbList for '{post_title}' [{lang}]"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=".", help="project root (default: cwd)")
    p.add_argument("--dry-run", action="store_true", help="report what would change, don't write")
    args = p.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"root not a directory: {root}", file=sys.stderr)
        return 2

    targets: list[Path] = []
    # EN: /blog/<slug>/index.html (direct children, not /blog/index.html)
    en_blog = root / "blog"
    if en_blog.is_dir():
        for d in en_blog.iterdir():
            if d.is_dir() and (d / "index.html").is_file():
                targets.append(d / "index.html")
    # i18n: /<lang>/blog/<slug>/index.html
    for lang in LANG_LABELS:
        if lang == "en":
            continue
        lang_blog = root / lang / "blog"
        if not lang_blog.is_dir():
            continue
        for d in lang_blog.iterdir():
            if d.is_dir() and (d / "index.html").is_file():
                targets.append(d / "index.html")

    if not targets:
        print("no blog posts found", file=sys.stderr)
        return 1

    n_updated = n_skipped = n_error = 0
    for path in sorted(targets):
        status, msg = process_file(path, root, args.dry_run)
        print(msg)
        if status == "updated":
            n_updated += 1
        elif status == "skipped":
            n_skipped += 1
        else:
            n_error += 1

    mode = "DRY RUN" if args.dry_run else "DONE"
    print(f"\n{mode}: updated={n_updated} skipped={n_skipped} error={n_error} total={len(targets)}")
    return 0 if n_error == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
