"""
Generate llms-full.txt from the WeddingAI.video HTML pages.

Follows the llmstxt.org "full" variant: each link from llms.txt is followed by
the full Markdown content of the linked page (not just a description).

Output: llms-full.txt at project root.
"""
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).parent
BASE_URL = "https://weddingai.video"

# Pages to include with their canonical URLs and short labels.
# Order matches the structure of llms.txt
PAGES = [
    ("# WeddingAI.video", None, None),  # H1, filled in at top
    ("services",       "/services/",                                         "All Services Index"),
    ("slow-motion",    "/services/video-enhancement/slow-motion.html",       "AI Slow Motion"),
    ("wedding-trailer","/services/personalization/wedding-trailer.html",     "Wedding Trailer"),
    ("ai-video-generator", "/services/personalization/ai-video-generator.html", "AI Video Generator"),
    ("family-tribute", "/services/absence-compensation/family-tribute.html", "Family Tribute"),
    ("family-message", "/services/absence-compensation/family-message.html", "Family Message"),
    ("celebrity-message", "/services/absence-compensation/celebrity-message.html", "Celebrity Messages"),
    ("cartoon-style",  "/services/personalization/cartoon-style.html",      "Cartoon Style"),
    ("multilingual",   "/services/personalization/multilingual.html",        "Multilingual"),
    ("pet-wedding",    "/services/personalization/pet-wedding.html",         "Pet Wedding"),
    ("meme-generator", "/services/personalization/meme-generator.html",      "Wedding GIFs & Memes"),
    ("about",          "/about.html",                                         "About Us"),
    ("gallery",        "/gallery.html",                                       "Gallery"),
    ("resources",      "/resources.html",                                     "Resources"),
    ("order",          "/order.html",                                         "Get a Free Quote"),
    ("privacy",        "/privacy.html",                                       "Privacy Policy"),
    ("terms",          "/terms.html",                                         "Terms of Service"),
]

# ---------------------------------------------------------------------------
# HTML → Markdown (good-enough for LLM consumption; not a full converter)
# ---------------------------------------------------------------------------

SKIP_TAGS = {"script", "style", "noscript", "svg", "iframe", "form", "button", "input", "select", "textarea"}

def is_comment(node):
    from bs4 import Comment
    return isinstance(node, Comment)

def inline_md(node, page_url=BASE_URL + "/"):
    """Render inline content of a tag to markdown."""
    if is_comment(node):
        return ""
    if isinstance(node, NavigableString):
        return str(node)
    if not isinstance(node, Tag):
        return ""
    if node.name in SKIP_TAGS:
        return ""
    if node.name == "br":
        return "\n"
    children = "".join(inline_md(c, page_url) for c in node.children)
    if node.name in ("strong", "b"):
        return f"**{children}**"
    if node.name in ("em", "i"):
        return f"*{children}*"
    if node.name == "code":
        return f"`{children}`"
    if node.name == "a":
        href = node.get("href", "")
        href = make_absolute(href, page_url)
        return f"[{children}]({href})" if href else children
    if node.name in ("picture", "source", "img"):
        return ""  # skip images; alt would be noise here
    if node.name == "span":
        return children
    return children

def make_absolute(url: str, page_url: str) -> str:
    """Resolve a relative URL against the page URL (which itself is absolute)."""
    from urllib.parse import urljoin
    if not url:
        return url
    if url.startswith(("http://", "https://", "mailto:", "tel:", "#", "data:")):
        return url
    return urljoin(page_url, url)

