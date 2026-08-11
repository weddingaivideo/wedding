#!/usr/bin/env python3
"""
inject-og-article.py

Add og:article:* meta tags to every blog post (EN + 8 i18n languages).
These tags are used by Facebook, LinkedIn, Slack, etc. for social sharing.
The Article JSON-LD schema already has datePublished/dateModified/author;
this script mirrors them as og:article:* meta tags next to the existing
og:* block.

For each post:
  - og:article:published_time → from JSON-LD datePublished
  - og:article:modified_time  → from JSON-LD dateModified
  - og:article:author         → "WeddingAI Editorial Team"
                                (matches the JSON-LD author.name set by
                                 functions/_middleware.js#rewriteArticleAuthor)

Idempotent: skips files that already have og:article:published_time.

Usage: python scripts/inject-og-article.py [--root <path>] [--dry-run]
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

ROOT_DEFAULT = Path(".")
AUTHOR_NAME = "WeddingAI Editorial Team"

# Match the Article JSON-LD body so we can extract datePublished/dateModified.
# The body is the JSON object between <script type="application/ld+json"> and </script>.
ARTICLE_LD_BLOCK_RE = re.compile(
    r'<script\s+type="application/ld\+json"[^>]*>(\s*\{.*?\})\s*</script>',
    re.IGNORECASE | re.DOTALL,
)
# Match the OG block. The first og:title is a stable anchor.
OG_TITLE_RE = re.compile(
    r'(<meta\s+property="og:title"[^>]+>)',
    re.IGNORECASE,
)
HAS_OG_PUB_RE = re.compile(r'og:article:published_time', re.IGNORECASE)


def extract_article_dates(text: str) -> tuple[str | None, str | None]:
    """Return (datePublished, dateModified) from the Article JSON-LD, or (None, None)."""
    for m in ARTICLE_LD_BLOCK_RE.finditer(text):
        body = m.group(1)
        try:
            obj = json.loads(body)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and obj.get("@type") == "Article":
            return (obj.get("datePublished"), obj.get("dateModified"))
    return (None, None)


def build_og_article_block(date_published: str | None, date_modified: str | None) -> str:
    """Return the 3 og:article:* <meta> tags to insert, one per line."""
    tags = []
    if date_published:
        tags.append(
            f'    <meta property="og:article:published_time" content="{date_published}">'
        )
    if date_modified:
        tags.append(
            f'    <meta property="og:article:modified_time" content="{date_modified}">'
        )
    tags.append(
        f'    <meta property="og:article:author" content="{AUTHOR_NAME}">'
    )
    return "\n".join(tags)


def process_file(path: Path, root: Path, dry: bool) -> tuple[str, str]:
    """Returns (status, message). status: 'updated' | 'skipped' | 'error'."""
    rel = path.relative_to(root)
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return "error", f"{rel}: read failed: {e}"

    if not text.strip():
        return "skipped", f"{rel}: empty file"

    if HAS_OG_PUB_RE.search(text):
        return "skipped", f"{rel}: already has og:article:published_time"

    pub, mod = extract_article_dates(text)
    if not pub and not mod:
        return "error", f"{rel}: no Article JSON-LD with dates found"

    block = build_og_article_block(pub, mod)

    # Insert right after the og:title tag (so the og:* block stays contiguous).
    new_text, n = OG_TITLE_RE.subn(r"\1\n" + block, text, count=1)
    if n == 0:
        # Fallback: insert before the first <meta property="og:*" tag, or just
        # before </head>. Last resort.
        any_og = re.search(r'(<meta\s+property="og:[^"]+"[^>]+>)', text, re.IGNORECASE)
        if any_og:
            new_text = text[:any_og.start()] + block + "\n" + text[any_og.start():]
            n = 1
        else:
            new_text = text.replace("</head>", block + "\n</head>", 1)
            n = 1

    if dry:
        return "updated", f"{rel}: (dry) would insert og:article:* (pub={pub}, mod={mod})"
    try:
        path.write_text(new_text, encoding="utf-8")
    except Exception as e:
        return "error", f"{rel}: write failed: {e}"
    return "updated", f"{rel}: inserted og:article:* (pub={pub}, mod={mod})"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=".")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"root not a directory: {root}", file=sys.stderr)
        return 2

    LANGS = {"zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th"}
    targets: list[Path] = []
    en_blog = root / "blog"
    if en_blog.is_dir():
        for d in en_blog.iterdir():
            if d.is_dir() and (d / "index.html").is_file():
                targets.append(d / "index.html")
    for lang in LANGS:
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
        if args.dry_run and status == "updated":
            print(msg)
        if status == "updated":
            n_updated += 1
        elif status == "skipped":
            n_skipped += 1
        else:
            n_error += 1
            print(msg, file=sys.stderr)

    mode = "DRY RUN" if args.dry_run else "DONE"
    print(f"\n{mode}: updated={n_updated} skipped={n_skipped} error={n_error} total={len(targets)}")
    return 0 if n_error == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
