# -*- coding: utf-8 -*-
"""Build /guides/: one editorial guide per free tool, in all 11 languages.

URL policy: purely additive. Every guide URL is new; no tool URL, canonical or
hreflang cluster is touched. The guides link TO the tools, not the other way
round, which is the same traffic-safe pattern used for /planning-tools/.

Run order:
  python .tmp/translate-guides.py           # 10 langs -> .tmp/guide-translations.json
  python scripts/add-tool-guides.py
  python .tmp/rebuild-shards-inplace.py
  python scripts/verify-i18n-shards.py
"""
import html
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("gd", ROOT / "scripts" / "tool_guides_data.py")
gd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gd)

LANGS = ["zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
ALL = ["en"] + LANGS
LOCALE = {"en": "en_US", "zh": "zh_CN", "es": "es_ES", "fr": "fr_FR",
          "de": "de_DE", "pt": "pt_BR", "ja": "ja_JP", "ru": "ru_RU",
          "ar": "ar_AE", "th": "th_TH", "hi": "hi_IN"}
BASE = "https://weddingai.video"
SLUG = "guides"
NS = "guides"
TEMPLATE = ROOT / "blog" / "wedding-dress-code-guide" / "index.html"
HUB = ROOT / "tools" / "index.html"
PLANNING = ROOT / "planning-tools" / "index.html"
MIDDLEWARE = ROOT / "functions" / "_middleware.js"
TRANS = ROOT / ".tmp" / "guide-translations.json"
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

GROUPS = [
    ("numbers", "group_numbers"),
    ("words", "group_words"),
    ("edit", "group_edit"),
    ("invites", "group_invites"),
    ("docs", "group_docs"),
]
GROUP_ORDER = {g: i for i, (g, _) in enumerate(GROUPS)}
SLUGS = sorted(gd.G, key=lambda s: (GROUP_ORDER[gd.G[s]["group"]], s))


# --------------------------------------------------------------------------
# Text table: en is the authored source, the other 10 come from the reviewed
# translation pass. Missing translations fail loudly rather than leaking EN.
# --------------------------------------------------------------------------
def source_texts():
    src = {}
    for key, val in gd.COMMON.items():
        src[NS + ".common." + key] = val
    for slug, g in gd.G.items():
        p = NS + "." + slug + "."
        src[p + "title"] = g["title"]
        src[p + "desc"] = g["desc"]
        src[p + "h1"] = g["h1"]
        src[p + "lead"] = g["lead"]
        for i, (label, value) in enumerate(g["facts"], 1):
            src[p + "f%dl" % i] = label
            src[p + "f%dv" % i] = value
        for i in (1, 2, 3):
            src[p + "s%d" % i] = g["s%d" % i]
        for i, (q, a) in enumerate(g["faq"], 1):
            src[p + "q%d" % i] = q
            src[p + "a%d" % i] = a
    return src


def load_texts():
    src = source_texts()
    raw = json.loads(TRANS.read_text(encoding="utf-8"))
    overrides = ROOT / ".tmp" / "guide-translations-overrides.json"
    if overrides.exists():
        # Reviewed / length-corrected replacements win over the raw batch output.
        raw.update(json.loads(overrides.read_text(encoding="utf-8")))
    table = {"en": dict(src)}
    missing = []
    for lang in LANGS:
        table[lang] = {}
        for key, en in src.items():
            val = raw.get("%s|%s" % (lang, key))
            if not val or not val.strip():
                missing.append((lang, key))
                val = en
            table[lang][key] = val.strip()
    if missing:
        raise SystemExit("[FAIL] %d translations missing (first 12): %s" %
                         (len(missing), missing[:12]))
    return table


TEXT = {}


def t(lang, key):
    return TEXT[lang][key]


def key(slug, field):
    return NS + "." + slug + "." + field


def common(field):
    return NS + ".common." + field


def esc(s):
    return html.escape(s, quote=True)


def fit(text, limit, label):
    if len(text) > limit:
        raise SystemExit("[FAIL] %s is %d chars (limit %d): %s" %
                         (label, len(text), limit, text))
    return text


def url(lang, path):
    return BASE + ("" if lang == "en" else "/" + lang) + path


def prefix(lang):
    return "" if lang == "en" else "/" + lang


def bind(lang, i18n_key, tag, text, cls=""):
    c = ' class="%s"' % cls if cls else ""
    return "<%s%s data-i18n=\"%s\">%s</%s>" % (tag, c, i18n_key, esc(text), tag)


CSS = """
.gd-wrap{max-width:860px;margin:0 auto;padding:0 var(--spacing-md) var(--spacing-xl)}
.gd-crumb{font-size:.82rem;color:var(--color-text-light);margin:var(--spacing-md) 0}
.gd-crumb a{color:var(--color-primary);text-decoration:none}
.gd-hero h1{font-size:clamp(1.8rem,4vw,2.6rem);line-height:1.2;color:var(--color-text);margin:0 0 .8rem}
.gd-lead{font-size:1.06rem;line-height:1.8;color:var(--color-text-light)}
.gd-meta{font-size:.8rem;color:var(--color-text-light);margin:.8rem 0 1.4rem}
.gd-cta{display:inline-block;background:var(--color-primary);color:#fff;padding:.7rem 1.25rem;border-radius:var(--radius-md);font-weight:700;text-decoration:none;font-size:.92rem}
.gd-cta:hover{opacity:.9}
.gd-section{margin-top:2.1rem}
.gd-section>h2{font-size:1.42rem;color:var(--color-text);margin:0 0 .85rem;line-height:1.35}
.gd-section p{line-height:1.85;color:var(--color-text-light);margin:0 0 .8rem}
.gd-table{width:100%;border-collapse:collapse;font-size:.92rem}
.gd-table th,.gd-table td{text-align:left;padding:.7rem .75rem;border-bottom:1px solid var(--color-border);vertical-align:top;line-height:1.6}
.gd-table th{width:34%;color:var(--color-text);font-weight:650;background:var(--color-surface-warm-2)}
.gd-table td{color:var(--color-text-light)}
.gd-faq details{background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-md);padding:.85rem 1rem;margin-bottom:.6rem}
.gd-faq summary{font-weight:650;color:var(--color-text);cursor:pointer}
.gd-faq p{color:var(--color-text-light);line-height:1.75;margin:.6rem 0 0}
.gd-related{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:.8rem}
.gd-related a{display:block;padding:.9rem 1rem;background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-md);text-decoration:none;color:var(--color-primary);font-weight:600;font-size:.9rem}
.gd-related a:hover{border-color:var(--color-primary)}
.gd-foot{margin-top:2.4rem;padding:1.3rem;background:var(--color-surface-warm-2);border:1px solid var(--color-border);border-radius:var(--radius-md);text-align:center;line-height:2}
.gd-foot a{color:var(--color-primary);font-weight:650;text-decoration:none;margin:0 .5rem}
.gd-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:.85rem;margin:.9rem 0 0}
.gd-card{display:flex;flex-direction:column;gap:.35rem;padding:1rem;background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-md);text-decoration:none;color:inherit}
.gd-card:hover{border-color:var(--color-primary)}
.gd-card h3{margin:0;font-size:1rem;line-height:1.4;color:var(--color-text)}
.gd-card p{margin:0;font-size:.83rem;line-height:1.6;color:var(--color-text-light)}
.gd-group{margin-top:2rem}
.gd-group>h2{font-size:1.35rem;color:var(--color-text);margin:0 0 .3rem}
@media(max-width:600px){.gd-table th{width:42%}.gd-wrap{padding:0 var(--spacing-sm) var(--spacing-lg)}}
"""


def hreflang_links(path):
    lines = ['<link rel="alternate" hreflang="%s" href="%s">' % (l, url(l, path))
             for l in ALL]
    lines.append('<link rel="alternate" hreflang="x-default" href="%s">' % url("en", path))
    return "\n".join(lines)


def head(lang, slug):
    path = "/%s/" % SLUG if slug is None else "/%s/%s/" % (SLUG, slug)
    canonical = url(lang, path)
    title_key = common("index_title") if slug is None else key(slug, "title")
    desc_key = common("index_desc") if slug is None else key(slug, "desc")
    title = fit(t(lang, title_key), 60, lang + ":" + title_key)
    desc = fit(t(lang, desc_key), 155, lang + ":" + desc_key)
    return """<!DOCTYPE html>
<html lang="%(lang)s">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>%(title)s</title>
<link rel="canonical" href="%(canonical)s">
%(alt)s
<meta name="description" content="%(desc)s" />
<meta property="og:type" content="%(ogtype)s">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(canonical)s">
<meta property="og:site_name" content="WeddingAI.video">
<meta property="og:locale" content="%(locale)s">
<meta property="og:image" content="https://weddingai.video/images/og-image-1200x630.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%(title)s">
<meta name="twitter:description" content="%(desc)s">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<meta name="theme-color" content="#D4AF37">
<link rel="manifest" href="/manifest.json">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="stylesheet" href="/styles.min.css?v=3.42">
<link rel="stylesheet" href="/styles/i18n.css">
<script defer src="/js/main.min.js?v=3.22"></script>
<script src="/js/langs.js" defer></script>
<script src="/js/i18n.js?v=4.29" defer></script>
<style>%(css)s</style>
%(jsonld)s
</head>
""" % {"lang": lang, "title": esc(title), "desc": esc(desc),
       "canonical": canonical, "alt": hreflang_links(path),
       "locale": LOCALE[lang], "css": CSS,
       "ogtype": "website" if slug is None else "article",
       "jsonld": jsonld(lang, slug)}


def ld(obj):
    return '<script type="application/ld+json">\n%s\n</script>\n' % json.dumps(
        obj, ensure_ascii=False, indent=2)


def breadcrumbs(lang, slug):
    p = prefix(lang)
    items = [
        {"@type": "ListItem", "position": 1,
         "name": "WeddingAI.video", "item": BASE + p + "/"},
        {"@type": "ListItem", "position": 2,
         "name": t(lang, common("all_tools")), "item": BASE + p + "/tools/"},
        {"@type": "ListItem", "position": 3,
         "name": t(lang, common("breadcrumb_guides")),
         "item": url(lang, "/guides/")},
    ]
    if slug is not None:
        items.append({"@type": "ListItem", "position": 4,
                      "name": t(lang, key(slug, "h1")),
                      "item": url(lang, "/guides/%s/" % slug)})
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": items}


def jsonld(lang, slug):
    out = []
    if slug is None:
        items = []
        for pos, s in enumerate(SLUGS, 1):
            items.append({
                "@type": "ListItem", "position": pos,
                "item": {"@type": "Article",
                         "name": t(lang, key(s, "h1")),
                         "url": url(lang, "/guides/%s/" % s)},
            })
        out.append({
            "@context": "https://schema.org", "@type": "CollectionPage",
            "name": t(lang, common("index_h1")),
            "description": t(lang, common("index_desc")),
            "url": url(lang, "/guides/"),
            "inLanguage": LOCALE[lang],
            "isPartOf": {"@type": "WebSite", "name": "WeddingAI.video",
                         "url": BASE + "/"},
            "mainEntity": {"@type": "ItemList", "numberOfItems": len(items),
                           "itemListElement": items},
        })
    else:
        g = gd.G[slug]
        words = len((g["lead"] + " " + g["s1"] + " " + g["s2"] + " " + g["s3"] + " " +
                     " ".join(v for _, v in g["facts"]) + " " +
                     " ".join(q + " " + a for q, a in g["faq"])).split())
        out.append({
            "@context": "https://schema.org", "@type": "Article",
            "headline": t(lang, key(slug, "h1")),
            "description": t(lang, key(slug, "desc")),
            "url": url(lang, "/guides/%s/" % slug),
            "inLanguage": LOCALE[lang],
            "datePublished": TODAY, "dateModified": TODAY,
            "wordCount": words,
            "author": {"@type": "Organization", "name": "WeddingAI.video",
                       "url": BASE + "/"},
            "publisher": {"@type": "Organization", "name": "WeddingAI.video",
                          "logo": {"@type": "ImageObject",
                                   "url": BASE + "/images/logo-full.jpeg"}},
            "mainEntityOfPage": {"@type": "WebPage",
                                 "@id": url(lang, "/guides/%s/" % slug)},
            "about": {"@type": "SoftwareApplication",
                      "name": t(lang, key(slug, "h1")),
                      "url": url(lang, "/tools/%s/" % slug),
                      "applicationCategory": "BusinessApplication",
                      "operatingSystem": "Web Browser",
                      "offers": {"@type": "Offer", "price": "0",
                                 "priceCurrency": "USD"}},
        })
        out.append({
            "@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": t(lang, key(slug, "q%d" % i)),
                 "acceptedAnswer": {"@type": "Answer",
                                    "text": t(lang, key(slug, "a%d" % i))}}
                for i in (1, 2, 3)
            ],
        })
    out.append(breadcrumbs(lang, slug))
    return "".join(ld(o) for o in out)


