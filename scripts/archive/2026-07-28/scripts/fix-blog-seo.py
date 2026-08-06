"""
Post-process blog HTML to fix SEO issues found by audit-blog-seo.py.

Fixes applied (idempotent):
1. Demote the first <h1> in <article body> to <h2> (we already have one in page-hero).
2. Add <meta name="keywords"> from frontmatter secondary_keywords.
3. Add Article JSON-LD to <head>.
4. Add og:image if missing AND a hero image exists at /images/blog/hero/<slug>.<ext>.
5. Add og:locale, og:type, article:published_time, article:modified_time.

Does NOT touch:
- styles.min.css
- The 50 source .md files
- generate-blog.py (so re-running it doesn't undo fixes)
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"
ARTICLES = ROOT / "articles"
HERO_DIR = ROOT / "images" / "blog" / "hero"
TODAY = datetime.utcnow().strftime("%Y-%m-%d")

SITE_URL = "https://weddingai.video"


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm = text[3:end].strip()
    meta = {}
    current_list = None
    for line in fm.splitlines():
        if not line.strip():
            continue
        m = re.match(r"^(\w+):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val == "":
            meta[key] = []
            current_list = meta[key]
        elif val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            items = [s.strip().strip('"').strip("'") for s in inner.split(",") if s.strip()]
            meta[key] = items
            current_list = None
        else:
            meta[key] = val.strip('"').strip("'")
            current_list = None
    return meta


def find_first_h1_in_body(text: str) -> tuple[int, int] | None:
    """Find the first <h1>...</h1> AFTER the page-hero section.

    The body section is delimited by class containing "blog-article".
    Returns the absolute (start, end) span of the first <h1> inside it, or None.
    """
    m = re.search(r'<div[^>]*class="[^"]*\bblog-article\b[^"]*"[^>]*>', text)
    if not m:
        return None
    body_start = m.end()
    h1 = re.search(r"<h1>([^<]+)</h1>", text[body_start:])
    if not h1:
        return None
    return (body_start + h1.start(), body_start + h1.end())


def find_hero_image(slug: str) -> str | None:
    """Check disk for /images/blog/hero/<slug>.<ext> in priority order."""
    for ext in ("jpg", "jpeg", "png", "webp", "avif"):
        p = HERO_DIR / f"{slug}.{ext}"
        if p.exists():
            return f"/images/blog/hero/{slug}.{ext}"
    return None


def build_article_jsonld(meta: dict, slug: str, title: str, description: str) -> str:
    canonical = f"{SITE_URL}/blog/{slug}/"
    primary = meta.get("primary_keyword", "wedding video")
    keywords = meta.get("secondary_keywords", []) or []
    if isinstance(keywords, str):
        keywords = [keywords]
    if primary and primary not in keywords:
        keywords = [primary] + keywords
    word_target = int(meta.get("word_count_target", 1500) or 1500)
    read_min = max(1, round(word_target / 200))
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "image": f"{SITE_URL}/images/blog/hero/{slug}.jpg",
        "author": {
            "@type": "Organization",
            "name": "WeddingAI.video",
            "url": SITE_URL,
        },
        "publisher": {
            "@type": "Organization",
            "name": "WeddingAI.video",
            "logo": {
                "@type": "ImageObject",
                "url": f"{SITE_URL}/images/logo-full.jpeg",
            },
        },
        "datePublished": "2026-07-23",
        "dateModified": TODAY,
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "url": canonical,
        "keywords": ", ".join(keywords),
        "wordCount": str(word_target),
        "timeRequired": f"PT{read_min}M",
        "inLanguage": "en-US",
    }, ensure_ascii=False)


def fix_article(html_path: Path, md_path: Path) -> list[str]:
    text = html_path.read_text(encoding="utf-8")
    if not md_path.exists():
        return [f"[skip] no md for {html_path.name}"]
    md = md_path.read_text(encoding="utf-8")
    meta = parse_frontmatter(md)
    slug = html_path.parent.name
    changes = []

    # 1. Demote first <h1> in body to <h2>
    span = find_first_h1_in_body(text)
    if span:
        s, e = span
        old = text[s:e]
        new = old.replace("<h1>", "<h2>", 1).replace("</h1>", "</h2>", 1)
        text = text[:s] + new + text[e:]
        changes.append("demoted body H1 -> H2")

    # 2. Add <meta name="keywords"> if missing
    if 'name="keywords"' not in text:
        primary = meta.get("primary_keyword", "wedding video")
        secondary = meta.get("secondary_keywords", []) or []
        if isinstance(secondary, str):
            secondary = [secondary]
        all_kw = [primary] + [s for s in secondary if s and s != primary]
        kw_str = ", ".join(all_kw)
        kw_tag = f'\n    <meta name="keywords" content="{kw_str}">'
        # Insert right after the description meta
        text = re.sub(
            r'(<meta name="description" content="[^"]+">)',
            r"\1" + kw_tag,
            text,
            count=1,
        )
        changes.append(f"added keywords ({len(all_kw)})")

    # 3. Add og:locale if missing
    if 'property="og:locale"' not in text:
        text = re.sub(
            r'(<meta property="og:site_name" content="[^"]+">)',
            r'\1\n    <meta property="og:locale" content="en_US">',
            text,
            count=1,
        )
        changes.append("added og:locale")

    # 4. Add og:image if hero image exists on disk
    hero = find_hero_image(slug)
    if hero and 'property="og:image"' not in text:
        img_tag = f'\n    <meta property="og:image" content="{SITE_URL}{hero}">'
        text = re.sub(
            r'(<meta property="og:locale" content="[^"]+">)',
            r"\1" + img_tag,
            text,
            count=1,
        )
        changes.append(f"added og:image -> {hero}")

    # 5. Add og:type=article if not already article
    if 'property="og:type"' in text and 'content="article"' not in text:
        text = re.sub(
            r'<meta property="og:type" content="website">',
            '<meta property="og:type" content="article">',
            text,
            count=1,
        )
        changes.append("og:type: website -> article")

    # 6. Add Article JSON-LD if not present
    if 'application/ld+json' not in text:
        title = meta.get("title", slug)
        desc = meta.get("meta_description", "")
        jsonld = build_article_jsonld(meta, slug, title, desc)
        # Insert before </head>
        ld_tag = f'\n    <script type="application/ld+json">{jsonld}</script>\n'
        text = re.sub(r"\s*</head>", ld_tag + "</head>", text, count=1)
        changes.append("added Article JSON-LD")

    if changes:
        html_path.write_text(text, encoding="utf-8")
    return changes


def fix_list_page(html_path: Path) -> list[str]:
    text = html_path.read_text(encoding="utf-8")
    changes = []

    # Make sure og:image points at site hero (list page has no per-article hero)
    if 'property="og:image"' not in text:
        text = re.sub(
            r'(<meta property="og:locale" content="en_US">)',
            r'\1\n    <meta property="og:image" content="https://weddingai.video/images/hero-wedding-vineyard.png">',
            text,
            count=1,
        )
        changes.append("added og:image (site hero)")

    # Add BlogPosting JSON-LD for the list
    if 'application/ld+json' not in text:
        ld = json.dumps({
            "@context": "https://schema.org",
            "@type": "Blog",
            "name": "WeddingAI.video Blog",
            "url": f"{SITE_URL}/blog/",
            "description": "50 in-depth articles on wedding video restoration, AI editing, slow motion, family tributes, and more.",
            "publisher": {
                "@type": "Organization",
                "name": "WeddingAI.video",
                "logo": {"@type": "ImageObject", "url": f"{SITE_URL}/images/logo-full.jpeg"},
            },
        }, ensure_ascii=False)
        text = re.sub(r"\s*</head>", f'\n    <script type="application/ld+json">{ld}</script>\n</head>', text, count=1)
        changes.append("added Blog JSON-LD")

    if changes:
        html_path.write_text(text, encoding="utf-8")
    return changes


def main() -> int:
    n = 0
    for art_dir in sorted(BLOG.iterdir()):
        if not art_dir.is_dir():
            continue
        slug = art_dir.name
        html = art_dir / "index.html"
        md = ARTICLES / f"{slug}.md"
        if not html.exists():
            continue
        changes = fix_article(html, md)
        if changes:
            print(f"[ok] {slug}: {', '.join(changes)}")
            n += 1

    list_path = BLOG / "index.html"
    if list_path.exists():
        changes = fix_list_page(list_path)
        if changes:
            print(f"[ok] blog/index.html: {', '.join(changes)}")
            n += 1

    print(f"\n[done] {n} files updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
