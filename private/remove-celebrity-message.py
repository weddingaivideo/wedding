"""
Remove ALL references to /services/absence-compensation/celebrity-message/ across the
weddingai.video static site. Sister script to the physical-file move into tmp/_trash_celebrity/.

Run from the weddingai repo root:
    py private/remove-celebrity-message.py

What it touches (auto):
  1. Every HTML file with nav/footer/service-card/option/HINTS/gallery-card/blog-list
     references that contain the literal string "celebrity" (preserved keys excluded)
  2. 11 sitemap-*.xml files (drops the <url> block + hreflang alternates)
  3. 10 i18n/*.json files (drops orphan translation keys; PRESERVES the "Home" key
     `services.absence-compensation.celebrity-message.a_text.home.90820803` which is
     used by every page's breadcrumb despite the misleading name)
  4. llms.txt + llms-full.txt (drops the Celebrity Wedding Messages entry/section)
  5. functions/api/quote.js (drops "celebrity-message" from SERVICE_LABELS)
  6. scripts/generate-service-category-indexes.py (drops NAV_ITEMS + group child)
  7. scripts/restructure-services-nav.py (drops the nav <li>)
  8. scripts/unlink-gallery-filter-params.py (drops the file path)

What it does NOT touch (and why):
  - scripts/archive/* — historical, never runs
  - private/architecture.html — not deployed (private/* 404s in _redirects)
  - tmp/_trash_celebrity/ — quarantined physical files
  - _redirects — handled by hand so the 308→301 change stays auditable
  - articles/47-wedding-video-cost-2026.md — handled by hand (line-by-line edits)
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")

# ---------------------------------------------------------------------------
# HTML rewrites — patterns are applied in order; first match wins.
# ---------------------------------------------------------------------------

# 1) Inline <li role="none"> and <li> blocks wrapping a celebrity link.
#    The blocks in this site are always single-line. Examples:
#      <li role="none"><a role="menuitem" href="/services/absence-compensation/celebrity-message/" ...>Celebrity Message</a></li>
#      <li><a href="/services/absence-compensation/celebrity-message/" ...>Celebrity Message</a></li>
LI_RE = re.compile(
    r'^[ \t]*<li(?:\s+role="none")?>(?:(?!</li>).)*?celebrity-message(?:(?!</li>).)*?</li>[ \t]*\r?\n',
    re.MULTILINE,
)

# 1b) <button> filter row in gallery/index.html.
BUTTON_RE = re.compile(
    r'^[ \t]*<button class="filter-btn" data-filter="celebrity-message"[^>]*>[^<]*</button>[ \t]*\r?\n',
    re.MULTILINE,
)

# 1c) Inline <li> with descriptive body text mentioning "celebrity" (e.g. blog
#     premium-budget bullet). The literal text "celebrity message" appears in
#     the body of the <li>.
LI_TEXT_RE = re.compile(
    r'^[ \t]*<li[^>]*>(?:(?!</li>).)*?\bcelebrity message\b(?:(?!</li>).)*?</li>[ \t]*\r?\n',
    re.MULTILINE,
)

# 2) <option value="celebrity-message" ...>...</option>  (order/index.html)
OPTION_RE = re.compile(
    r'^[ \t]*<option[^>]*\bvalue="celebrity-message"[^>]*>[^<]*</option>[ \t]*\r?\n',
    re.MULTILINE,
)

# 3) HINTS dict line in order/index.html — single line, comma-terminated.
HINTS_RE = re.compile(
    r"^[ \t]*'celebrity-message':\s*\{[^}]*\},\s*\r?\n",
    re.MULTILINE,
)

# 4) Gallery card blocks (multi-line). Two <article class="gallery-card"
#    data-category="celebrity-message"> blocks live in gallery/index.html.
GALLERY_CARD_RE = re.compile(
    r'[ \t]*<article class="gallery-card" data-category="celebrity-message">.*?</article>\r?\n?',
    re.DOTALL,
)

# 5) Service sub-card block on services/index.html and
#    services/absence-compensation/index.html. The <picture> + h3 + p + span
#    all live inside one <div class="service-sub-card"> ... </div>.
SUB_CARD_RE = re.compile(
    r'[ \t]*<div class="service-sub-card">\s*'
    r'<picture>(?:(?!</picture>).)*celebrity-message(?:(?!</picture>).)*?</picture>'
    r'(?:(?!</div>).)*?</div>[ \t]*\r?\n',
    re.DOTALL,
)

# 6) Homepage <article class="service-card service-card-compact"> block.
HOME_CARD_RE = re.compile(
    r'[ \t]*<article class="service-card service-card-compact">\s*'
    r'<a href="/services/absence-compensation/celebrity-message/"[^>]*>'
    r'.*?</a>\s*</article>\r?\n?',
    re.DOTALL,
)

# 7) Related-card <a> in family-tribute (multi-line block).
RELATED_CARD_RE = re.compile(
    r'[ \t]*<a href="/services/absence-compensation/celebrity-message/" class="related-card"[^>]*>'
    r'.*?</a>[ \t]*\r?\n',
    re.DOTALL,
)

# 8) search/index.html "Includes" list line — references celebrity-message
#    inside a single <li> with two other links. We match the whole <li> line.
SEARCH_INCLUDES_RE = re.compile(
    r'^[ \t]*<li[^>]*>(?:(?!</li>).)*?celebrity-message(?:(?!</li>).)*?</li>[ \t]*\r?\n',
    re.MULTILINE,
)

# 9) search/index.html "title: 'Celebrity-Style Wedding Message'" entry in the
#    inline JS index. Single line, terminated by `,`.
SEARCH_INDEX_RE = re.compile(
    r'^[ \t]*\{ title: "Celebrity-Style Wedding Message", url: "/services/absence-compensation/celebrity-message/", desc: "AI-generated celebrity-style wedding message for fun and shareable content\.", tags: \[[^\]]+\] \},[ \t]*\r?\n',
    re.MULTILINE,
)

# 10) pricing/index.html pricing table row. The <tr> wraps 3 <td>s and spans
#     multiple physical lines.
PRICING_ROW_RE = re.compile(
    r'[ \t]*<tr[^>]*>(?:(?!</tr>).)*?celebrity-message(?:(?!</tr>).)*?</tr>[ \t]*\r?\n',
    re.DOTALL,
)

# 11) blog/wedding-video-cost-2026*/index.html: the "WeddingAI.video Service
#     Pricing" line that contains a markdown table row with
#     "| Celebrity/Influencer Message | $199-$499 | ... |". The line is one
#     long <p> with a data-i18n attr that translates the entire table.
PRICING_TABLE_P_RE = re.compile(
    r'^[ \t]*<p[^>]*>(?:(?!</p>).)*?\| Celebrity/Influencer Message \|[^|]*\|[^|]*\|(?:(?!</p>).)*?</p>[ \t]*\r?\n',
    re.MULTILINE,
)

HTML_RULES = [
    ("LI block (nav/footer)",          LI_RE),
    ("BUTTON filter row",              BUTTON_RE),
    ("LI text (descriptive body)",     LI_TEXT_RE),
    ("OPTION select",                  OPTION_RE),
    ("HINTS dict line",                HINTS_RE),
    ("GALLERY <article> block",        GALLERY_CARD_RE),
    ("SERVICE-SUB-CARD <div> block",   SUB_CARD_RE),
    ("HOMEPAGE service-card block",    HOME_CARD_RE),
    ("RELATED-CARD <a> block",         RELATED_CARD_RE),
    ("SEARCH 'Includes' <li>",         SEARCH_INCLUDES_RE),
    ("SEARCH index entry",             SEARCH_INDEX_RE),
    ("PRICING <tr> row",               PRICING_ROW_RE),
    ("PRICING <p> with table",         PRICING_TABLE_P_RE),
]


def rewrite_html(path: Path) -> tuple[int, dict[str, int]]:
    text = path.read_text(encoding="utf-8")
    before = text
    counts: dict[str, int] = {}
    for label, rx in HTML_RULES:
        new = rx.sub("", text)
        n = text.count("celebrity-message") + text.count("Celebrity Message") + text.count("Celebrity-Style") - (
            new.count("celebrity-message") + new.count("Celebrity Message") + new.count("Celebrity-Style")
        )
        # Some patterns also remove non-celebrity-message "celebrity" mentions
        # (e.g. celebrity_message in data-i18n, "Celebrity Message" text in
        # the <li> body, or the literal string "celebrity" in i18n keys); the
        # count above is approximate. Trust it for reporting.
        if new != text:
            counts[label] = max(n, 1)
        text = new
    if text != before:
        path.write_text(text, encoding="utf-8")
    return sum(counts.values()), counts


# ---------------------------------------------------------------------------
# Sitemap rewrites
# ---------------------------------------------------------------------------

SITEMAP_URL_RE = re.compile(
    r'[ \t]*<url>\s*'
    r'<loc>https://weddingai\.video/(?:[a-z]{2}/)?services/absence-compensation/celebrity-message/</loc>'
    r'.*?</url>\r?\n?',
    re.DOTALL,
)


def rewrite_sitemap(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    new = SITEMAP_URL_RE.sub("", text)
    if new != text:
        path.write_text(new, encoding="utf-8")
        return 1
    return 0


# ---------------------------------------------------------------------------
# i18n JSON rewrites
# ---------------------------------------------------------------------------

# Preserved keys: the "Home" translation that every page's breadcrumb references
# via data-i18n, despite the misleading "celebrity-message" prefix in the key.
PRESERVE_KEYS = {
    "services.absence-compensation.celebrity-message.a_text.home.90820803",
}


def rewrite_i18n(path: Path) -> int:
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    to_delete = [k for k in list(data.keys()) if k not in PRESERVE_KEYS and "celebrity" in k.lower()]
    if not to_delete:
        return 0
    ordered = [(k, v) for k, v in json.loads(raw, object_pairs_hook=list) if k not in set(to_delete)]
    path.write_text(
        json.dumps(dict(ordered), ensure_ascii=False, indent=2, separators=(",", ": ")) + "\n",
        encoding="utf-8",
    )
    return len(to_delete)


# ---------------------------------------------------------------------------
# Targeted single-file rewrites
# ---------------------------------------------------------------------------

LLMS_TXT_RE = re.compile(
    r'^- \[Celebrity Wedding Messages[^\n]*\n',
    re.MULTILINE,
)

LLMS_FULL_RE = re.compile(
    r'### \[Celebrity Wedding Messages\]\(https://weddingai\.video/services/absence-compensation/celebrity-message\.html\)\n\n'
    r'_\(local source: C:\\Users\\qiaoshan\\\.openclaw\\workspace\\weddingai\\services\\absence-compensation\\celebrity-message\.html\)_\n\n',
)

QUOTE_LABEL_RE = re.compile(
    r'^[ \t]*"celebrity-message": "Celebrity Message",\r?\n',
    re.MULTILINE,
)


def rewrite_quote_js(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    new = QUOTE_LABEL_RE.sub("", text)
    if new != text:
        path.write_text(new, encoding="utf-8")
        return 1
    return 0


GEN_CAT_NAV_RE = re.compile(
    r'^[ \t]*\("/services/absence-compensation/celebrity-message/","404\.a_text\.celebrity_message\.59529435","Celebrity Message"\),\r?\n',
    re.MULTILINE,
)

GEN_CAT_CHILD_RE = re.compile(
    r'[ \t]*\{\r?\n'
    r'[ \t]*"href": "/services/absence-compensation/celebrity-message/",\r?\n'
    r'[ \t]*"title": "Celebrity-Style Wedding Message",\r?\n'
    r'[ \t]*"title_i18n": "404\.a_text\.celebrity_message\.59529435",\r?\n'
    r'[ \t]*"desc": "AI-generated celebrity-style wedding message for fun and shareable content\.",\r?\n'
    r'[ \t]*"desc_i18n": "services\.p_text\.ai_generated_celebrity_style_wedding_mes\.09663712",\r?\n'
    r'[ \t]*"price": "From \$499",\r?\n'
    r'[ \t]*"price_i18n": "services\.span_text\.from_499\.68608774",\r?\n'
    r'[ \t]*"img": "catalog-celebrity-message",\r?\n'
    r'[ \t]*"alt": "Glamorous celebrity style wedding moment",\r?\n'
    r'[ \t]*\},\r?\n',
    re.MULTILINE,
)

RESTRUCTURE_NAV_RE = re.compile(
    r'^[ \t]*<li role="none"><a role="menuitem" href="/services/absence-compensation/celebrity-message/" data-i18n="404\.a_text\.celebrity_message\.59529435">Celebrity Message</a></li>\r?\n',
    re.MULTILINE,
)

UNLINK_PATH_RE = re.compile(
    r'^[ \t]*"services/absence-compensation/celebrity-message/index\.html",\r?\n',
    re.MULTILINE,
)


def rewrite_targeted(path: Path, rx: re.Pattern, label: str) -> int:
    text = path.read_text(encoding="utf-8")
    new = rx.sub("", text)
    if new != text:
        path.write_text(new, encoding="utf-8")
        print(f"  [{label}] {path.relative_to(ROOT)}")
        return 1
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("=== HTML files ===")
    html_files = list(ROOT.rglob("*.html"))
    html_files = [p for p in html_files if "_trash_celebrity" not in p.parts and "private" not in p.parts]
    html_changed = 0
    html_total = 0
    for p in html_files:
        n, _ = rewrite_html(p)
        if n:
            html_changed += 1
            html_total += n
            print(f"  [{n:>3} hits] {p.relative_to(ROOT)}")
    print(f"  -> {html_changed} files changed, ~{html_total} references removed\n")

    print("=== Sitemap files ===")
    sitemap_files = sorted(ROOT.glob("sitemap*.xml"))
    sitemap_total = 0
    for p in sitemap_files:
        n = rewrite_sitemap(p)
        if n:
            sitemap_total += n
            print(f"  [{n:>3} url blocks] {p.relative_to(ROOT)}")
    print(f"  -> {sitemap_total} url blocks removed\n")

    print("=== i18n JSON files ===")
    i18n_files = sorted(ROOT.glob("i18n/*.json"))
    i18n_total = 0
    for p in i18n_files:
        n = rewrite_i18n(p)
        if n:
            i18n_total += n
            print(f"  [{n:>3} keys] {p.relative_to(ROOT)}")
    print(f"  -> {i18n_total} orphan keys removed (Home key preserved)\n")

    print("=== Targeted single-file rewrites ===")
    targeted = 0
    targeted += rewrite_targeted(ROOT / "llms.txt", LLMS_TXT_RE, "llms.txt")
    targeted += rewrite_targeted(ROOT / "llms-full.txt", LLMS_FULL_RE, "llms-full.txt")
    targeted += rewrite_quote_js(ROOT / "functions/api/quote.js")
    if rewrite_quote_js(ROOT / "functions/api/quote.js") == 0:
        pass  # already counted
    else:
        print(f"  [SERVICE_LABELS] {ROOT.relative_to(ROOT)}functions/api/quote.js")
    gen = ROOT / "scripts/generate-service-category-indexes.py"
    targeted += rewrite_targeted(gen, GEN_CAT_NAV_RE, "gen-cat (NAV_ITEMS)")
    targeted += rewrite_targeted(gen, GEN_CAT_CHILD_RE, "gen-cat (absence-compensation child)")
    restr = ROOT / "scripts/restructure-services-nav.py"
    targeted += rewrite_targeted(restr, RESTRUCTURE_NAV_RE, "restructure-services-nav")
    unlink = ROOT / "scripts/unlink-gallery-filter-params.py"
    targeted += rewrite_targeted(unlink, UNLINK_PATH_RE, "unlink-gallery-filter-params")
    print(f"  -> {targeted} targeted rewrites done\n")

    print("=== Summary ===")
    print(f"  HTML files:    {html_changed} changed")
    print(f"  Sitemap url:   {sitemap_total} blocks")
    print(f"  i18n keys:     {i18n_total}")
    print(f"  Targeted:      {targeted}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