def localize_chrome(text, lang):
    if lang == "en":
        return text
    return re.sub(
        r'href="/(tools|blog|services|gallery|about|pricing|resources|planning-tools|guides)/',
        lambda m: 'href="/%s/%s/' % (lang, m.group(1)), text)


def body(lang, slug):
    p = prefix(lang)
    o = ['<main id="main-content">', '<div class="gd-wrap">']
    o.append('<nav class="gd-crumb"><a href="%s/">WeddingAI.video</a> / '
             '<a href="%s/tools/">%s</a> / <a href="%s/guides/">%s</a>%s</nav>' % (
                 p, p, esc(t(lang, common("all_tools"))), p,
                 esc(t(lang, common("breadcrumb_guides"))),
                 "" if slug is None else " / " + esc(t(lang, key(slug, "h1")))))

    if slug is None:
        o.append('<section class="gd-hero">')
        o.append("  " + bind(lang, common("index_h1"), "h1",
                             t(lang, common("index_h1"))))
        o.append("  " + bind(lang, common("index_lead"), "p",
                             t(lang, common("index_lead")), "gd-lead"))
        o.append('</section>')
        for group, label_key in GROUPS:
            group_slugs = [s for s in SLUGS if gd.G[s]["group"] == group]
            if not group_slugs:
                continue
            o.append('<section class="gd-group">')
            o.append("  " + bind(lang, common(label_key), "h2",
                                 t(lang, common(label_key))))
            o.append('  <div class="gd-grid">')
            for s in group_slugs:
                o.append('    <a class="gd-card" href="%s/guides/%s/">' % (p, s))
                o.append("      " + bind(lang, key(s, "h1"), "h3", t(lang, key(s, "h1"))))
                o.append("      " + bind(lang, key(s, "desc"), "p",
                                         t(lang, key(s, "desc"))))
                o.append('    </a>')
            o.append('  </div>')
            o.append('</section>')
    else:
        g = gd.G[slug]
        o.append('<article>')
        o.append('<section class="gd-hero">')
        o.append("  " + bind(lang, key(slug, "h1"), "h1", t(lang, key(slug, "h1"))))
        o.append("  " + bind(lang, key(slug, "lead"), "p",
                             t(lang, key(slug, "lead")), "gd-lead"))
        o.append('  <p class="gd-meta"><span data-i18n="%s">%s</span> · '
                 '<time datetime="%s">%s</time></p>' %
                 (common("reviewed"), esc(t(lang, common("reviewed"))), TODAY, TODAY))
        o.append('  <p><a class="gd-cta" href="%s/tools/%s/" data-i18n="%s">%s →</a></p>' %
                 (p, slug, common("cta"), esc(t(lang, common("cta")))))
        o.append('</section>')

        o.append('<section class="gd-section">')
        o.append("  " + bind(lang, common("quick_h2"), "h2", t(lang, common("quick_h2"))))
        o.append('  <table class="gd-table"><tbody>')
        for i in (1, 2, 3, 4):
            o.append('    <tr><th data-i18n="%s">%s</th><td data-i18n="%s">%s</td></tr>' %
                     (key(slug, "f%dl" % i), esc(t(lang, key(slug, "f%dl" % i))),
                      key(slug, "f%dv" % i), esc(t(lang, key(slug, "f%dv" % i)))))
        o.append('  </tbody></table>')
        o.append('</section>')

        for i, field in enumerate(("s1", "s2", "s3"), 1):
            h2key = ("how_h2", "regional_h2", "mistakes_h2")[i - 1]
            o.append('<section class="gd-section">')
            o.append("  " + bind(lang, common(h2key), "h2", t(lang, common(h2key))))
            o.append("  " + bind(lang, key(slug, field), "p", t(lang, key(slug, field))))
            o.append('</section>')

        o.append('<section class="gd-section gd-faq">')
        o.append("  " + bind(lang, common("faq_h2"), "h2", t(lang, common("faq_h2"))))
        for i in (1, 2, 3):
            o.append('  <details class="faq-item">')
            o.append('    <summary data-i18n="%s">%s</summary>' %
                     (key(slug, "q%d" % i), esc(t(lang, key(slug, "q%d" % i)))))
            o.append('    <p data-i18n="%s">%s</p>' %
                     (key(slug, "a%d" % i), esc(t(lang, key(slug, "a%d" % i)))))
            o.append('  </details>')
        o.append('</section>')

        o.append('<section class="gd-section">')
        o.append("  " + bind(lang, common("related_h2"), "h2",
                             t(lang, common("related_h2"))))
        o.append('  <div class="gd-related">')
        for r in g["rel"]:
            o.append('    <a href="%s/guides/%s/" data-i18n="%s">%s →</a>' %
                     (p, r, key(r, "h1"), esc(t(lang, key(r, "h1")))))
        o.append('  </div>')
        o.append('</section>')
        o.append('</article>')

    o.append('<div class="gd-foot">')
    o.append('  <a href="%s/tools/" data-i18n="%s">%s</a> · '
             '<a href="%s/planning-tools/" data-i18n="%s">%s</a> · '
             '<a href="%s/guides/" data-i18n="%s">%s</a>' %
             (p, common("all_tools"), esc(t(lang, common("all_tools"))),
              p, common("planning_hub"), esc(t(lang, common("planning_hub"))),
              p, common("all_guides"), esc(t(lang, common("all_guides")))))
    o.append('  <p data-i18n="%s" style="font-size:.8rem;color:var(--color-text-light);margin:.5rem 0 0">%s</p>' %
             (common("footer_note"), esc(t(lang, common("footer_note")))))
    o.append('</div>')
    o.extend(['</div>', '</main>'])
    return "\n".join(o)


