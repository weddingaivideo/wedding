#!/usr/bin/env python3
"""
Write the 10 static language copies of a tool page.

WHY STATIC COPIES AND NOT JUST THE MIDDLEWARE
----------------------------------------------
The middleware can serve /<lang>/tools/<slug>/ from the English source and
translate it at runtime. But then the HEAD stays English: the meta
description, the og:title and the twitter card are not bound to the
dictionary, so a Hindi search result shows an English snippet under a
Hindi title.

So each language gets its own file with a pre-translated head, exactly
like the 13 existing tools do. The BODY stays English and is translated at
runtime by the middleware's data-i18n pass - which is what the
data-i18n bindings in the English page are for.

LINK PREFIXING
--------------
Root-relative links are repointed at /<lang>/..., but only where a
localized twin actually exists. A link to a page that has no localized
twin must keep pointing at the English page: the middleware would render
it, but the promise "this link stays in your language" is not worth
breaking for a deep service page.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

OG_LOCALE = {
    "zh": "zh_CN", "es": "es_ES", "fr": "fr_FR", "de": "de_DE", "pt": "pt_BR",
    "ja": "ja_JP", "ru": "ru_RU", "ar": "ar_SA", "th": "th_TH", "hi": "hi_IN",
}

# Hubs that exist in every language (the middleware renders them).
HUB_SEGMENTS = {
    "tools", "blog", "about", "pricing", "order", "services",
    "resources", "gallery", "privacy", "terms",
}


def localize_href(href, lang, root):
    if not href.startswith("/"):
        return href
    if href.startswith("/cdn-cgi/"):
        return href
    if href.startswith("/%s/" % lang) or href == "/%s" % lang:
        return href
    if href == "/" or href.startswith("/#"):
        return "/%s/%s" % (lang, href[1:])
    path = href.split("#")[0].split("?")[0]
    segs = [s for s in path.strip("/").split("/") if s]
    if not segs:
        return href
    first = segs[0]
    if first == "services" and len(segs) > 1:
        # Deep service pages have no localized twin in the static copies.
        return href
    if first == "blog" and len(segs) > 1:
        twin = root / lang / path.strip("/") / "index.html"
        if not twin.exists():
            return href
        return "/%s%s" % (lang, href)
    if first in HUB_SEGMENTS:
        return "/%s%s" % (lang, href)
    return href


def replace_meta(html, attr_name, attr_value, new_value):
    """Replace the content="" of the meta tag with the given name/property."""
    pat = re.compile(
        r'(<meta\s+name="%s"\s+content=")([^"]*)(")' % re.escape(attr_name))
    if not pat.search(html):
        pat = re.compile(
            r'(<meta\s+property="%s"\s+content=")([^"]*)(")' % re.escape(attr_name))
    new_html, n = pat.subn(lambda m: m.group(1) + new_value + m.group(3), html, count=1)
    if n != 1:
        raise SystemExit("[FAIL] could not find <meta %s> to replace" % attr_name)
    return new_html


def localize_schema(html, lang, schema):
    """Rewrite the JSON-LD blocks with the translated strings.

    WHY
    ---
    The middleware localizes the FAQ schema only for the homepage and the
    pricing page (it knows the scopes homepage_faq and pricing_faq). A tool
    page's FAQPage block would therefore keep the ENGLISH questions and
    answers on every language page - and a search engine sees structured
    data that contradicts the copy on the page.

    The FAQ answers here are the same strings as the visible FAQ, so they
    were translated with the same result: the schema and the visible copy
    cannot drift apart.
    """
    if not schema:
        return html
    faq = schema.get("faq") or []
    howto = schema.get("howto") or {}
    app = schema.get("app") or {}

    def repl(match):
        body = match.group(1)
        try:
            obj = json.loads(body)
        except Exception:  # noqa: BLE001
            return match.group(0)
        kind = obj.get("@type")
        changed = False
        if kind == "FAQPage":
            for i, q in enumerate(obj.get("mainEntity", [])):
                if i >= len(faq):
                    break
                if q.get("name") != faq[i]["name"]:
                    q["name"] = faq[i]["name"]
                    changed = True
                ans = q.get("acceptedAnswer") or {}
                if ans.get("text") != faq[i]["text"]:
                    ans["text"] = faq[i]["text"]
                    changed = True
        elif kind == "HowTo":
            if howto.get("name") and obj.get("name") != howto["name"]:
                obj["name"] = howto["name"]
                changed = True
            steps = obj.get("step") or []
            for i, step in enumerate(steps):
                if i >= len(howto.get("steps") or []):
                    break
                src = howto["steps"][i]
                if step.get("name") != src["name"]:
                    step["name"] = src["name"]
                    changed = True
                if step.get("text") != src["text"]:
                    step["text"] = src["text"]
                    changed = True
        elif kind == "SoftwareApplication":
            if app.get("description") and obj.get("description") != app["description"]:
                obj["description"] = app["description"]
                changed = True
            fl = app.get("featureList") or []
            cur = obj.get("featureList") or []
            if len(cur) == len(fl):
                if cur != fl:
                    obj["featureList"] = fl
                    changed = True
        if not changed:
            return match.group(0)
        out = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        # A literal "</script>" inside the JSON would close the tag early.
        out = out.replace("<", "\\u003c").replace(">", "\\u003e")
        return '<script type="application/ld+json">%s</script>' % out

    return re.sub(r'<script\s+type="application/ld\+json"[^>]*>([\s\S]*?)</script>',
                  repl, html)


def build_copy(en_html, lang, head, root, schema):
    html = en_html

    # 1. The document language.
    html, n = re.subn(r'<html\s+lang="[^"]*">', '<html lang="%s">' % lang, html, count=1)
    if n != 1:
        raise SystemExit("[FAIL] no <html lang> in the English page")

    # 2. The head copy.
    url = "https://weddingai.video/%s/tools/%s/" % (lang, SLUG)
    html, n = re.subn(r"<title>.*?</title>",
                      lambda m: "<title>%s</title>" % head["title"], html, count=1, flags=re.S)
    if n != 1:
        raise SystemExit("[FAIL] no <title> in the English page")
    html = re.sub(r'<link rel="canonical" href="[^"]*">',
                  '<link rel="canonical" href="%s">' % url, html, count=1)
    html = replace_meta(html, "description", None, head["description"])
    html = replace_meta(html, "og:title", None, head["og_title"])
    html = replace_meta(html, "og:description", None, head["og_description"])
    html = replace_meta(html, "og:image:alt", None, head["og_image_alt"])
    html = replace_meta(html, "twitter:title", None, head["twitter_title"])
    html = replace_meta(html, "twitter:description", None, head["twitter_description"])
    html = replace_meta(html, "apple-mobile-web-app-title", None, head["app_title"])
    html = re.sub(r'<meta property="og:url" content="[^"]*">',
                  '<meta property="og:url" content="%s">' % url, html, count=1)

    # 3. og:locale, plus the alternate that says which locale this is.
    html, n = re.subn(
        r'<meta property="og:locale" content="[^"]*">',
        '<meta property="og:locale" content="%s">\n    '
        '<meta property="og:locale:alternate" content="en_US" />' % OG_LOCALE[lang],
        html, count=1)
    if n != 1:
        raise SystemExit("[FAIL] no og:locale in the English page")

    # 4. The links.
    html = re.sub(
        r'(<a\b[^>]*?\shref\s*=\s*")([^"]*)(")',
        lambda m: m.group(1) + localize_href(m.group(2), lang, root) + m.group(3),
        html)

    # 5. The JSON-LD.
    html = localize_schema(html, lang, schema)

    return html


SLUG = ""


def main():
    global SLUG
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--head", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    SLUG = args.slug

    head_path = Path(args.head) if args.head else ROOT / ".tmp" / ("%s-head.json" % args.slug)
    if not head_path.exists():
        raise SystemExit("[FAIL] no head file at %s" % head_path)
    heads = json.loads(head_path.read_text(encoding="utf-8"))
    jsonld = heads.get("jsonld") or {}

    en_path = ROOT / "tools" / args.slug / "index.html"
    en_html = en_path.read_text(encoding="utf-8")

    langs = [l for l in heads if l != "en" and l != "jsonld"]
    if not langs:
        raise SystemExit("[FAIL] the head file has no language besides en")

    for lang in langs:
        need = ["title", "description", "og_title", "og_description",
                "twitter_title", "twitter_description", "og_image_alt", "app_title"]
        missing = [k for k in need if not heads[lang].get(k)]
        if missing:
            raise SystemExit("[FAIL] %s is missing head fields: %s" % (lang, missing))
        html = build_copy(en_html, lang, heads[lang], ROOT,
                          (jsonld.get(lang) if isinstance(jsonld, dict) else None))
        dest = ROOT / lang / "tools" / args.slug / "index.html"
        if args.dry_run:
            print("  %s -> %s (%d bytes)" % (lang, dest.relative_to(ROOT), len(html.encode("utf-8"))))
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8", newline="\n")
        print("  %s -> %s (%d bytes)" % (lang, dest.relative_to(ROOT), len(html.encode("utf-8"))))

    print("\n%d language copies written" % len(langs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
