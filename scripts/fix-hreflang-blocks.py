#!/usr/bin/env python3
"""
Rewrite the hreflang alternate block of every html page to the canonical
12-entry form (11 languages + x-default), with every href pointing at its
own language.

WHY
---
The blocks were hand-written per page and had drifted in three ways:

  1. MISSING LANGUAGES. 670 pages advertised only 10 languages - the `hi`
     graph (added with the November 2026 Hindi launch) was never backfilled,
     so 622 pages were missing an alternate for a language that exists.
  2. THE WRONG LANGUAGE IN THE `zh` SLOT. The block was copied from the
     ENGLISH page and the page's own language prefix was substituted into
     the FIRST localized entry - which in the template is `zh`. So every
     localized page outside the zh folder advertised `zh` pointing at
     ITSELF: an /ar/ page told Google that the Arabic version of the page
     is the Urdu one, and vice versa.
  3. DUPLICATED ENTRIES. 34 pages carried the English page's `en` +
     x-default pair next to their own, so the same hreflang value appeared
     twice.

The middleware already injects a correct 12-entry block at runtime, and
before 2026-11-01 it stripped the author's block first - but its strip regex
only matched ONE attribute order:

    <link rel="alternate" hreflang="xx" href="...">     stripped
    <link href="..." hreflang="xx" rel="alternate"/>     NOT stripped

The 50 hi/blog pages are written in the second form, so their block survived
next to the injected one and the live page served 24 alternate links instead
of 12 ("Hreflang: Multiple Entries"). The middleware now strips any
attribute order; this script makes the SOURCE match what is served, so the
two can no longer disagree.

WHAT IT CHANGES
---------------
Only the <link rel="alternate" ...> tags in <head>. The canonical link, the
title, the body and every other element are left byte-identical. The output
is verified per file: exactly 12 alternates, one per language, each href
matching its hreflang.

Exit code 0 = every file rewritten and verified.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = "https://weddingai.video"

# The canonical order, from js/langs.js. The middleware uses the same order.
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
DEFAULT_LANG = "en"

SKIP_DIRS = ("private/", "i18n/", ".tmp/", "qa/", "node_modules/")

LINK_RE = re.compile(r"<link\b[^>]*>", re.IGNORECASE)
ATTR_RE = re.compile(r"([a-zA-Z-]+)\s*=\s*(?:\"([^\"]*)\"|'([^']*)')")


def attrs_of(tag):
    out = {}
    for m in ATTR_RE.finditer(tag):
        out[m.group(1).lower()] = m.group(2) if m.group(2) is not None else m.group(3)
    return out


def lang_of(path):
    parts = path.split("/")
    if len(parts) > 1 and parts[0] in LANGS:
        return parts[0]
    return DEFAULT_LANG


def rest_of(path):
    """The clean URL path of a page, without the language prefix."""
    parts = path.split("/")
    if len(parts) > 1 and parts[0] in LANGS:
        parts = parts[1:]
    if parts and parts[-1] == "index.html":
        parts = parts[:-1]
    return ("/".join(parts) + "/") if parts else ""


def canonical_block(rest):
    """The 12 alternate links, in the middleware's exact format."""
    out = []
    for l in LANGS:
        href = f"{BASE}/{l}/{rest}" if l != DEFAULT_LANG else f"{BASE}/{rest}"
        out.append(f'<link rel="alternate" hreflang="{l}" href="{href}">')
    out.append(f'<link rel="alternate" hreflang="x-default" href="{BASE}/{rest}">')
    return out


def main():
    changed = 0
    unchanged = 0
    bom_fixed = 0
    failures = []

    print("=" * 90)
    print("HREFLANG BLOCK NORMALIZATION")
    print("=" * 90)

    for path in sorted(REPO.rglob("*.html")):
        rel = path.relative_to(REPO).as_posix()
        if rel.startswith(SKIP_DIRS):
            continue
        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        if had_bom:
            # 633 of the 722 html files started with a UTF-8 BOM. It is
            # harmless in a browser, but it breaks every naive text tool:
            # `text.startswith("<!DOCTYPE")` is False, `re.match(r"^<html")`
            # is None, and this very script refused to touch the file.
            raw = raw[3:]
        html = raw.decode("utf-8")

        alts = []
        for m in LINK_RE.finditer(html):
            a = attrs_of(m.group(0))
            if a.get("rel", "").lower() == "alternate" and a.get("hreflang"):
                alts.append(m)

        if not alts:
            if had_bom:
                path.write_bytes(raw)
                bom_fixed += 1
            continue

        rest = rest_of(rel)
        want = canonical_block(rest)

        # The indentation of the first alternate link, so the rewritten block
        # sits in the file the way it did before.
        first = alts[0]
        line_start = html.rfind("\n", 0, first.start()) + 1
        indent = html[line_start:first.start()]
        if indent.strip():
            indent = ""

        new_block = ("\n" + indent).join(want)

        # Remove every alternate tag together with the whitespace that
        # preceded it, then put the canonical block where the first one was.
        spans = []
        for m in alts:
            start = m.start()
            ls = html.rfind("\n", 0, start) + 1
            if not html[ls:start].strip():
                start = ls
            spans.append((start, m.end()))
        # A canonical link must never be swallowed by the replacement.
        for m in LINK_RE.finditer(html):
            if attrs_of(m.group(0)).get("rel", "").lower() == "canonical":
                for s, e in spans:
                    if s <= m.start() < e:
                        failures.append(f"{rel}: a canonical link sits inside the "
                                        f"alternate block - skipped")
                        spans = None
                        break
            if spans is None:
                break
        if spans is None:
            continue

        out = []
        cursor = 0
        for i, (s, e) in enumerate(spans):
            out.append(html[cursor:s])
            if i == 0:
                out.append(new_block)
            cursor = e
        out.append(html[cursor:])
        new_html = "".join(out)

        # --- verify the result before writing ---------------------------
        got = [attrs_of(m.group(0)) for m in LINK_RE.finditer(new_html)
               if attrs_of(m.group(0)).get("rel", "").lower() == "alternate"]
        problems = []
        if len(got) != 12:
            problems.append(f"{len(got)} alternates instead of 12")
        seen = {}
        for a in got:
            hl = a.get("hreflang")
            if hl in seen:
                problems.append(f"duplicate hreflang '{hl}'")
            seen[hl] = a.get("href")
        for l in LANGS + ["x-default"]:
            if l not in seen:
                problems.append(f"missing '{l}'")
        for l, href in seen.items():
            want_href = (f"{BASE}/{l}/{rest}" if l not in (DEFAULT_LANG, "x-default")
                         else f"{BASE}/{rest}")
            if href != want_href:
                problems.append(f"'{l}' -> {href} (expected {want_href})")
        if problems:
            failures.append(f"{rel}: " + "; ".join(problems))
            continue

        if new_html == html and not had_bom:
            unchanged += 1
            continue

        path.write_bytes(new_html.encode("utf-8"))
        changed += 1
        if had_bom:
            bom_fixed += 1

    print(f"  rewritten: {changed}")
    print(f"  already correct: {unchanged}")
    print(f"  UTF-8 BOM removed: {bom_fixed}")
    print()
    if failures:
        print(f"RESULT: {len(failures)} FAILURE(S)")
        for f in failures[:25]:
            print("  - " + f)
        if len(failures) > 25:
            print(f"  ... and {len(failures) - 25} more")
        return 1
    print("RESULT: every page advertises exactly one alternate per language "
          "(11 + x-default) and every href matches its hreflang")
    return 0


if __name__ == "__main__":
    sys.exit(main())
