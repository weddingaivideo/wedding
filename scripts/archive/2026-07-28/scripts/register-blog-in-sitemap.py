"""
Register the new /blog/ pages in sitemap.xml and _redirects.

- sitemap.xml: insert 1 (list) + 50 (per-article) <url> blocks before </urlset>.
  Reuses the structure used elsewhere (lastmod + image:image placeholder).
- _redirects: add /blog.html -> /blog/ 308 (and the no-slash form /blog -> /blog/).
"""
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITEMAP = ROOT / "sitemap.xml"
REDIRECTS = ROOT / "_redirects"
ARTICLES_DIR = ROOT / "articles"
BLOG_DIR = ROOT / "blog"
TODAY = datetime.utcnow().strftime("%Y-%m-%d")


def update_sitemap() -> int:
    text = SITEMAP.read_text(encoding="utf-8")
    # Skip if blog already registered
    if "https://weddingai.video/blog" in text:
        print("[skip] sitemap.xml already has /blog/ entries")
        return 0

    blocks = []
    # List page
    blocks.append(f"""    <url>
        <loc>https://weddingai.video/blog</loc>
        <lastmod>{TODAY}</lastmod>
        <priority>0.9</priority>
        <changefreq>weekly</changefreq>
        <image:image>
            <image:loc>https://weddingai.video/images/logo-full.jpeg</image:loc>
        </image:image>
    </url>""")

    # Per-article pages
    for d in sorted(BLOG_DIR.iterdir()):
        if not d.is_dir():
            continue
        slug = d.name
        article_md = ARTICLES_DIR / f"{slug}.md"
        # Try to read mtime of the source .md so lastmod reflects the source
        if article_md.exists():
            mtime = datetime.utcfromtimestamp(article_md.stat().st_mtime).strftime("%Y-%m-%d")
        else:
            mtime = TODAY
        blocks.append(f"""    <url>
        <loc>https://weddingai.video/blog/{slug}</loc>
        <lastmod>{mtime}</lastmod>
        <priority>0.7</priority>
        <changefreq>monthly</changefreq>
        <image:image>
            <image:loc>https://weddingai.video/images/logo-full.jpeg</image:loc>
        </image:image>
    </url>""")

    new_block = "\n".join(blocks) + "\n"
    # Insert before </urlset>
    new_text, n = re.subn(r"</urlset>\s*$", new_block + "</urlset>", text, count=1)
    if n == 0:
        sys.exit("[fail] no </urlset> in sitemap.xml")
    SITEMAP.write_text(new_text, encoding="utf-8")
    print(f"[ok] sitemap.xml: added 1 list + {len(blocks) - 1} article URLs")
    return 0


def update_redirects() -> int:
    text = REDIRECTS.read_text(encoding="utf-8")
    if "/blog.html" in text:
        print("[skip] _redirects already has /blog entries")
        return 0
    addition = (
        "\n# Blog (v3.12.0) — generated from articles/*.md by scripts/generate-blog.py\n"
        "/blog.html                      /blog/                   308\n"
        "/blog                           /blog/                   308\n"
    )
    # Also add per-article redirects (e.g. /blog/01-foo -> /blog/01-foo/ 308) — Pages
    # serves the directory index.html directly for /blog/01-foo/, so without the
    # .html form we'd 404. Add the .html -> /  redirect for the list page; per-article
    # .html files don't exist on disk so we skip them.
    new_text = text + addition
    REDIRECTS.write_text(new_text, encoding="utf-8")
    print("[ok] _redirects: added /blog.html and /blog -> /blog/ (308)")
    return 0


if __name__ == "__main__":
    update_sitemap()
    update_redirects()
