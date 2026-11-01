#!/usr/bin/env python3
"""Check the title / description values the MIDDLEWARE actually serves.

scripts/check-seo-lengths.py measures the static HTML. For the 525 pages
whose title carries `data-i18n` and whose description carries
`data-i18n-attr="content:…"`, the value a visitor receives comes from
i18n/<lang>.json — the static file only holds the English source.

THE KEY MODEL (this is the part that is easy to get wrong)
-----------------------------------------------------------
Every page binds exactly ONE title key and ONE description key. The key set
is the union of every language's variants (the zh key, the ja key, the de
key…), and EVERY dictionary stores all of them — each holding the value in
its OWN language:

    es.json["…title_text.sem_oramento_para_videgrafo…"]  -> Portuguese
    es.json["…title_text.gnstiges_hochzeitsvideo…"]       -> German

The middleware resolves `dict[lang][the key the page binds]`, so for a page
under /es/ only the key THAT page binds matters in es.json. Every other
variant key in es.json is an orphan and never renders.

Therefore the check is per language and per that language's OWN pages.
Scoring every bound key against every dictionary (the naive version)
overstates the backlog by roughly 8×.

Usage:
    python scripts/check-i18n-meta-lengths.py            # report (exit 0)
    python scripts/check-i18n-meta-lengths.py --strict   # exit 1 when over
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "i18n"
TITLE_MAX = 60
DESC_MAX = 160
LANGS = ["en", "de", "es", "fr", "pt", "ja", "ru", "ar", "th", "hi", "zh"]

# Attribute ORDER inside a <meta> tag is not consistent across the site:
#     <meta name="description" data-i18n-attr="content:KEY" content="...">
#     <meta content="..." data-i18n-attr="content:KEY" name="description"/>
# A positional regex only sees the first form. Parse attributes BY NAME.
RE_TITLE_TAG = re.compile(r"<title\b[^>]*>(.*?)</title>", re.DOTALL | re.IGNORECASE)
RE_META_TAG = re.compile(r"<meta\b[^>]*?/?>", re.DOTALL | re.IGNORECASE)
RE_ATTR = re.compile(r"""([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+))""")


def parse_attrs(tag):
    out = {}
    for m in RE_ATTR.finditer(tag):
        out[m.group(1).lower()] = m.group(2) or m.group(3) or m.group(4) or ""
    return out


def bound_meta_keys(text, want_name=None, want_property=None):
    """Every (key, meta-kind) bound through data-i18n-attr="content:KEY"."""
    found = []
    for m in RE_META_TAG.finditer(text):
        a = parse_attrs(m.group(0))
        name = a.get("name", "").lower()
        prop = a.get("property", "").lower()
        if want_name is not None and name != want_name:
            continue
        if want_property is not None and prop != want_property:
            continue
        spec = a.get("data-i18n-attr", "")
        for part in spec.split("|"):
            if part.startswith("content:"):
                found.append((part[len("content:"):], name or prop))
    return found


def bound_title_keys(text):
    out = []
    for m in RE_TITLE_TAG.finditer(text):
        a = parse_attrs(m.group(0)[: m.group(0).index(">") + 1])
        if "data-i18n" in a:
            out.append(a["data-i18n"])
    return out


SKIP = {".tmp", ".git", "node_modules", "qa", "internal-tools", "private", "scripts"}

# ---------------------------------------------------------------------------
# The title a visitor actually receives is not the dictionary value.
#
# functions/_middleware.js `localizeCurrencyForLang` rewrites every "$X" in
# the document into "$X <span class="wa-local-price">(≈ EUR9)</span>". The
# <meta> tags are stashed first, so a description is never touched, but the
# <title> is not a meta tag and IS rewritten. The span's markup does not
# count as title text; its text does.
#
# So the served title length is the dictionary length plus the currency text.
# Measuring the dictionary value alone measures a layer nobody sees.
# ---------------------------------------------------------------------------
LANG_TO_CURRENCY = {
    "zh": ("\u00a5", 7.2), "ja": ("\u00a5", 150), "ru": ("\u20bd", 90),
    "ar": ("\u062f.\u0625", 3.67), "th": ("\u0e3f", 35),
    "es": ("\u20ac", 0.92), "fr": ("\u20ac", 0.92), "de": ("\u20ac", 0.92),
    "pt": ("R$", 5.4),
}
# The amount pattern the middleware uses (functions/_middleware.js,
# USD_AMOUNT). A separator followed by exactly three digits is a thousands
# separator ("$1,000"); one or two digits is a decimal comma ("$9,9" = 9.9).
USD_AMOUNT = r"\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?"
PRICE_RE = re.compile(r"\$\s?" + USD_AMOUNT
                     + r"(?:[ \u2013\-]\$\s?" + USD_AMOUNT + r")?")


def parse_usd_amount(token):
    """Read the USD amount out of a matched price token (same rules as the
    middleware's parseUsdAmount)."""
    m = re.search(r"\$\s?(" + USD_AMOUNT + ")", token)
    if not m:
        return None
    s = re.sub(r"[\s\u00a0]", "", m.group(1))
    dec = re.match(r"^(.*?)[.,](\d{1,2})$", s)
    if dec:
        whole = re.sub(r"[.,]", "", dec.group(1)) or "0"
        try:
            return float(f"{whole}.{dec.group(2)}")
        except ValueError:
            return None
    try:
        return float(re.sub(r"[.,]", "", s))
    except ValueError:
        return None


def served_title_length(value, lang):
    """Length of the <title> text the middleware serves."""
    if not isinstance(value, str):
        return 0
    cur = LANG_TO_CURRENCY.get(lang)
    if not cur:
        return len(value)
    symbol, rate = cur
    extra = 0
    for m in PRICE_RE.finditer(value):
        num = parse_usd_amount(m.group(0))
        if num is None:
            continue
        extra += len(f" (\u2248 {symbol}{round(num * rate)})")
    return len(value) + extra


def walk(node, prefix, out):
    if isinstance(node, dict):
        for k, v in node.items():
            walk(v, f"{prefix}.{k}" if prefix else k, out)
    elif isinstance(node, str):
        out[prefix] = node


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--show", type=int, default=8, help="examples per language")
    args = ap.parse_args()

    if not I18N.is_dir():
        print("i18n/ directory not found")
        return 0

    title_owner = defaultdict(set)
    desc_owner = defaultdict(set)
    social_owner = defaultdict(set)
    social_lang = defaultdict(set)
    # (lang, path-without-the-language-prefix) -> the keys the page binds
    page_keys = {}
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT)
        if rel.parts and rel.parts[0] in SKIP:
            continue
        parts = rel.parts
        lang = parts[0] if parts and parts[0] in LANGS else "en"
        try:
            t = p.read_text(encoding="utf-8")
        except Exception:
            continue
        tks = bound_title_keys(t)
        dks = [k for k, _kind in bound_meta_keys(t, want_name="description")]
        for key in tks:
            title_owner[key].add(lang)
        for key in dks:
            desc_owner[key].add(lang)
        for key, kind in bound_meta_keys(t, want_property="og:description"):
            social_owner[kind].add(key)
            social_lang[kind].add(lang)
        for key, kind in bound_meta_keys(t, want_name="twitter:description"):
            social_owner[kind].add(key)
            social_lang[kind].add(lang)
        # the path WITHOUT the language prefix, so a localized page and its
        # English counterpart compare equal
        norm = rel.as_posix()
        if lang != "en":
            norm = norm[len(lang) + 1:]
        page_keys[(lang, norm)] = (set(tks), set(dks))

    # The FALLBACK keys: an English page with no localized twin is served to
    # every other language, with its title/description swapped for that
    # language's translation under the ENGLISH key.
    fallback_title = defaultdict(set)
    fallback_desc = defaultdict(set)
    for lang in LANGS:
        own = {norm for (lg, norm) in page_keys if lg == lang}
        for (lg, norm), (tks, dks) in page_keys.items():
            if lg != "en" or norm in own:
                continue
            fallback_title[lang] |= tks
            fallback_desc[lang] |= dks

    print(f"bound title keys: {len(title_owner)}   bound description keys: {len(desc_owner)}")
    print("(a language also serves the English keys of the English pages it has "
          "no localized twin of)")
    print("(title lengths are measured AS SERVED: the value plus the local-currency "
          "text the middleware appends to a price in the <title>)")
    print(f"{'lang':<6}{'bound':>7}{'title>60':>10}{'desc>160':>10}{'missing':>9}")
    total_t = total_d = total_m = 0
    examples = defaultdict(list)
    for lang in LANGS:
        f = I18N / f"{lang}.json"
        if not f.exists():
            continue
        flat = {}
        walk(json.loads(f.read_text(encoding="utf-8")), "", flat)
        # a key can be bound by an English page AND be live for another
        # language (the fallback path), so this is a UNION, not a filter
        my_t = {k for k, o in title_owner.items() if lang in o} | fallback_title.get(lang, set())
        my_d = {k for k, o in desc_owner.items() if lang in o} | fallback_desc.get(lang, set())
        nt = nd = miss = 0
        for k in my_t:
            v = flat.get(k)
            if v is None:
                miss += 1
            else:
                served = served_title_length(v, lang)
                if served > TITLE_MAX:
                    nt += 1
                    examples[(lang, "title")].append((served, k, v))
        for k in my_d:
            v = flat.get(k)
            if v is None:
                miss += 1
            elif len(v) > DESC_MAX:
                nd += 1
                examples[(lang, "desc")].append((len(v), k, v))
        print(f"{lang:<6}{len(my_t) + len(my_d):>7}{nt:>10}{nd:>10}{miss:>9}")
        total_t += nt
        total_d += nd
        total_m += miss

    print(f"\nlive values over the limit: {total_t} titles, {total_d} descriptions")

    for (lang, kind), items in sorted(examples.items()):
        if not items:
            continue
        print(f"\n--- {lang} {kind} ({len(items)} over) ---")
        for ln, key, val in sorted(items, key=lambda x: -x[0])[:args.show]:
            print(f"  [{ln:>4}] {key[:70]}")
            print(f"         {val[:140]}")

    if total_t or total_d:
        print("\nNOTE: these are the values the middleware serves to that "
              "language's visitors. The static-file check cannot see them. "
              "They are a translation/rewriting job, not a deploy blocker.")
    # ---- og:description / twitter:description (live, never blocking) ------
    for kind in sorted(social_owner):
        n_over = 0
        samples = []
        for lang in LANGS:
            f = I18N / f"{lang}.json"
            if not f.exists():
                continue
            flat = {}
            walk(json.loads(f.read_text(encoding="utf-8")), "", flat)
            for key in social_owner[kind]:
                if lang not in social_lang[kind]:
                    continue
                v = flat.get(key)
                if v is None:
                    continue
                if len(v) > DESC_MAX:
                    n_over += 1
                    samples.append((len(v), lang, key, v))
        print(f"{kind:<20} bound={len(social_owner[kind]):>5}  over {DESC_MAX}: {n_over}")
        for ln, lang, key, v in sorted(samples, reverse=True)[:args.show]:
            print(f"    [{ln:>4}] {lang} {key[:66]}")
            print(f"           {v[:140]}")

    if args.strict and (total_t or total_d):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