def build_pages():
    tpl = TEMPLATE.read_text(encoding="utf-8")
    pre, rest = tpl.split('<main id="main-content">', 1)
    _, post = rest.split('</main>', 1)
    chrome_top = pre[pre.index("<body"):]
    chrome_bottom = post[:post.index("</body>")]
    n = 0
    for lang in ALL:
        for slug in [None] + SLUGS:
            path = ("/%s/" % SLUG) if slug is None else ("/%s/%s/" % (SLUG, slug))
            page = (head(lang, slug) + localize_chrome(chrome_top, lang)
                    + body(lang, slug) + localize_chrome(chrome_bottom, lang)
                    + "</body>\n</html>\n")
            d = (ROOT if lang == "en" else ROOT / lang) / SLUG
            if slug is not None:
                d = d / slug
            d.mkdir(parents=True, exist_ok=True)
            (d / "index.html").write_text(page, encoding="utf-8", newline="\n")
            n += 1
    print("pages written: %d (%d guides + index, x %d langs)" %
          (n, len(SLUGS) + 1, len(ALL)))


def sitemap_entry(lang, slug):
    path = "/%s/" % SLUG if slug is None else "/%s/%s/" % (SLUG, slug)
    lines = ["    <url>", "        <loc>%s</loc>" % url(lang, path),
             "        <lastmod>%s</lastmod>" % TODAY,
             "        <changefreq>monthly</changefreq>",
             "        <priority>%s</priority>" % ("0.7" if slug is None else "0.6")]
    for l in ALL:
        lines.append('        <xhtml:link rel="alternate" hreflang="%s" href="%s" />' %
                     (l, url(l, path)))
    lines.append('        <xhtml:link rel="alternate" hreflang="x-default" href="%s" />' %
                 url("en", path))
    lines.append("    </url>")
    return "\n".join(lines) + "\n"


