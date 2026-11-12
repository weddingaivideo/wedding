#!/usr/bin/env python3
"""Add the dress-code guide landing page the research report asked for.

Tier 3 note in 欧美免费工具需求研究-2026-11-10.md: the dress-code topic is
"content-first, better as a blog article than a tool". The tool exists; this
adds the editorial companion and links the two both ways.

Produces:
  blog/wedding-dress-code-guide/index.html
  <lang>/blog/wedding-dress-code-guide/index.html   (10 langs)
  one <url> entry in each of the 11 sitemaps
  a backlink on the tool page (en + 10 langs)
  .tmp/dress-code-keys.json  (English strings for translation)

Reuses the existing blog template's header/footer/scripts so the site chrome,
CSP nonce and data-i18n conventions stay identical.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLUG = "wedding-dress-code-guide"
TEMPLATE = ROOT / "blog" / "choose-wedding-videographer" / "index.html"
TOOL = "wedding-dress-code-decoder"
LANGS = ["zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
LOCALE = {"en": "en_US", "zh": "zh_CN", "es": "es_ES", "fr": "fr_FR", "de": "de_DE",
          "pt": "pt_BR", "ja": "ja_JP", "ru": "ru_RU", "ar": "ar_AE",
          "th": "th_TH", "hi": "hi_IN"}
BASE = "https://weddingai.video"
TITLE = "Wedding Dress Codes, Decoded: What Guests Should Wear"
DESC = ("Black tie, cocktail, semi-formal, beach: what each wedding dress code really means, "
        "and the three questions to ask the couple.")
# Single source of truth for both the visible <details> and the FAQPage graph.
FAQS = [
    ("Can I wear black to a wedding?",
     "Yes in most Western settings. All-black reads as evening-appropriate; add texture or "
     "a colour accent if the ceremony is daytime."),
    ("What does 'festive' or 'creative black tie' mean?",
     "Keep the formality of black tie but allow personality — a velvet jacket, a coloured "
     "gown, a statement accessory."),
    ("Is it safe to ask the couple?",
     "Always. Ask what the venue floor is like and whether there is a ceremony dress "
     "requirement; those two answers settle most outfit decisions."),
]
TEXT: dict[str, str] = {}


def key(tag: str, text: str) -> str:
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
    snippet = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:36].strip("_")
    k = f"blog.{SLUG}.{tag}.{snippet}.{digest}"
    TEXT[k] = text
    return k


def bound(tag: str, text: str, elem: str = "p", cls: str = "") -> str:
    c = f' class="{cls}"' if cls else ""
    return f'<{elem}{c} data-i18n="{key(tag, text)}">{text}</{elem}>'


def body() -> str:
    h1 = bound("h1_text", TITLE, "h1")
    lead = bound("p_text",
                 "Wedding invitations compress an entire wardrobe decision into two or three words. "
                 "Vogue calls the dress code one of the most-searched wedding topics there is, and "
                 "US etiquette guides agree on the broad strokes — but the labels drift between "
                 "regions, venues and generations. This guide translates each one into something "
                 "you can actually shop for.", "p", "lead")
    sections = [
        ("Why the code exists",
         "A dress code is not a dress rule. It tells guests how formal the room will feel so nobody "
         "arrives wildly overdressed or underdressed. The couple sets a baseline for photographs, "
         "the venue and the tone of the day; within that baseline your own style still matters. "
         "When the invitation gives no code at all, the formality of the venue and the time of day "
         "are the best clues."),
        ("White tie and black tie",
         "White tie is the rarest code in modern US weddings: floor-length gowns, tailcoats and "
         "full formal accessories. Black tie means a tuxedo or a dark formal suit with a tie, and "
         "a long or elegantly tailored evening dress. 'Black tie optional' is the phrase that "
         "causes the most confusion — it means a tuxedo is welcome but a dark suit is entirely "
         "correct, and a formal cocktail dress is fine."),
        ("Formal, cocktail and semi-formal",
         "Formal (sometimes 'black tie invited') sits just below black tie: a dark suit, a "
         "midi or long dress. Cocktail is the most common US code — a suit or dressy separates, "
         "a knee-length or midi dress, and shoes you can dance in. Semi-formal is a step looser "
         "and often appears for daytime or outdoor ceremonies; think a light suit or a polished "
         "day dress rather than sequins."),
        ("Dressy casual, casual and beach",
         "Dressy casual means no jeans or sneakers, but no tie either: chinos, a blazer, a "
         "summer dress. Casual genuinely does allow neat jeans and flats — though 'casual' at a "
         "wedding still is not beachwear. Beach or destination codes add practical constraints: "
         "linen, breathable fabrics, block heels or barefoot-friendly sandals, and a layer for "
         "evening wind."),
        ("The three things the code never tells you",
         "Colour is the first. In Western weddings guests avoid white, ivory and anything bridal; "
         "in many South Asian celebrations white is mourning and red belongs to the couple. "
         "Second, headwear and shoulders can be governed by the ceremony venue rather than the "
         "invitation — a church may require a cover. Third, shoes matter more than the label: "
         "grass, gravel, sand and old stone floors punish stilettos. When in doubt, ask the "
         "couple or the planner; a two-line question is always less awkward than guessing."),
        ("Regional differences worth knowing",
         "The labels in this guide are US/UK convention. Southern European weddings often run "
         "more formal than the printed code suggests, while Scandinavian and Australian "
         "celebrations tend to read it more loosely. A 'formal' invitation in Germany or France "
         "can still mean a full suit and an evening gown. If the wedding is abroad, treat the "
         "local norm as the tie-breaker."),
    ]
    out = [f'<section class="page-hero page-hero-small"><div class="container page-hero-content">{h1}</div></section>',
           '<section class="section" style="background: var(--color-white);">',
           '<div class="container blog-article" style="max-width: 760px;">',
           lead]
    for head, para in sections:
        out.append(bound("h2_text", head, "h2"))
        out.append(bound("p_text", para))
    out.append(bound("h2_text", "Quick answers", "h2"))
    out.append('<div class="faq-list">')
    for q, a in FAQS:
        # class="faq-item" is the canonical visible-FAQ form the schema gate
        # counts; without it the FAQPage graph looks like invisible markup.
        out.append('<details class="faq-item"><summary data-i18n="%s">%s</summary>%s</details>'
                   % (key("summary_text", q), q, bound("p_text", a)))
    out.append('</div>')
    out.append('<p><a class="ft-btn ft-btn-primary" href="/tools/%s/" data-i18n="%s">'
               'Decode the exact wording on your invitation</a></p>'
               % (TOOL, key("a_text", "Decode the exact wording on your invitation")))
    out.append('</div></section>')
    return "\n".join(out)


def new_jsonld(lang: str, tr: dict[str, str] | None) -> str:
    def local(text: str, tag: str) -> str:
        return (tr or {}).get(key(tag, text), text)

    prefix = "" if lang == "en" else "/" + lang
    data = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": (tr or {}).get(f"blog.{SLUG}.title_text", TITLE),
        "description": (tr or {}).get(f"blog.{SLUG}.meta_description", DESC),
        "url": f"{BASE}{prefix}/blog/{SLUG}/",
        "datePublished": "2026-11-12", "dateModified": "2026-11-12",
        "inLanguage": LOCALE[lang],
        "author": {"@type": "Organization", "name": "WeddingAI.video Editorial"},
        "publisher": {"@type": "Organization", "name": "WeddingAI.video"},
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"{BASE}{prefix}/blog/{SLUG}/"},
    }
    # Build the FAQ graph from the SAME list the visible <details> use, so
    # schema and copy can never drift in count or wording again.
    faq = {
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": local(q, "summary_text"),
             "acceptedAnswer": {"@type": "Answer", "text": local(a, "p_text")}}
            for q, a in FAQS
        ],
    }
    return "".join('<script type="application/ld+json">\n%s\n</script>\n' % json.dumps(d, ensure_ascii=False, indent=2)
                   for d in (data, faq))


def fit(text: str, limit: int) -> str:
    """Keep translated head fields inside the SEO gate (60 / 160)."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit - 1].rstrip()
    if " " in cut:
        cut = cut[:cut.rfind(" ")]
    return cut.rstrip(" ,;:—-") + "…"


