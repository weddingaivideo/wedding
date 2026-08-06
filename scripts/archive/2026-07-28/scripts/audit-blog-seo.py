"""SEO audit for all blog pages. Reports missing/weak SEO elements."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"
ARTICLE = (ROOT / "articles").glob("*.md")

print("=== Blog SEO Audit ===\n")

issues = {
    "missing_og_image": [],
    "missing_jsonld": [],
    "missing_h1": [],
    "h1_too_many": [],
    "missing_canonical": [],
    "missing_meta_keyword": [],
    "title_too_long": [],
    "desc_too_long": [],
    "no_internal_links": [],
    "no_external_links": [],
    "thin_content": [],  # < 600 words
    "missing_alt": [],
    "weak_alt": [],
    "no_og_locale": [],
}

# Cache frontmatter word counts
fm_words = {}
for md in ARTICLE:
    text = md.read_text(encoding="utf-8")
    m = re.match(r"---\s*\n(.*?)\n---", text, re.DOTALL)
    if m:
        fm = m.group(1)
        wm = re.search(r"word_count_target:\s*(\d+)", fm)
        if wm:
            fm_words[md.stem] = int(wm.group(1))

for f in sorted(BLOG.rglob("*.html")):
    rel = f.relative_to(BLOG)
    is_list = rel == Path("index.html")
    text = f.read_text(encoding="utf-8")
    slug = f.parent.name if not is_list else "LIST"

    # 1. og:image
    if 'property="og:image"' not in text:
        issues["missing_og_image"].append(slug)

    # 2. JSON-LD
    if 'application/ld+json' not in text:
        issues["missing_jsonld"].append(slug)

    # 3. H1 count
    h1_count = text.count("<h1>")
    if h1_count == 0 and not is_list:
        issues["missing_h1"].append(slug)
    elif h1_count > 1 and not is_list:
        issues["h1_too_many"].append(slug)

    # 4. canonical
    if 'rel="canonical"' not in text:
        issues["missing_canonical"].append(slug)

    # 5. meta keyword
    if 'name="keywords"' not in text:
        issues["missing_meta_keyword"].append(slug)

    # 6. title length
    m = re.search(r"<title>([^<]+)</title>", text)
    if m and len(m.group(1)) > 60:
        issues["title_too_long"].append(slug)

    # 7. desc length
    m = re.search(r'<meta name="description" content="([^"]+)"', text)
    if m and len(m.group(1)) > 160:
        issues["desc_too_long"].append(slug)

    # 8. internal links (to other weddingai.video pages)
    if not is_list:
        internal = re.findall(r'href="(/[^"]+|https://weddingai\.video/[^"]+)"', text)
        # exclude self-link
        real_internal = [l for l in internal if slug not in l]
        if not real_internal:
            issues["no_internal_links"].append(slug)

    # 9. external links
    if not is_list:
        ext = re.findall(r'href="https?://(?!weddingai\.video)[^"]+"', text)
        if not ext:
            issues["no_external_links"].append(slug)

    # 10. content word count (rough, strip HTML)
    if not is_list:
        # Take only blog-article section
        m = re.search(r'<div class="blog-article"[^>]*>(.*?)</div>\s*</div>\s*</section>', text, re.DOTALL)
        body = m.group(1) if m else text
        body_text = re.sub(r"<[^>]+>", " ", body)
        body_text = re.sub(r"\s+", " ", body_text).strip()
        words = len(body_text.split())
        if words < 600:
            issues["thin_content"].append((slug, words))

    # 11/12. img alt
    if not is_list:
        for img in re.finditer(r"<img[^>]+>", text):
            attrs = img.group(0)
            if "alt=" not in attrs:
                issues["missing_alt"].append(slug)
                break
            m = re.search(r'alt="([^"]*)"', attrs)
            if m and (len(m.group(1)) < 10 or m.group(1) in ("image", "img", "photo", "picture", "wedding")):
                issues["weak_alt"].append(slug)
                break

# Report
for k, v in issues.items():
    if v:
        if k == "thin_content":
            print(f"[{len(v):3d}] {k}:")
            for slug, w in v[:5]:
                print(f"        {slug} ({w} words)")
        else:
            print(f"[{len(v):3d}] {k}: {', '.join(str(x) for x in v[:5])}{' ...' if len(v) > 5 else ''}")

print(f"\nTotal blog HTML files: {len(list(BLOG.rglob('*.html')))}")
print(f"Total articles:        {len(list((ROOT / 'articles').glob('*.md')))}")