def update_sitemaps():
    """Idempotently restore any missing guide <url> by <loc>.

    A previous run may have quarantined a whole language (33 URLs) or just a
    few pages. Recomputing by <loc> makes a re-run converge to the full set,
    after which mark-incomplete-guide-langs.py re-applies the quarantine.
    """
    total = 0
    for lang in ALL:
        p = ROOT / ("sitemap-%s.xml" % lang)
        s = p.read_text(encoding="utf-8")
        have = set(re.findall(r"<loc>([^<]*)</loc>", s))
        missing = []
        for slug in [None] + SLUGS:
            entry = sitemap_entry(lang, slug)
            m = re.search(r"<loc>([^<]*)</loc>", entry)
            if m and m.group(1) not in have:
                missing.append(entry)
        if not missing:
            continue
        p.write_text(s.replace("</urlset>", "".join(missing) + "</urlset>", 1),
                     encoding="utf-8", newline="\n")
        total += len(missing)
    print("sitemaps: restored %d missing guide URLs across 11 files" % total)


def update_dictionaries():
    """Append missing keys AND refresh values that changed.

    On the first launch several languages fell back to English placeholders
    while the translation quota was exhausted. Re-running the generator with
    the completed translations must overwrite those placeholders in place,
    otherwise the runtime dictionary keeps serving English on localised pages.
    Line-by-line edits preserve the existing formatting (a full json.dump
    collapses the file to one line and produces a huge unreadable diff).
    """
    src = source_texts()
    totals = {"new": 0, "changed": 0}
    for lang in ALL:
        p = ROOT / "i18n" / ("%s.json" % lang)
        raw = p.read_text(encoding="utf-8")
        data = json.loads(raw)
        new = {k: TEXT[lang][k] for k in src if k not in data}
        changed = {k: TEXT[lang][k] for k in src
                   if k in data and data[k] != TEXT[lang][k]}
        if not new and not changed:
            continue
        eol = "\r\n" if "\r\n" in raw else "\n"
        lines = raw.splitlines(keepends=True)

        for k, v in changed.items():
            prefix = "  " + json.dumps(k, ensure_ascii=False) + ": "
            for i, line in enumerate(lines):
                if line.startswith(prefix):
                    trailing = "," if line.rstrip("\r\n").endswith(",") else ""
                    lines[i] = (prefix + json.dumps(v, ensure_ascii=False) +
                                trailing + eol)
                    break
            else:
                raise SystemExit("[FAIL] %s: cannot locate line for %s" % (p, k))

        if new:
            close = next(i for i in range(len(lines) - 1, -1, -1)
                         if lines[i].strip() == "}")
            prev = close - 1
            while prev >= 0 and not lines[prev].strip():
                prev -= 1
            if not lines[prev].rstrip().endswith(","):
                lines[prev] = lines[prev].rstrip("\r\n") + "," + eol
            block = "".join('  %s: %s%s' % (
                json.dumps(k2, ensure_ascii=False),
                json.dumps(v, ensure_ascii=False),
                ",\n" if i < len(new) - 1 else "\n")
                for i, (k2, v) in enumerate(new.items()))
            lines.insert(close, block)

        out = "".join(lines)
        check = json.loads(out)
        for k2, v in list(new.items()) + list(changed.items()):
            if check.get(k2) != v:
                raise SystemExit("[FAIL] %s: %s did not round-trip" % (p, k2))
        p.write_text(out, encoding="utf-8", newline="")
        totals["new"] += len(new)
        totals["changed"] += len(changed)
    print("dictionaries: %d new keys, %d refreshed values (11 langs)" %
          (totals["new"], totals["changed"]))