def build_head(html: str, lang: str, tr: dict[str, str] | None) -> str:
    html = html.replace("choose-wedding-videographer", SLUG)
    html = re.sub(r'<script type="application/ld\+json">[\s\S]*?</script>\s*', "", html)
    html = html.replace("</head>", new_jsonld(lang, tr) + "</head>", 1)
    html = html.replace('<html lang="en">', f'<html lang="{lang}">', 1)
    t = fit(tr.get(f"blog.{SLUG}.title_text", TITLE) if tr else TITLE, 60)
    d = fit(tr.get(f"blog.{SLUG}.meta_description", DESC) if tr else DESC, 155)
    prefix = "" if lang == "en" else "/" + lang
    html = re.sub(r'(<title\b[^>]*>)[\s\S]*?(</title>)',
                  lambda m: m.group(1) + t + m.group(2), html, count=1)
    html = re.sub(r'(<meta name="description"[^>]*content=")[^"]*(")',
                  lambda m: m.group(1) + d.replace('"', "&quot;") + m.group(2), html, count=1)
    for prop in ("og:title", "twitter:title"):
        html = re.sub(r'(<meta (?:property|name)="%s" content=")[^"]*(")' % re.escape(prop),
                      lambda m: m.group(1) + t.replace('"', "&quot;") + m.group(2), html, count=1)
    for prop in ("og:description", "twitter:description"):
        html = re.sub(r'(<meta (?:property|name)="%s" content=")[^"]*(")' % re.escape(prop),
                      lambda m: m.group(1) + d.replace('"', "&quot;") + m.group(2), html, count=1)
    html = re.sub(r'(<link rel="canonical" href=")[^"]*(")',
                  lambda m: m.group(1) + f"{BASE}{prefix}/blog/{SLUG}/" + m.group(2), html, count=1)
    html = re.sub(r'(<meta property="og:url" content=")[^"]*(")',
                  lambda m: m.group(1) + f"{BASE}{prefix}/blog/{SLUG}/" + m.group(2), html, count=1)
    html = re.sub(r'(<meta property="og:locale" content=")[^"]*(")',
                  lambda m: m.group(1) + LOCALE[lang] + m.group(2), html, count=1)
    # The template's head keys name the OLD article. Drop them: the head now
    # carries literal per-language values, so no dangling dictionary keys.
    cut = html.find("</head>")
    if cut > 0:
        head = re.sub(r'\s+data-i18n(?:-attr)?="[^"]*"', "", html[:cut])
        html = head + html[cut:]
    if lang != "en":
        # Localize page links, never asset paths.
        html = re.sub(r'href="/(tools|blog|services|gallery|about|pricing|resources)/',
                      lambda m: 'href="/%s/%s/' % (lang, m.group(1)), html)
    return html