def render(node, depth=0, page_url=BASE_URL + "/"):
    """Render a block-level element to markdown."""
    if is_comment(node):
        return ""
    if isinstance(node, NavigableString):
        text = str(node).strip()
        return text + "\n\n" if text else ""
    if not isinstance(node, Tag):
        return ""
    if node.name in SKIP_TAGS:
        return ""
    if node.name in ("script",) and node.get("type") == "application/ld+json":
        return ""  # skip structured data blocks

    name = node.name
    if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
        level = int(name[1])
        text = "".join(inline_md(c, page_url) for c in node.children).strip()
        return f"{'#' * level} {text}\n\n"
    if name == "p":
        text = "".join(inline_md(c, page_url) for c in node.children).strip()
        return f"{text}\n\n" if text else ""
    if name in ("ul", "ol"):
        out = []
        for i, li in enumerate(node.find_all("li", recursive=False)):
            text = "".join(inline_md(c, page_url) for c in li.children).strip()
            text = re.sub(r"\n{2,}", " ", text)
            bullet = f"{i+1}." if name == "ol" else "-"
            out.append(f"{bullet} {text}")
        return "\n".join(out) + "\n\n"
    if name == "blockquote":
        inner = render_children(node, page_url).strip()
        quoted = "\n".join("> " + line for line in inner.split("\n"))
        return quoted + "\n\n"
    if name == "details":
        summary = node.find("summary")
        body = "".join(render(c, page_url=page_url) for c in node.children if c is not summary)
        s = "".join(inline_md(c, page_url) for c in summary.children).strip() if summary else "Details"
        return f"**{s}**\n\n{body}"
    if name in ("picture", "figure"):
        return ""  # skip media blocks
    if name == "section" or name == "article" or name == "div" or name == "header" or name == "footer":
        return render_children(node, page_url)
    if name == "hr":
        return "\n---\n\n"
    return ""

def render_children(node, page_url=BASE_URL + "/"):
    return "".join(render(c, page_url=page_url) for c in node.children)

def clean_md(s):
    # Collapse 3+ newlines to 2; strip leading whitespace on lines
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = "\n".join(line.rstrip() for line in s.split("\n"))
    return s.strip() + "\n"

def html_to_md(html_path: Path, page_url: str):
    html = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    # Use <main> if present, else body
    main = soup.find("main")
    if main is None:
        main = soup.body or soup
    # Drop the breadcrumb nav to avoid noise
    for nav in main.find_all("nav", class_="breadcrumb"):
        nav.decompose()
    md = render_children(main, page_url)
    return clean_md(md)

# ---------------------------------------------------------------------------
# Build llms-full.txt
# ---------------------------------------------------------------------------

INTRO = (
    "AI-powered wedding video services for couples worldwide. We restore old footage, "
    "create cinematic AI films, generate multilingual versions, and personalize videos "
    "with cartoon styles, memes, pet weddings, and tributes. Founded 2024, serving 500+ "
    "couples across 12+ countries."
)

SECTIONS = {
    "Core Services": [
        ("/services/",                                                              "All Services"),
        ("/services/video-enhancement/slow-motion.html",                            "AI Slow Motion"),
        ("/services/video-enhancement/vintage-restoration.html",                   "Vintage Footage Restoration"),
        ("/services/personalization/wedding-trailer.html",                          "Wedding Trailer"),
        ("/services/personalization/ai-video-generator.html",                       "AI Video Generator"),
    ],
    "Absence Compensation": [
        ("/services/absence-compensation/family-tribute.html",                      "Family Tribute"),
        ("/services/absence-compensation/family-message.html",                      "Family Message"),
        ("/services/absence-compensation/celebrity-message.html",                   "Celebrity Wedding Messages"),
    ],
    "Personalization": [
        ("/services/personalization/cartoon-style.html",                            "Cartoon Style"),
        ("/services/personalization/multilingual.html",                             "Multilingual"),
        ("/services/personalization/pet-wedding.html",                              "Pet Wedding"),
        ("/services/personalization/meme-generator.html",                           "Wedding GIFs & Memes"),
    ],
    "Pricing & Quotes": [
        ("/order.html",                                                             "Get a Free Quote"),
    ],
    "Company": [
        ("/about.html",                                                             "About Us"),
        ("/gallery.html",                                                           "Gallery & Case Studies"),
        ("/resources.html",                                                         "Resources & Guides"),
    ],
    "Legal & Contact": [
        ("/privacy.html",                                                           "Privacy Policy"),
        ("/terms.html",                                                             "Terms of Service"),
        ("mailto:order@weddingai.video",                                            "Contact / Email"),
    ],
}