# --------------------------------------------------------------------------
# Internal links: every tool points at its guide, both hubs point at the
# guide index, and the planning hub links each of its 14 planning guides.
# --------------------------------------------------------------------------
def inject_block(path, marker, block, guard):
    if not path.exists():
        return 0
    s = path.read_text(encoding="utf-8")
    if guard in s:
        return 0
    if marker not in s:
        return 0
    path.write_text(s.replace(marker, block + marker, 1), encoding="utf-8",
                    newline="")
    return 1


def inject_tool_links():
    n = 0
    for lang in ALL:
        p = prefix(lang)
        for slug in SLUGS:
            f = (ROOT / "tools" if lang == "en" else ROOT / lang / "tools") / slug / "index.html"
            block = ('<p class="ft-serp-sources"><a href="%s/guides/%s/" '
                     'data-i18n="%s">%s →</a></p>\n' %
                     (p, slug, common("guide_link"),
                      esc(t(lang, common("guide_link")))))
            n += inject_block(f, "</main>", block, 'data-i18n="%s"' % common("guide_link"))
    print("tool-page guide links: %d" % n)


def inject_hub_links():
    n = 0
    block = ('\n <div style="max-width:1140px;margin:0 auto var(--spacing-xl);'
             'text-align:center;padding:1.2rem">'
             '\n  <p style="margin:0"><a href="/guides/" data-i18n="%s" '
             'style="color:var(--color-primary);font-weight:700;text-decoration:none">%s →</a></p>'
             '\n </div>\n' % (common("all_guides"),
                              esc(t("en", common("all_guides")))))
    n += inject_block(HUB, "</main>", block, 'data-i18n="%s"' % common("all_guides"))
    for lang in LANGS:
        f = ROOT / lang / "planning-tools" / "index.html"
        b = ('\n <div class="pt-footer-cta" style="max-width:1140px;margin:0 auto var(--spacing-xl)">'
             '\n  <p><a href="/%s/guides/" data-i18n="%s">%s →</a></p>'
             '\n </div>\n' % (lang, common("all_guides"),
                              esc(t(lang, common("all_guides")))))
        n += inject_block(f, "</main>", b, 'data-i18n="%s"' % common("all_guides"))
    b_en = ('\n <div class="pt-footer-cta" style="max-width:1140px;margin:0 auto var(--spacing-xl)">'
            '\n  <p><a href="/guides/" data-i18n="%s">%s →</a></p>'
            '\n </div>\n' % (common("all_guides"), esc(t("en", common("all_guides")))))
    n += inject_block(PLANNING, "</main>", b_en,
                      'data-i18n="%s"' % common("all_guides"))
    print("hub guide links: %d" % n)


