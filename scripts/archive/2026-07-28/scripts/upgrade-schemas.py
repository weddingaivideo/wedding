#!/usr/bin/env python3
"""
One-shot schema upgrade for WeddingAI.video (v3.7.0).

Tasks:
  1. Convert index.html's `Product` schema to `Service` (drop `brand`,
     add `serviceType`, `provider`, `areaServed`, `offers`).
  2. Add `FAQPage` schema to every page with `<details class="faq-item">`
     that doesn't already have one.
  3. Add `BreadcrumbList` schema to pages missing it (resources.html,
     search.html).

Idempotent — re-running is a no-op.
"""
import os
import re
import json
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")

# Skip this file (Google verification placeholder)
SKIP = {"google-site-verification.html"}

# Page -> breadcrumb path (name, url). The root `/` is always added.
BREADCRUMBS = {
    "index.html":            None,  # homepage: no BreadcrumbList
    "about.html":            [("About Us", "/about")],
    "gallery.html":          [("Gallery", "/gallery")],
    "order.html":            [("Get a Quote", "/order")],
    "privacy.html":          [("Privacy Policy", "/privacy")],
    "terms.html":            [("Terms of Service", "/terms")],
    "search.html":           [("Search", "/search")],
    "resources.html":        [("Resources & Guides", "/resources")],
    "success.html":          [("Thank You", "/success")],
    "services/index.html":   [("Services", "/services/")],
    "services/absence-compensation/celebrity-message.html": [
        ("Services", "/services/"),
        ("Absence Compensation", "/services/#absence-compensation"),
        ("Celebrity Message", "/services/absence-compensation/celebrity-message"),
    ],
    "services/absence-compensation/family-message.html": [
        ("Services", "/services/"),
        ("Absence Compensation", "/services/#absence-compensation"),
        ("Family Message", "/services/absence-compensation/family-message"),
    ],
    "services/absence-compensation/family-tribute.html": [
        ("Services", "/services/"),
        ("Absence Compensation", "/services/#absence-compensation"),
        ("Family Tribute", "/services/absence-compensation/family-tribute"),
    ],
    "services/personalization/ai-video-generator.html": [
        ("Services", "/services/"),
        ("Personalization", "/services/#personalization"),
        ("AI Video Generator", "/services/personalization/ai-video-generator"),
    ],
    "services/personalization/cartoon-style.html": [
        ("Services", "/services/"),
        ("Personalization", "/services/#personalization"),
        ("Cartoon Style", "/services/personalization/cartoon-style"),
    ],
    "services/personalization/meme-generator.html": [
        ("Services", "/services/"),
        ("Personalization", "/services/#personalization"),
        ("Meme Generator", "/services/personalization/meme-generator"),
    ],
    "services/personalization/multilingual.html": [
        ("Services", "/services/"),
        ("Personalization", "/services/#personalization"),
        ("Multilingual", "/services/personalization/multilingual"),
    ],
    "services/personalization/pet-wedding.html": [
        ("Services", "/services/"),
        ("Personalization", "/services/#personalization"),
        ("Pet Wedding", "/services/personalization/pet-wedding"),
    ],
    "services/personalization/wedding-trailer.html": [
        ("Services", "/services/"),
        ("Personalization", "/services/#personalization"),
        ("Wedding Trailer", "/services/personalization/wedding-trailer"),
    ],
    "services/video-enhancement/slow-motion.html": [
        ("Services", "/services/"),
        ("Video Enhancement", "/services/#video-enhancement"),
        ("Slow Motion", "/services/video-enhancement/slow-motion"),
    ],
}

# 11 countries we serve (matches existing service page schemas)
COUNTRIES = ["US", "UK", "Germany", "France", "Italy", "Spain",
             "Australia", "Canada", "India", "China", "Japan"]


def iter_html_files():
    for p in ROOT.rglob("*.html"):
        if p.name in SKIP:
            continue
        if "__pycache__" in p.parts or "scripts" in p.parts:
            continue
        yield p


def relpath(p: Path) -> str:
    return str(p.relative_to(ROOT)).replace("\\", "/")


# ---------------------------------------------------------------------
# 1. Product -> Service (index.html only)
# ---------------------------------------------------------------------

def convert_product_to_service(text: str) -> tuple[str, int]:
    """Convert the @type:Product schema on index.html to @type:Service."""
    if '"@type": "Product"' not in text:
        return text, 0

    # Find the <script> wrapper that contains the Product schema.
    # Each <script type="application/ld+json"> block contains a single JSON
    # object. Find the one that has "@type": "Product".
    script_re = re.compile(
        r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>',
        re.DOTALL,
    )
    for m in script_re.finditer(text):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if data.get("@type") != "Product":
            continue

        # Transform
        data.pop("brand", None)
        data["@type"] = "Service"
        data["serviceType"] = "AI Wedding Video Services"
        data.setdefault("provider", {"@id": "https://weddingai.video/#organization"})
        data.setdefault("url", "https://weddingai.video/")
        if "areaServed" not in data:
            data["areaServed"] = [{"@type": "Country", "name": c} for c in COUNTRIES]
        if "offers" not in data:
            data["offers"] = {
                "@type": "Offer",
                "url": "https://weddingai.video/services",
                "priceCurrency": "USD",
                "price": "49",
                "priceSpecification": {
                    "@type": "PriceSpecification",
                    "priceCurrency": "USD",
                    "minPrice": "49",
                    "price": "49",
                },
                "availability": "https://schema.org/InStock",
            }

        # Serialize and re-indent to match the surrounding 4-space convention
        new_json = json.dumps(data, indent=4, ensure_ascii=False)
        # Indent every line by 4 spaces (the file's <script> bodies are
        # nested one level beyond the <script> tag itself)
        new_block = (
            '<script type="application/ld+json">\n'
            '    ' + new_json.replace('\n', '\n    ') + '\n'
            '    </script>'
        )
        return text[:m.start()] + new_block + text[m.end():], 1

    return text, 0


