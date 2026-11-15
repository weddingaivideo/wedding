# -*- coding: utf-8 -*-
"""Keep untranslated /guides/ pages out of the index until they are filled.

A page whose body is still English must not compete with its English twin in
the hreflang cluster. This script detects such languages by comparing each
translated value with the English source, then marks their 33 guide pages
noindex,follow and removes those URLs from that language's sitemap.

`--unmark` reverses both changes once the translations are complete.
"""
import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("tg", ROOT / ".tmp" / "translate-guides.py")
tg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tg)
spec2 = importlib.util.spec_from_file_location("guides", ROOT / "scripts" / "add-tool-guides.py")
guides = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(guides)

TABLE = ROOT / ".tmp" / "guide-translations.json"
LANGS = ["zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
MARK = '<meta name="robots" content="noindex,follow">'
THRESHOLD = 0.25          # >25% English echo => treat the language as incomplete


def cognate_ok(en, key):
    """Short single-token labels (WebP, RSVP, Audio, Guides...) legitimately
    stay identical across languages; do not count them as English echoes."""
    s = en.strip()
    if " " in s or len(s) > 12:
        return False
    return bool(re.search(r"\.f\d+l$", key)) or key.startswith("guides.common.")


def incomplete_langs():
    src = tg.build_source()
    data = json.loads(TABLE.read_text(encoding="utf-8"))
    out = []
    for lang in LANGS:
        same = sum(1 for k, en in src.items()
                   if data.get("%s|%s" % (lang, k), "").strip() == en.strip()
                   and not cognate_ok(en, k))
        ratio = same / len(src)
        print("  %-3s english-echo %4d/%d = %.1f%%" %
              (lang, same, len(src), ratio * 100))
        if ratio > THRESHOLD:
            out.append(lang)
    return out


def guide_pages(lang):
    base = (ROOT if lang == "en" else ROOT / lang) / "guides"
    return [base / "index.html"] + [base / s / "index.html" for s in guides.SLUGS]


def toggle_noindex(lang, add):
    n = 0
    for p in guide_pages(lang):
        if not p.exists():
            continue
        s = p.read_text(encoding="utf-8")
        if add and MARK not in s:
            i = s.find('<meta name="viewport"')
            if i < 0:
                continue
            eol = s.find("\n", i)
            s = s[:eol + 1] + MARK + "\n" + s[eol + 1:]
        elif not add and MARK in s:
            s = s.replace(MARK + "\n", "", 1).replace(MARK, "", 1)
        else:
            continue
        p.write_text(s, encoding="utf-8", newline="")
        n += 1
    return n


def sitemap_entry(lang, slug):
    # Reuse the generator's exact entry so --unmark restores byte-identical XML.
    return guides.sitemap_entry(lang, slug)


URL_BLOCK = re.compile(r"[ \t]*<url>[\s\S]*?</url>[ \t]*\r?\n?")


def guide_entries(lang):
    """(loc, freshly generated <url> block) for the hub + all 32 guides."""
    out = []
    for slug in [None] + guides.SLUGS:
        entry = sitemap_entry(lang, slug)
        m = re.search(r"<loc>([^<]*)</loc>", entry)
        if m:
            out.append((m.group(1), entry))
    return out


def present_guide_locs(s, wanted):
    found = set()
    for block in URL_BLOCK.finditer(s):
        m = re.search(r"<loc>([^<]*)</loc>", block.group(0))
        if m and m.group(1) in wanted:
            found.add(m.group(1))
    return found


def remove_guide_urls(s, wanted):
    """Delete <url> blocks by <loc>, independent of their <lastmod> value.

    Byte-comparing a freshly generated block fails once
    sync-sitemap-lastmod.py has rewritten the dates, which silently leaves
    quarantined URLs in the sitemap.
    """
    def drop(m):
        loc = re.search(r"<loc>([^<]*)</loc>", m.group(0))
        return "" if loc and loc.group(1) in wanted else m.group(0)
    return URL_BLOCK.sub(drop, s)


def toggle_sitemap(lang, add):
    p = ROOT / ("sitemap-%s.xml" % lang)
    if not p.exists():
        return 0
    s = p.read_text(encoding="utf-8")
    entries = guide_entries(lang)
    wanted = {loc for loc, _ in entries}
    present = present_guide_locs(s, wanted)

    if not add:
        if not present:
            return 0
        p.write_text(remove_guide_urls(s, wanted), encoding="utf-8", newline="\n")
        return len(present)

    # Partial quarantines remove individual <url> blocks while leaving other
    # /guides/ entries in place, so "does this sitemap contain /guides/?" is
    # not a safe completeness test. Restore by <loc>, one entry at a time.
    missing = [entry for loc, entry in entries if loc not in present]
    if not missing:
        return 0
    p.write_text(s.replace("</urlset>", "".join(missing) + "</urlset>", 1),
                 encoding="utf-8", newline="\n")
    return len(missing)


def partial_pages(exclude_langs):
    """A single guide whose translation batch failed should not poison a whole
    language. Detect per-page English echo and quarantine just that URL."""
    src = tg.build_source()
    data = json.loads(TABLE.read_text(encoding="utf-8"))
    quarantined = {}
    for lang in LANGS:
        if lang in exclude_langs:
            continue
        def echo_ratio(path):
            """Measure the keys the page ACTUALLY binds.

            The hub also renders a card for all 32 guides, so checking only
            guides.common.* keys badly understates its English content.
            """
            if not path.exists():
                return 0.0
            keys = re.findall(r'data-i18n="([^"]+)"',
                              path.read_text(encoding="utf-8"))
            keys = [k for k in keys if k in src]
            if not keys:
                return 0.0
            n = sum(1 for k in keys
                    if data.get("%s|%s" % (lang, k), "").strip() == src[k].strip()
                    and not cognate_ok(src[k], k))
            return n / len(keys)

        base = ROOT / lang / "guides"
        bad = [None] if echo_ratio(base / "index.html") > 0.5 else []
        for slug in guides.SLUGS:
            if echo_ratio(base / slug / "index.html") > 0.5:
                bad.append(slug)
        if not bad:
            continue
        quarantined[lang] = bad
        for slug in bad:
            p = (ROOT / lang / "guides" / "index.html" if slug is None
                 else ROOT / lang / "guides" / slug / "index.html")
            if p.exists():
                toggle_noindex_file(p, True)
            sm = ROOT / ("sitemap-%s.xml" % lang)
            if sm.exists():
                s = sm.read_text(encoding="utf-8")
                m = re.search(r"<loc>([^<]*)</loc>", sitemap_entry(lang, slug))
                if m and present_guide_locs(s, {m.group(1)}):
                    sm.write_text(remove_guide_urls(s, {m.group(1)}),
                                  encoding="utf-8", newline="\n")
        print("  %-3s quarantined %d pages: %s" %
              (lang, len(bad), ["<hub>" if x is None else x for x in bad][:8]))
    return quarantined


def toggle_noindex_file(p, add):
    s = p.read_text(encoding="utf-8")
    if add and MARK not in s:
        i = s.find('<meta name="viewport"')
        if i < 0:
            return 0
        eol = s.find("\n", i)
        s = s[:eol + 1] + MARK + "\n" + s[eol + 1:]
    elif not add and MARK in s:
        s = s.replace(MARK + "\n", "", 1).replace(MARK, "", 1)
    else:
        return 0
    p.write_text(s, encoding="utf-8", newline="")
    return 1


def update_verifier(full_langs, partial):
    p = ROOT / "scripts" / "verify-sitemaps.py"
    if not p.exists():
        return
    expected = {"sitemap.xml": 11}
    for l in ["en"] + LANGS:
        n = 189
        if l in full_langs:
            n -= 33
        n -= len(partial.get(l, []))
        expected["sitemap-%s.xml" % l] = n
    body = "EXPECTED_URLS = " + json.dumps(expected, indent=4)
    s = p.read_text(encoding="utf-8")
    s = re.sub(r'EXPECTED_URLS = \{[^}]*\}', body, s, count=1)
    p.write_text(s, encoding="utf-8", newline="")
    print("verify-sitemaps.py expectations updated")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unmark", action="store_true")
    args = ap.parse_args()
    incomplete_langs()               # diagnostic: print echo ratios per lang
    # Quarantine per page, never per language. A language with a third of its
    # keys still untranslated usually has two thirds of its pages COMPLETE;
    # a whole-language noindex would hide those good pages for no reason.
    langs = LANGS if args.unmark else []
    if args.unmark:
        # Do not rely on the marker still being present: re-running the page
        # generator rewrites every guide page and drops it. Sweep all langs so
        # partial sitemap quarantines are restored too.
        print("unmarking all languages:", langs)
    for lang in langs:
        n = toggle_noindex(lang, not args.unmark)
        m = toggle_sitemap(lang, args.unmark)
        print("  %-3s pages=%2d sitemap=%2d (%s)" %
              (lang, n, m, "unmarked" if args.unmark else "noindex"))
    partial = {} if args.unmark else partial_pages(langs)
    update_verifier([] if args.unmark else langs, partial)
    print("done")


if __name__ == "__main__":
    main()