def inject_planning_guide_links():
    """A separate guide-index block on the planning hub.

    Never inject an <a> inside the existing card <a>: nested anchors are
    invalid HTML and the gate's tag-balance check would catch it.
    """
    planning_slugs = [
        "wedding-checklist-generator", "wedding-guest-count-calculator",
        "wedding-countdown-widget", "wedding-vendor-questions-checklist",
        "wedding-alcohol-calculator", "wedding-cake-serving-calculator",
        "wedding-gift-calculator", "wedding-vendor-tipping-calculator",
        "wedding-vow-writer", "wedding-speech-writer",
        "wedding-day-timeline-generator", "wedding-dress-code-decoder",
        "wedding-thank-you-note-generator", "name-change-checklist",
    ]
    n = 0
    for lang in ALL:
        p = prefix(lang)
        f = (ROOT if lang == "en" else ROOT / lang) / "planning-tools" / "index.html"
        if not f.exists():
            continue
        b = ['\n <section data-guide-index style="max-width:1140px;margin:var(--spacing-xl) auto 0;padding:0 var(--spacing-md)">']
        b.append('  <h2 data-i18n="%s" style="font-size:1.5rem;color:var(--color-text);margin:0 0 .9rem">%s</h2>' %
                 (common("all_guides"), esc(t(lang, common("all_guides")))))
        b.append('  <div class="pt-grid">')
        for slug in planning_slugs:
            b.append('    <a class="pt-card" href="%s/guides/%s/">' % (p, slug))
            b.append('      <h3 class="pt-name" data-i18n="%s">%s</h3>' %
                     (key(slug, "h1"), esc(t(lang, key(slug, "h1")))))
            b.append('      <span class="pt-cta" data-i18n="%s">%s →</span>' %
                     (common("guide_link"), esc(t(lang, common("guide_link")))))
            b.append('    </a>')
        b.append('  </div>\n </section>\n')
        n += inject_block(f, "</main>", "\n".join(b), "data-guide-index")
    print("planning hub guide-index blocks: %d pages" % n)


