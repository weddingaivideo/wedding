"""
Generate the /blog/ section from `articles/*.md`.

What it produces
----------------
- /blog/index.html               — list of all 50 articles
- /blog/<slug>/index.html        — one HTML page per article
- /blog/<slug>/                  — the directory itself (Pages serves index.html)

Inputs
------
- articles/*.md                  — markdown files with YAML frontmatter
- styles.min.css                 — referenced by every generated page
- templates/header.html + footer.html — header/footer chunks (read inline below)

Conventions
-----------
- Slug = file stem (e.g. 01-restore-old-wedding-videos.md -> 01-restore-old-wedding-videos)
- Image refs: `images/...` (relative to project root) become absolute `/images/...`
- Missing images (e.g. `images/png/...` which don't exist on disk) are silently skipped
  — better than a 404 on every article page

Markdown support
----------------
Hand-rolled, intentionally minimal but covers everything in the corpus:
  h1, h2, h3, paragraphs, ul, ol, bold, italic, inline code,
  links, images, blockquotes, hr, html comments (stripped).
"""
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = ROOT / "articles"
BLOG_DIR = ROOT / "blog"
TODAY = datetime.utcnow().strftime("%Y-%m-%d")

# ----------------------------------------------------------------------------
# YAML frontmatter parser (avoid external dep; we only need a handful of fields)
# ----------------------------------------------------------------------------
def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_block = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")
    meta = {}
    current_key = None
    current_list = None
    for line in fm_block.splitlines():
        if not line.strip():
            continue
        if line.startswith("  ") and current_list is not None:
            # list item continuation
            stripped = line.strip().strip('"').rstrip(",")
            current_list.append(stripped)
            continue
        m = re.match(r'^(\w+):\s*(.*)$', line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val == "":
            current_list = []
            meta[key] = current_list
            current_key = key
        elif val.startswith("[") and val.endswith("]"):
            # inline list like ["a","b"]
            inner = val[1:-1].strip()
            items = [s.strip().strip('"').strip("'") for s in inner.split(",") if s.strip()]
            meta[key] = items
            current_list = None
        else:
            meta[key] = val.strip('"').strip("'")
            current_list = None
    return meta, body


# ----------------------------------------------------------------------------
# Tiny markdown -> HTML (covers the corpus; not CommonMark-complete)
# ----------------------------------------------------------------------------
INLINE_PATTERNS = [
    (re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)"), r'<img src="\2" alt="\1" loading="lazy" />'),
    (re.compile(r"\[([^\]]+)\]\(([^)]+)\)"), r'<a href="\2">\1</a>'),
    (re.compile(r"\*\*([^*]+)\*\*"), r"<strong>\1</strong>"),
    (re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)"), r"<em>\1</em>"),
    (re.compile(r"`([^`]+)`"), r"<code>\1</code>"),
]


def apply_inline(text: str) -> str:
    # Protect <code> blocks from further inline processing
    out = text
    for pat, repl in INLINE_PATTERNS:
        out = pat.sub(repl, out)
    return out


def slugify_image_path(rel: str) -> str:
    """Turn 'images/png/01-foo.png' into '/images/png/01-foo.png'.

    Skip if the file is missing on disk — we don't want 404s in the blog."""
    if rel.startswith("http"):
        return rel
    abs_path = ROOT / rel
    if not abs_path.exists():
        return None
    return "/" + rel.lstrip("/")


def render_markdown(md: str) -> str:
    lines = md.splitlines()
    out = []
    i = 0
    in_ul = False
    in_ol = False
    para = []

    def flush_para():
        nonlocal para
        if para:
            out.append(f"<p>{apply_inline(' '.join(para).strip())}</p>")
            para = []

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # HTML comment -> drop
        if stripped.startswith("<!--") and stripped.endswith("-->"):
            i += 1
            continue
        if stripped.startswith("<!--"):
            # multi-line comment
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue

        # Headings
        m = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if m:
            flush_para()
            close_lists()
            level = len(m.group(1))
            out.append(f"<h{level}>{apply_inline(m.group(2))}</h{level}>")
            i += 1
            continue

        # HR
        if stripped == "---":
            flush_para()
            close_lists()
            out.append("<hr>")
            i += 1
            continue

        # Blockquote
        if stripped.startswith(">"):
            flush_para()
            close_lists()
            bq = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                bq.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append(f"<blockquote><p>{apply_inline(' '.join(bq))}</p></blockquote>")
            continue

        # Unordered list
        if re.match(r"^[-*]\s+", stripped):
            flush_para()
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            item = re.sub(r"^[-*]\s+", "", stripped)
            out.append(f"  <li>{apply_inline(item)}</li>")
            i += 1
            continue

        # Ordered list
        if re.match(r"^\d+\.\s+", stripped):
            flush_para()
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            item = re.sub(r"^\d+\.\s+", "", stripped)
            out.append(f"  <li>{apply_inline(item)}</li>")
            i += 1
            continue

        # Blank line
        if not stripped:
            flush_para()
            close_lists()
            i += 1
            continue

        # Paragraph accumulation
        para.append(stripped)
        i += 1

    flush_para()
    close_lists()
    return "\n".join(out)


# ----------------------------------------------------------------------------
# HTML helpers — share header/footer between list and article pages
# ----------------------------------------------------------------------------
def head_block(title: str, description: str, canonical: str, og_image: str = "") -> str:
    og_image_tag = f'<meta property="og:image" content="{og_image}">' if og_image else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <link rel="canonical" href="{canonical}">
    <meta property="og:type" content="article">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:site_name" content="WeddingAI.video">
    <meta property="og:locale" content="en_US">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    {og_image_tag}
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <meta name="theme-color" content="#c45a72">
    <link rel="manifest" href="/manifest.json">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">
    <link rel="preload" href="/styles.min.css" as="style">
    <link rel="stylesheet" href="/styles.min.css" media="print" onload="this.media='all'">
    <noscript><link rel="stylesheet" href="/styles.min.css"></noscript>
    <script defer src="/js/main.min.js"></script>
    <script>
    // gtag.js (G-4FE7KSJDNB) deferred to first interaction or idle —
    // ~159 KiB skipped entirely on bounce; manual pageview on script load.
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-4FE7KSJDNB', {{ send_page_view: false, transport_type: 'beacon' }});
    window.__loadGtag = function() {{
      if (window.__gtagLoaded) return;
      window.__gtagLoaded = true;
      var s = document.createElement('script');
      s.src = 'https://www.googletagmanager.com/gtag/js?id=G-4FE7KSJDNB';
      s.async = true;
      s.onload = function() {{
        gtag('event', 'page_view', {{
          page_title: document.title,
          page_location: location.href,
          page_path: location.pathname + location.search
        }});
      }};
      s.setAttribute('data-gtag-lazy', '1');
      document.head.appendChild(s);
    }};
    ['scroll','click','touchstart','keydown'].forEach(function(evt){{
      window.addEventListener(evt, window.__loadGtag, {{ once: true, passive: true, capture: true }});
    }});
    window.addEventListener('load', function() {{
      if ('requestIdleCallback' in window) {{
        requestIdleCallback(window.__loadGtag, {{ timeout: 4000 }});
      }} else {{
        setTimeout(window.__loadGtag, 3000);
      }}
    }});
    </script>
</head>
<body>
"""


HEADER_NAV = """    <header class="site-header">
        <div class="container header-inner">
            <a href="/" class="logo" title="WeddingAI.video — wedding video services">
                <picture>
    <source srcset="/images/logo-full-178.avif 178w, /images/logo-full-356.avif 356w, /images/logo-full-712.avif 712w" type="image/avif" sizes="(max-width: 600px) 178px, 356px">
    <source srcset="/images/logo-full-178.webp 178w, /images/logo-full-356.webp 356w, /images/logo-full-712.webp 712w" type="image/webp" sizes="(max-width: 600px) 178px, 356px">
    <img src="/images/logo-full.jpeg" alt="WeddingAI.video" height="72" width="1619" fetchpriority="high" loading="eager" sizes="(max-width: 600px) 178px, 356px">
  </picture>
            </a>
            <nav class="main-nav" aria-label="Main navigation">
                <ul class="nav-list">
                    <li><a href="/#services" title="Browse our wedding video services">Services</a></li>
                    <li><a href="/gallery/" title="View our gallery and case studies">Gallery</a></li>
                    <li><a href="/blog/" title="Read our wedding video blog">Blog</a></li>
                    <li><a href="/about/" title="Learn about us">About</a></li>
                    <li><a href="/order/" class="btn-nav" title="Get a free quote — start your project">Get a Quote</a></li>
                </ul>
            </nav>
            <button class="mobile-menu-toggle" aria-label="Toggle mobile menu" aria-expanded="false">
                <span></span><span></span><span></span>
            </button>
        </div>
    </header>
"""


FOOTER = """    <footer class="site-footer">
        <div class="container footer-inner">
            <div class="footer-brand">
                <a href="/" class="logo" title="WeddingAI.video — wedding video services">
                    <picture>
    <source srcset="/images/logo-full-178.avif 178w, /images/logo-full-356.avif 356w, /images/logo-full-712.avif 712w" type="image/avif" sizes="(max-width: 600px) 178px, 356px">
    <source srcset="/images/logo-full-178.webp 178w, /images/logo-full-356.webp 356w, /images/logo-full-712.webp 712w" type="image/webp" sizes="(max-width: 600px) 178px, 356px">
    <img src="/images/logo-full.jpeg" alt="WeddingAI.video" height="72" width="1619" loading="lazy" sizes="(max-width: 600px) 178px, 356px">
  </picture>
                </a>
                <p>AI-powered wedding video services for couples worldwide.</p>
            </div>
            <nav class="footer-nav" aria-label="Footer navigation">
                <div class="footer-col">
                    <h4>Resources</h4>
                    <ul>
                        <li><a href="/blog/" title="Read our wedding video blog">Blog</a></li>
                        <li><a href="/gallery/" title="View our gallery and case studies">Gallery</a></li>
                        <li><a href="/about/" title="Learn about us">About Us</a></li>
                    </ul>
                </div>
                <div class="footer-col">
                    <h4>Services</h4>
                    <ul>
                        <li><a href="/services/video-enhancement/slow-motion/" title="AI Slow Motion Enhancement">Slow Motion</a></li>
                        <li><a href="/services/personalization/ai-video-generator/" title="AI Wedding Video Generator">AI Video Generator</a></li>
                        <li><a href="/services/personalization/wedding-trailer/" title="Cinematic Wedding Trailer">Wedding Trailer</a></li>
                        <li><a href="/services/absence-compensation/family-tribute/" title="Tribute to Loved Ones">Family Tribute</a></li>
                    </ul>
                </div>
                <div class="footer-col">
                    <h4>Contact</h4>
                    <ul>
                        <li><a href="/order/" title="Get a free quote — start your project">Get a Quote</a></li>
                    </ul>
                </div>
            </nav>
        </div>
        <div class="footer-bottom">
            <div class="container">
                <p>© 2026 WeddingAI.video. All rights reserved.</p>
                <p><a href="/privacy/" title="Read our privacy policy">Privacy Policy</a> · <a href="/terms/" title="Read our terms of service">Terms of Service</a></p>
            </div>
        </div>
    </footer>
</body>
</html>
"""


# ----------------------------------------------------------------------------
# Article page
# ----------------------------------------------------------------------------
def _drop_dup_body_heading(html: str, title: str) -> str:
    """Drop the first <h1>/<h2> line in body html if its text duplicates the page-hero h1.

    Articles often open with a `# Title` markdown heading that the body renderer
    turns into <h1> (or the second batch used <h2>). Since the page already has
    an <h1> in the hero block, this leaves the page with a duplicate top-level
    heading — a real SEO/a11y issue (and an audit-flag).

    We compare the heading's text (tags stripped, whitespace collapsed) against
    `title` (case-insensitive) and drop the line if they match. Idempotent: a no-op
    when the first body heading is a real section title (the common case in the
    first batch of 50 articles where the body `# Title` was reworded).
    """
    if not title or not html:
        return html
    title_norm = re.sub(r"\s+", " ", title).strip().lower()
    # Match one heading line at the start of a line: <h1 ...>TEXT</h1> or <h2 ...>TEXT</h2>,
    # with optional surrounding whitespace and a trailing newline.
    m = re.search(
        r"(?m)^[ \t]*<h([12])\b[^>]*>(.*?)</h\1>[ \t]*\r?\n",
        html,
        re.IGNORECASE | re.DOTALL,
    )
    if not m:
        return html
    inner = m.group(2)
    # Strip nested tags (e.g. <span data-i18n=...>) so the comparison is robust
    # against i18n post-processing that wraps the text.
    text = re.sub(r"<[^>]+>", "", inner)
    text = re.sub(r"\s+", " ", text).strip().lower()
    if text and text == title_norm:
        return html[: m.start()] + html[m.end():]
    return html


def render_article(meta: dict, body_md: str, slug: str) -> str:
    title = meta.get("title", slug)
    description = meta.get("meta_description", "")
    primary_kw = meta.get("primary_keyword", "wedding video")
    word_count = int(meta.get("word_count_target", 1500))
    # Rough read time: 200 wpm
    read_min = max(1, round(word_count / 200))

    canonical = f"https://weddingai.video/blog/{slug}/"
    html_body = render_markdown(body_md)
    # Drop any <img> whose src points at a missing file (avoid alt-text leaks).
    # Done by scanning all <img ... /> tags: if src is missing on disk, drop the
    # whole tag (along with the wrapping <p>...</p> if it became empty).
    def img_drop(m):
        tag = m.group(0)
        src_m = re.search(r'src="([^"]+)"', tag)
        if not src_m:
            return ""
        rel = src_m.group(1)
        if rel.startswith("http"):
            return tag
        if not (ROOT / rel).exists():
            return ""
        # rewrite to absolute path
        return tag.replace(f'src="{rel}"', f'src="/{rel.lstrip(chr(47))}"', 1)
    html_body = re.sub(r'<img[^>]*/?>', img_drop, html_body)
    # Also rewrite <a href="images/..."> to /images/... if it exists, else #
    html_body = re.sub(
        r'href="(images/[^"]+)"',
        lambda m: f'href="/{m.group(1)}"' if (ROOT / m.group(1)).exists() else 'href="#"',
        html_body,
    )
    # Collapse empty <p></p> that the dropped <img> left behind.
    html_body = re.sub(r"<p>\s*</p>", "", html_body)
    # Defensive: drop a body heading that duplicates the hero <h1>. This keeps
    # the page from rendering the same title twice (page audit will catch it).
    html_body = _drop_dup_body_heading(html_body, title)

    head = head_block(f"{title} | WeddingAI.video Blog", description, canonical)
    hero = f"""
    <main>
        <section class="page-hero page-hero-small">
            <div class="page-hero-bg"></div>
            <div class="page-hero-overlay"></div>
            <div class="container page-hero-content">
                <p style="color: var(--color-primary); font-size: 0.875rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">WeddingAI.video Blog</p>
                <h1>{title}</h1>
                <p>{description}</p>
                <p style="margin-top: 1rem; font-size: 0.875rem; color: rgba(255,255,255,0.7);">{read_min} min read · Updated {TODAY}</p>
            </div>
        </section>

        <section class="section" style="background: var(--color-white);">
            <div class="container blog-article" style="max-width: 760px;">
                {html_body}
            </div>
        </section>

        <section class="section cta-section" aria-label="Get started">
            <div class="container">
                <div class="cta-content">
                    <h2>Ready to Transform Your Wedding Memories?</h2>
                    <p>Tell us about your project and we'll get back within 24 hours with a free quote.</p>
                    <a href="/order/" class="btn btn-primary btn-large" title="Get a free quote — start your project">Get a Free Quote →</a>
                </div>
            </div>
        </section>
    </main>
    """
    return head + HEADER_NAV + hero + FOOTER


# ----------------------------------------------------------------------------
# List page
# ----------------------------------------------------------------------------
def render_list(articles: list[dict]) -> str:
    canonical = "https://weddingai.video/blog/"
    title = "Wedding Video Blog: Tips, Guides & AI Insights | WeddingAI.video"
    description = "50 in-depth articles on wedding video restoration, AI editing, slow motion, family tributes, and more. Updated for 2026."
    head = head_block(title, description, canonical, og_image="https://weddingai.video/images/hero-wedding-vineyard.png")

    cards = []
    for a in articles:
        slug = a["slug"]
        cards.append(f"""
                <article class="case-card">
                    <a href="/blog/{slug}/" class="case-img-link" title="Read: {a['title']}">
                        <div class="case-img" role="img" aria-label="{a['title']}">
                            <img src="/images/blog/hero/{slug}.jpg" alt="{a['title']}" loading="lazy" width="640" height="360" />
                        </div>
                    </a>
                    <div class="case-body">
                        <h3><a href="/blog/{slug}/" style="color: var(--color-secondary);" title="Read: {a['title']}">{a['title']}</a></h3>
                        <p>{a['description']}</p>
                        <p style="font-size: 0.75rem; color: var(--color-text-light); margin-top: 0.5rem;">{a['read_min']} min read</p>
                    </div>
                </article>""")

    body = f"""
    <main>
        <section class="page-hero page-hero-small">
            <div class="page-hero-bg"></div>
            <div class="page-hero-overlay"></div>
            <div class="container page-hero-content">
                <p style="color: var(--color-primary); font-size: 0.875rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">WeddingAI.video Blog</p>
                <h1>Wedding Video Tips, Guides & AI Insights</h1>
                <p>{len(articles)} in-depth articles covering restoration, AI editing, slow motion, family tributes, and more. Updated for 2026.</p>
            </div>
        </section>

        <section class="section" style="background: var(--color-white);">
            <div class="container">
                <div class="cases-grid">
                    {''.join(cards)}
                </div>
            </div>
        </section>

        <section class="section cta-section" aria-label="Get started">
            <div class="container">
                <div class="cta-content">
                    <h2>Ready to Transform Your Wedding Memories?</h2>
                    <p>Tell us about your project and we'll get back within 24 hours with a free quote.</p>
                    <a href="/order/" class="btn btn-primary btn-large" title="Get a free quote — start your project">Get a Free Quote →</a>
                </div>
            </div>
        </section>
    </main>
    """
    return head + HEADER_NAV + body + FOOTER


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main() -> int:
    if not ARTICLES_DIR.exists():
        sys.exit(f"[fail] {ARTICLES_DIR} missing")

    BLOG_DIR.mkdir(parents=True, exist_ok=True)
    article_metas = []
    for md_path in sorted(ARTICLES_DIR.glob("*.md")):
        slug = md_path.stem
        text = md_path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        # Try to extract a numeric prefix from the slug (e.g. 01-foo -> 1)
        m = re.match(r"^(\d+)-", slug)
        num = int(m.group(1)) if m else 0
        word_count = int(meta.get("word_count_target", 1500) or 1500)
        article_metas.append({
            "slug": slug,
            "num": num,
            "title": meta.get("title", slug.replace("-", " ").title()),
            "description": meta.get("meta_description", ""),
            "primary_keyword": meta.get("primary_keyword", ""),
            "read_min": max(1, round(word_count / 200)),
            "body": body,
            "meta": meta,
        })

    # Generate list page
    list_html = render_list(article_metas)
    (BLOG_DIR / "index.html").write_text(list_html, encoding="utf-8")
    print(f"[ok] blog/index.html ({len(article_metas)} articles)")

    # Generate one page per article
    for a in article_metas:
        slug = a["slug"]
        out_dir = BLOG_DIR / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        html = render_article(a["meta"], a["body"], slug)
        (out_dir / "index.html").write_text(html, encoding="utf-8")

    print(f"[ok] {len(article_metas)} article pages written to blog/<slug>/index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