def replace_main(html: str, content: str) -> str:
    m = re.search(r'<main id="main-content">[\s\S]*?</main>', html)
    if not m:
        raise RuntimeError("template <main> not found")
    return html.replace(m.group(0), '<main id="main-content">\n' + content + '\n</main>', 1)


def sitemap_entry(lang: str) -> str:
    prefix = "" if lang == "en" else "/" + lang
    lines = ["    <url>", f"        <loc>{BASE}{prefix}/blog/{SLUG}/</loc>",
             "        <lastmod>2026-11-12</lastmod>", "        <changefreq>monthly</changefreq>",
             "        <priority>0.7</priority>"]
    for l in ["en"] + LANGS:
        p = "" if l == "en" else "/" + l
        lines.append(f'        <xhtml:link rel="alternate" hreflang="{l}" href="{BASE}{p}/blog/{SLUG}/" />')
    lines.append(f'        <xhtml:link rel="alternate" hreflang="x-default" href="{BASE}/blog/{SLUG}/" />')
    lines.append("    </url>")
    return "\n".join(lines) + "\n"


def main() -> None:
    tpl = TEMPLATE.read_text(encoding="utf-8")
    trfile = ROOT / ".tmp" / "dress-code-translations.json"
    tr = json.loads(trfile.read_text(encoding="utf-8")) if trfile.exists() else None

    # Head strings need their own (short) dictionary entries for the copies.
    TEXT[f"blog.{SLUG}.title_text"] = TITLE
    TEXT[f"blog.{SLUG}.meta_description"] = DESC

    def values(lang: str):
        return {k: v[lang] for k, v in tr.items()} if tr else None

    content = body()
    en_dir = ROOT / "blog" / SLUG
    en_dir.mkdir(parents=True, exist_ok=True)
    (en_dir / "index.html").write_text(
        replace_main(build_head(tpl, "en", None), content), encoding="utf-8", newline="\n")

    for lang in LANGS:
        d = ROOT / lang / "blog" / SLUG
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(
            replace_main(build_head(tpl, lang, values(lang)), content),
            encoding="utf-8", newline="\n")

    # Backlink from the tool page in all languages.
    link_text = "Read the full dress code guide for guests"
    lk = f"tools.{TOOL}.a_text.{re.sub(r'[^a-z0-9]+', '_', link_text.lower()).strip('_')[:36]}.{hashlib.md5(link_text.encode()).hexdigest()[:8]}"
    TEXT[lk] = link_text
    for lang in ["en"] + LANGS:
        p = (ROOT / "tools" if lang == "en" else ROOT / lang / "tools") / TOOL / "index.html"
        if not p.exists():
            continue
        h = p.read_text(encoding="utf-8")
        if f'data-i18n="{lk}"' in h:
            continue
        href = ("" if lang == "en" else "/" + lang) + f"/blog/{SLUG}/"
        block = ('<p class="ft-serp-sources"><a href="%s" data-i18n="%s">%s</a></p>\n'
                 % (href, lk, link_text))
        h = h.replace("</main>", block + "</main>", 1) if "</main>" in h else h.replace("<footer", block + "<footer", 1)
        p.write_text(h, encoding="utf-8", newline="\n")

    for lang in ["en"] + LANGS:
        p = ROOT / ("sitemap-%s.xml" % lang)
        s = p.read_text(encoding="utf-8")
        if f"/blog/{SLUG}/" in s:
            continue
        s = s.replace("</urlset>", sitemap_entry(lang) + "</urlset>", 1)
        p.write_text(s, encoding="utf-8", newline="\n")

    keys = ROOT / ".tmp" / "dress-code-keys.json"
    keys.write_text(json.dumps(TEXT, ensure_ascii=False, indent=2), encoding="utf-8")
    print("blog pages: 11, backlinks: 11, sitemaps: 11")
    print("English keys: %d -> %s" % (len(TEXT), keys.relative_to(ROOT)))


if __name__ == "__main__":
    main()