def inject_blog_link():
    """Dress-code guide is the natural editorial bridge into the new hub."""
    n = 0
    for lang in ALL:
        p = prefix(lang)
        f = (ROOT / "blog" if lang == "en" else ROOT / lang / "blog") / \
            "wedding-dress-code-guide" / "index.html"
        block = ('<p class="blog-inline-cta"><a href="%s/planning-tools/" '
                 'data-i18n="%s">%s →</a></p>\n' %
                 (p, common("planning_hub"),
                  esc(t(lang, common("planning_hub")))))
        n += inject_block(f, "</main>", block,
                          'data-i18n="%s"' % common("planning_hub"))
    print("dress-code guide -> planning hub links: %d" % n)


def add_middleware_allowlist():
    s = MIDDLEWARE.read_text(encoding="utf-8")
    if '"guides"' in s:
        print("middleware allowlist: already present")
        return
    old = '"planning-tools",'
    if old not in s:
        raise SystemExit("[FAIL] middleware allowlist anchor not found")
    MIDDLEWARE.write_text(s.replace(old, old + '\n    "guides",', 1),
                          encoding="utf-8", newline="")
    print("middleware allowlist: added guides")


def main():
    global TEXT
    TEXT = load_texts()
    for lang in ALL:
        fit(t(lang, common("index_title")), 60, lang + ".index_title")
        fit(t(lang, common("index_desc")), 155, lang + ".index_desc")
        for slug in SLUGS:
            fit(t(lang, key(slug, "title")), 60, lang + "." + slug + ".title")
            fit(t(lang, key(slug, "desc")), 155, lang + "." + slug + ".desc")
    build_pages()
    update_sitemaps()
    update_dictionaries()
    inject_tool_links()
    inject_hub_links()
    inject_planning_guide_links()
    inject_blog_link()
    add_middleware_allowlist()
    print("done. Next: python .tmp/rebuild-shards-inplace.py")


if __name__ == "__main__":
    main()