# ---------------------------------------------------------------------
# 2. FAQPage generation
# ---------------------------------------------------------------------

FAQ_DETAILS_RE = re.compile(
    r'<details class="faq-item">\s*<summary>(?P<q>[^<]+)</summary>\s*<p>(?P<a>.*?)</p>\s*</details>',
    re.DOTALL,
)
# Alternate pattern used by pet-wedding.html: <div class="faq-item"><h3>?</h3><p>?</p></div>
FAQ_DIV_RE = re.compile(
    r'<div class="faq-item">\s*<h3>(?P<q>[^<]+)</h3>\s*<p>(?P<a>.*?)</p>\s*</div>',
    re.DOTALL,
)


def extract_faqs(text: str) -> list[tuple[str, str]]:
    items = [(m.group("q").strip(), m.group("a").strip())
             for m in FAQ_DETAILS_RE.finditer(text)]
    items += [(m.group("q").strip(), m.group("a").strip())
              for m in FAQ_DIV_RE.finditer(text)]
    return items


def has_faqpage(text: str) -> bool:
    return '"@type": "FAQPage"' in text or '"@type":"FAQPage"' in text


def add_faqpage(text: str) -> tuple[str, int]:
    if has_faqpage(text):
        return text, 0
    faqs = extract_faqs(text)
    if not faqs:
        return text, 0

    main_entity = []
    for q, a in faqs:
        q_esc = q.replace("\\", "\\\\").replace('"', '\\"')
        a_esc = a.replace("\\", "\\\\").replace('"', '\\"')
        main_entity.append(
            '            {\n'
            '                "@type": "Question",\n'
            f'                "name": "{q_esc}",\n'
            '                "acceptedAnswer": {\n'
            '                    "@type": "Answer",\n'
            f'                    "text": "{a_esc}"\n'
            '                }\n'
            '            }'
        )
    body = ',\n'.join(main_entity)
    script = (
        '<script type="application/ld+json">\n'
        '    {\n'
        '        "@context": "https://schema.org",\n'
        '        "@type": "FAQPage",\n'
        '        "mainEntity": [\n'
        f'{body}\n'
        '        ]\n'
        '    }\n'
        '    </script>'
    )
    if '<footer' in text:
        text = text.replace('<footer', script + '\n\n\n    <footer', 1)
    else:
        text = text.replace('</body>', script + '\n\n</body>', 1)
    return text, 1


# ---------------------------------------------------------------------
# 3. BreadcrumbList generation
# ---------------------------------------------------------------------

def has_breadcrumb(text: str) -> bool:
    return '"@type": "BreadcrumbList"' in text or '"@type":"BreadcrumbList"' in text


def add_breadcrumb(text: str, rel: str) -> tuple[str, int]:
    if has_breadcrumb(text):
        return text, 0
    crumbs = BREADCRUMBS.get(rel)
    if not crumbs:
        return text, 0

    items = ['            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://weddingai.video/"}']
    for i, (name, url) in enumerate(crumbs, start=2):
        items.append(
            f'            {{"@type": "ListItem", "position": {i}, '
            f'"name": "{name}", "item": "https://weddingai.video{url}"}}'
        )
    body = ',\n'.join(items)
    script = (
        '<script type="application/ld+json">\n'
        '    {\n'
        '        "@context": "https://schema.org",\n'
        '        "@type": "BreadcrumbList",\n'
        '        "itemListElement": [\n'
        f'{body}\n'
        '        ]\n'
        '    }\n'
        '    </script>'
    )
    if '<footer' in text:
        text = text.replace('<footer', script + '\n\n\n    <footer', 1)
    else:
        text = text.replace('</body>', script + '\n\n</body>', 1)
    return text, 1


# ---------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------

def process_file(p: Path) -> dict:
    rel = relpath(p)
    text = p.read_text(encoding="utf-8")
    out = text
    stats = {"product_to_service": 0, "faqpage_added": 0, "breadcrumb_added": 0}

    out, n = convert_product_to_service(out)
    stats["product_to_service"] = n

    out, n = add_faqpage(out)
    stats["faqpage_added"] = n

    out, n = add_breadcrumb(out, rel)
    stats["breadcrumb_added"] = n

    if out != text:
        p.write_text(out, encoding="utf-8")
    return stats


def main():
    total = {"product_to_service": 0, "faqpage_added": 0, "breadcrumb_added": 0}
    for p in iter_html_files():
        s = process_file(p)
        if sum(s.values()) > 0:
            rel = relpath(p)
            print(f"  {rel}: P->S={s['product_to_service']}, FAQ+={s['faqpage_added']}, BC+={s['breadcrumb_added']}")
        for k, v in s.items():
            total[k] += v

    print()
    print(f"Product -> Service:   {total['product_to_service']} file(s)")
    print(f"FAQPage added:        {total['faqpage_added']} file(s)")
    print(f"Breadcrumb added:     {total['breadcrumb_added']} file(s)")


if __name__ == "__main__":
    main()
