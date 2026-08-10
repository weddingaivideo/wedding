#!/usr/bin/env python3
"""
Inject an ItemList of all blog articles into blog/index.html, sorted by
Article.datePublished DESC. Each ListItem references the corresponding
Article schema (by @id) in the detail page.

This is the "Top X articles" / "Most recent articles" rich-result pattern.
The existing Blog schema block stays untouched.

Idempotent.

Run:
    python scripts/inject-blog-itemlist.py         # dry-run
    python scripts/inject-blog-itemlist.py --apply # write
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://weddingai.video"
BLOG_DIR = ROOT / "blog"
TARGET = BLOG_DIR / "index.html"

HAS_ARTICLE = re.compile(r'"@type"\s*:\s*"Article"')
SCRIPT_RE = re.compile(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', re.DOTALL)
SLUG_RE = re.compile(r'"url"\s*:\s*"https://weddingai\.video/blog/([^/]+)/?"')

MARKER = "/* P0-INJECTED: blog ItemList */"
COMMENT_OPEN = "<!-- P0-INJECTED: blog ItemList -->"
COMMENT_END  = "<!-- /P0-INJECTED -->"
BLOCK_RE = re.compile(rf"{re.escape(COMMENT_OPEN)}.*?{re.escape(COMMENT_END)}", re.DOTALL)
BODY_END_RE = re.compile(r"</body>")


def collect_articles() -> list[dict]:
    """Walk blog/<slug>/index.html and pull headline + datePublished + url."""
    out = []
    for slug_dir in sorted(BLOG_DIR.iterdir()):
        if not slug_dir.is_dir():
            continue
        page = slug_dir / "index.html"
        if not page.exists():
            continue
        text = page.read_text(encoding="utf-8")
        article = None
        for body in SCRIPT_RE.findall(text):
            if not HAS_ARTICLE.search(body):
                continue
            try:
                d = json.loads(body)
            except json.JSONDecodeError:
                continue
            if d.get("@type") == "Article":
                article = d
                break
        if not article:
            continue
        url = f"{SITE}/blog/{slug_dir.name}/"
        out.append({
            "slug": slug_dir.name,
            "url":  url,
            "name": article.get("headline") or article.get("name") or slug_dir.name,
            "date": article.get("datePublished") or "2026-01-01",
            "section": article.get("articleSection", "Wedding Video"),
        })
    # sort by date desc, ties by name asc
    out.sort(key=lambda a: (a["date"], a["slug"]), reverse=True)
    return out


def build_block(articles: list[dict]) -> str:
    payload = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "@id": f"{SITE}/blog/#itemlist",
        "url": f"{SITE}/blog/",
        "name": "WeddingAI.video Blog \u2014 All Articles",
        "description": f"{len(articles)} in-depth articles on wedding video restoration, AI editing, slow motion, family tributes, and more.",
        "numberOfItems": len(articles),
        "itemListOrder": "https://schema.org/ItemListOrderDescending",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "item": {
                    "@type": "Article",
                    "@id": f"{a['url']}#article",
                    "url": a["url"],
                    "name": a["name"],
                    "datePublished": a["date"],
                    "articleSection": a["section"],
                },
            }
            for i, a in enumerate(articles)
        ],
    }
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return (
        f"{COMMENT_OPEN}\n"
        f'<script type="application/ld+json">\n{body}\n</script>\n'
        f"{COMMENT_END}"
    )


def main():
    dry_run = "--apply" not in sys.argv
    if dry_run:
        print("DRY-RUN mode. Pass --apply to write changes.\n")
    if not TARGET.exists():
        sys.exit(f"ERROR: {TARGET} not found")

    articles = collect_articles()
    print(f"  collected {len(articles)} articles\n")
    if not articles:
        sys.exit("  no articles found")

    text = TARGET.read_text(encoding="utf-8")
    new_block = build_block(articles)
    if BLOCK_RE.search(text):
        new_text = BLOCK_RE.sub(new_block, text)
        action = "REPLACED"
    else:
        m = BODY_END_RE.search(text)
        if not m:
            sys.exit("  ERR : no </body>")
        new_text = text[: m.start()] + new_block + "\n" + text[m.start():]
        action = "INJECTED"

    if dry_run:
        print(f"  DRY  : blog/index.html -> {action} ({len(new_block)} bytes)")
    else:
        TARGET.write_text(new_text, encoding="utf-8")
        print(f"  WROTE: blog/index.html -> {action}")


if __name__ == "__main__":
    main()
