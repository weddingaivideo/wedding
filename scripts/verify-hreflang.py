#!/usr/bin/env python3
"""
Audit the hreflang blocks of every html page.

WHAT THIS CHECKS
----------------
A page must advertise exactly ONE alternate per language, plus x-default:

    en -> https://weddingai.video/<rest>/
    zh -> https://weddingai.video/zh/<rest>/
    ...
    x-default -> https://weddingai.video/<rest>/

and every one of those hrefs must actually be the URL of that language. The
page's own language must point at itself.

WHY THIS NEEDS A SCRIPT
-----------------------
The two defects it looks for are both invisible to a naive reading:

  * a duplicated hreflang value (the same language advertised twice, or the
    en + x-default pair pointing at the same URL), and
  * an alternate whose hreflang says one language while its href points at
    another language's URL.

The second one is a copy/paste artefact: the hreflang block is copied from
the ENGLISH page and the page's own language prefix is substituted into the
FIRST localized entry - which in the template is `zh`. So every localized
page outside the zh folder advertised `zh` pointing at ITSELF.

The markup also comes in two attribute orders:

    <link rel="alternate" hreflang="xx" href="...">
    <link href="..." hreflang="xx" rel="alternate">

so the parser below reads the attributes instead of matching one fixed
string. A regex written against one form reports "0 problems" on the pages
that use the other form - which is exactly what happened.

Exit code 0 = every page is consistent.
"""
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = "https://weddingai.video"
LANGS = ["ar", "de", "en", "es", "fr", "hi", "ja", "pt", "ru", "th", "zh"]
SKIP_DIRS = ("private/", "i18n/", ".tmp/", "qa/", "node_modules/")

LINK_RE = re.compile(r"<link\b([^>]*)>", re.IGNORECASE)
ATTR_RE = re.compile(r"([a-zA-Z-]+)\s*=\s*\"([^\"]*)\"")


def lang_of(path):
    """The language a page belongs to ('en' for the English source)."""
    parts = path.split("/")
    if len(parts) > 1 and parts[0] in LANGS:
        return parts[0]
    return "en"


def rest_of(path):
    """The URL path of a page, without the language prefix.

    The site uses clean URLs: the file about/index.html is served as
    /about/, and the file index.html is served as /.
    """
    parts = path.split("/")
    if len(parts) > 1 and parts[0] in LANGS:
        parts = parts[1:]
    if parts and parts[-1] == "index.html":
        parts = parts[:-1]
    if not parts:
        return ""
    return "/".join(parts) + "/"


def alternates(html):
    """(hreflang, href) for every rel="alternate" link, order-agnostic."""
    out = []
    for m in LINK_RE.finditer(html):
        attrs = {k.lower(): v for k, v in ATTR_RE.findall(m.group(1))}
        if attrs.get("rel", "").lower() != "alternate":
            continue
        if "hreflang" not in attrs:
            continue
        out.append((attrs["hreflang"], attrs.get("href", "")))
    return out


def main():
    problems = Counter()
    detail = []
    pages = 0

    for path in sorted(REPO.rglob("*.html")):
        rel = path.relative_to(REPO).as_posix()
        if rel.startswith(SKIP_DIRS):
            continue
        try:
            html = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        pairs = alternates(html)
        if not pairs:
            continue
        pages += 1

        lang = lang_of(rel)
        rest = rest_of(rel)
        en_url = f"{BASE}/{rest}" if rest else BASE
        own_url = f"{BASE}/{lang}/{rest}" if lang != "en" else en_url

        seen = Counter(hl for hl, _ in pairs)
        for hl, n in seen.items():
            if n > 1:
                problems["duplicate hreflang"] += 1
                detail.append(f"{rel}: hreflang '{hl}' appears {n}x")
        missing = [l for l in LANGS if l not in seen]
        if missing:
            problems["missing language"] += 1
            detail.append(f"{rel}: no alternate for {', '.join(missing)}")
        if "x-default" not in seen:
            problems["missing x-default"] += 1
            detail.append(f"{rel}: no x-default alternate")

        by_lang = {}
        for hl, href in pairs:
            by_lang.setdefault(hl, []).append(href)
        for hl, hrefs in by_lang.items():
            if hl == "x-default":
                want = en_url
            elif hl == "en":
                want = en_url
            else:
                want = f"{BASE}/{hl}/{rest}"
            for href in hrefs:
                if href.rstrip("/") != want.rstrip("/"):
                    problems["href points at the wrong language"] += 1
                    detail.append(
                        f"{rel}: hreflang '{hl}' -> {href}  (expected {want})")
        # the page must point at itself
        own = by_lang.get(lang, [])
        for href in own:
            if href.rstrip("/") != own_url.rstrip("/"):
                problems["own language points elsewhere"] += 1
                detail.append(f"{rel}: '{lang}' -> {href} (expected {own_url})")

    print("=" * 100)
    print("HREFLANG AUDIT")
    print("=" * 100)
    print(f"pages with an alternate block: {pages}")
    print()
    if not problems:
        print("RESULT: every page advertises exactly one alternate per language "
              "(11 languages + x-default) and every href matches its hreflang.")
        return 0

    print("--- problems ---")
    for kind, n in problems.most_common():
        print(f"  {n:>5}  {kind}")
    print()
    print("--- first 40 details ---")
    for line in detail[:40]:
        print("  " + line)
    if len(detail) > 40:
        print(f"  ... and {len(detail) - 40} more")
    print()
    print(f"RESULT: {sum(problems.values())} PROBLEM(S)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