URL_TO_LOCAL = {
    "/services/":                                              ROOT / "services" / "index.html",
    "/services/video-enhancement/slow-motion.html":            ROOT / "services" / "video-enhancement" / "slow-motion.html",
    "/services/video-enhancement/vintage-restoration.html":   ROOT / "services" / "video-enhancement" / "vintage-restoration.html",
    "/services/personalization/wedding-trailer.html":          ROOT / "services" / "personalization" / "wedding-trailer.html",
    "/services/personalization/ai-video-generator.html":       ROOT / "services" / "personalization" / "ai-video-generator.html",
    "/services/absence-compensation/family-tribute.html":      ROOT / "services" / "absence-compensation" / "family-tribute.html",
    "/services/absence-compensation/family-message.html":      ROOT / "services" / "absence-compensation" / "family-message.html",
    "/services/absence-compensation/celebrity-message.html":   ROOT / "services" / "absence-compensation" / "celebrity-message.html",
    "/services/personalization/cartoon-style.html":            ROOT / "services" / "personalization" / "cartoon-style.html",
    "/services/personalization/multilingual.html":             ROOT / "services" / "personalization" / "multilingual.html",
    "/services/personalization/pet-wedding.html":              ROOT / "services" / "personalization" / "pet-wedding.html",
    "/services/personalization/meme-generator.html":           ROOT / "services" / "personalization" / "meme-generator.html",
    "/order.html":                                             ROOT / "order.html",
    "/about.html":                                             ROOT / "about.html",
    "/gallery.html":                                           ROOT / "gallery.html",
    "/resources.html":                                         ROOT / "resources.html",
    "/privacy.html":                                           ROOT / "privacy.html",
    "/terms.html":                                             ROOT / "terms.html",
}

def main():
    out = []
    out.append("# WeddingAI.video\n")
    out.append(f"\n> {INTRO}\n\n")
    out.append("Full content of each linked page follows the link list. "
               "This file is the 'full' variant of llms.txt per the llmstxt.org spec; "
               "use it to give an LLM complete site context in a single fetch.\n\n")

    for section_name, items in SECTIONS.items():
        out.append(f"## {section_name}\n\n")
        for url, label in items:
            full_url = url if url.startswith("http") or url.startswith("mailto:") else BASE_URL + url
            out.append(f"### [{label}]({full_url})\n\n")
            if url.startswith("mailto:"):
                out.append(f"Email: {url.replace('mailto:', '')}\n\n")
                continue
            local = URL_TO_LOCAL.get(url)
            if local and local.exists():
                md = html_to_md(local, full_url)
                if md:
                    out.append(md)
                    out.append("\n")
                else:
                    out.append("(page is empty)\n\n")
            else:
                out.append(f"_(local source: {local})_\n\n" if local else "_(external link)_\n\n")
        out.append("\n")

    out.append("## Optional\n\n")
    out.append("- [Sitemap](https://weddingai.video/sitemap.xml): Full XML sitemap with image metadata.\n")
    out.append("- [Robots.txt](https://weddingai.video/robots.txt): Crawler rules and sitemap reference.\n")
    out.append("- [llms.txt](https://weddingai.video/llms.txt): Brief link-only version of this file.\n")

    text = "".join(out)
    (ROOT / "llms-full.txt").write_text(text, encoding="utf-8")
    size_kb = len(text) / 1024
    print(f"[ok] llms-full.txt generated: {size_kb:.1f} KB ({len(text):,} bytes)")

if __name__ == "__main__":
    main()
