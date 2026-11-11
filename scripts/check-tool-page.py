#!/usr/bin/env python3
"""
Check a tool page before it goes live.

WHY A SCRIPT AND NOT A READ
---------------------------
A tool page has about a dozen ways to be broken that a diff does not show:

* an ES2020+ construct (`?.`, `??`, `let`, template literals) that the
  project's browser floor does not have,
* a `getElementById("x")` for an element that does not exist - the code
  runs, the button does nothing,
* a link to a blog post that was never written - a 404 on a page that is
  supposed to be the internal-link hub of the site,
* a PRICE on a tool page. The tools are free; a price on a tool page
  contradicts the product claim (see AGENTS.md),
* a title over 60 characters or a description over 160 - the deploy gate
  `scripts/check-seo-lengths.py` fails the build on those,
* a FAQPage schema whose text differs from the FAQ the reader can see -
  structured data that contradicts the page it sits on.

Every one of those is invisible in a diff and fatal in production.

A SELF-FALSIFYING CHECK
-----------------------
A checker that can only pass proves nothing. This script has
`--negative-control`: it injects a known defect into a COPY of the page
(a price, a 90-character title, a broken id) and requires the checker to
report it. If the checker stays quiet on the broken copy, the checker
is broken - not the page.

Usage
-----
    python scripts/check-tool-page.py tools/wedding-stationery-set-maker/index.html
    python scripts/check-tool-page.py tools/<slug>/index.html --negative-control
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TITLE_MAX = 60
DESC_MAX = 160

# ES2020+ constructs the browser floor does not have. `let` / `const` /
# template literals are banned outright: the page has to run in the
# browsers the site supports without a transpile step.
BANNED = [
    ("optional chaining", r"\?\."),
    ("nullish coalescing", r"\?\?"),
    ("let", r"(?<![\w.$])let\s"),
    ("const", r"(?<![\w.$])const\s"),
    ("template literal", r"`"),
    ("arrow function", r"=>"),
    ("async function", r"(?<![\w.$])async\s"),
    ("await", r"(?<![\w.$])await\s"),
    ("class", r"(?<![\w.$])class\s"),
    ("spread", r"\.\.\."),
    ("exponent assignment", r"\*\*="),
    ("logical assignment", r"\|\|=|&&=|\?\?="),
    ("document.write", r"document\s*\.\s*write\b"),
    ("eval", r"(?<![\w.$])eval\s*\("),
    ("new Function", r"new\s+Function\s*\("),
]

# A price on a tool page. The number forms are what a price looks like;
# "free" is the promise, not a price.
PRICE_RE = re.compile(
    r"(\$\s?\d|\d\s?\$|USD\s?\d|\d\s?USD|EUR\s?\d|\d\s?EUR|"
    r"£\s?\d|\d\s?£|¥\s?\d|\d\s?¥|₹\s?\d|\d\s?₹)")
# ...but the structured data is allowed to say the tool is free.
PRICE_ALLOWED_CONTEXT = re.compile(r'"(?:price|priceCurrency|lowPrice|highPrice)"\s*:\s*"?0"?')

LINK_RE = re.compile(r'(?:href|src)\s*=\s*"(/[^"#?]+)"')
SCRIPT_RE = re.compile(r"(?s)<script\b([^>]*)>(.*?)</script>")
TITLE_RE = re.compile(r"<title\b[^>]*>(.*?)</title>", re.S)
DESC_RE = re.compile(r'<meta\b[^>]*\bname="description"[^>]*\bcontent="([^"]*)"', re.S)
ID_RE = re.compile(r'\bid="([^"]+)"')
GETID_RE = re.compile(r'getElementById\(\s*[\'"]([^\'"]+)[\'"]\s*\)')
DETAILS_RE = re.compile(r"<details[^>]*>(.*?)</details>", re.S)
SUMMARY_RE = re.compile(r"<summary[^>]*>(.*?)</summary>", re.S)
STRIP_RE = re.compile(r"<[^>]+>")


def strip_tags(text):
    return STRIP_RE.sub("", text).strip()


def lang_dirs():
    out = []
    for d in sorted((ROOT).iterdir()):
        if d.is_dir() and len(d.name) == 2 and d.name.isalpha():
            out.append(d.name)
    return out


def check_links(html, problems):
    """Every internal link must point at a file that exists."""
    langs = set(lang_dirs())
    for path in sorted(set(LINK_RE.findall(html))):
        if path.startswith("/js/") or path.startswith("/css/") \
                or path.startswith("/fonts/") or path.startswith("/images/"):
            # A static asset - it must exist on disk.
            target = ROOT / path.lstrip("/")
            if not target.exists():
                problems.append("asset link does not exist: %s" % path)
            continue
        parts = [p for p in path.split("/") if p]
        if parts and parts[0] in langs:
            parts = parts[1:]
        if not parts:
            continue
        base = ROOT.joinpath(*parts)
        if base.is_dir():
            if not (base / "index.html").exists():
                problems.append("link points at a directory without index.html: %s" % path)
        elif base.suffix == ".html":
            if not base.exists():
                problems.append("link points at a missing page: %s" % path)
        elif not (base.exists() or (base / "index.html").exists()):
            problems.append("link points at a missing file: %s" % path)


def check_prices(html, problems):
    for m in PRICE_RE.finditer(html):
        start = max(0, m.start() - 90)
        context = html[start:m.end() + 40]
        if PRICE_ALLOWED_CONTEXT.search(context):
            continue
        problems.append("a tool page must not show a price: %r" % m.group(0))


def check_faq_parity(html, problems):
    """The FAQPage schema must describe the FAQ the reader can see."""
    schema_faq = []
    for m in SCRIPT_RE.finditer(html):
        attrs, body = m.group(1), m.group(2)
        if "ld+json" not in attrs:
            continue
        try:
            obj = json.loads(body)
        except Exception:  # noqa: BLE001
            continue
        if isinstance(obj, dict) and obj.get("@type") == "FAQPage":
            for q in obj.get("mainEntity", []):
                schema_faq.append((q.get("name", ""),
                                   q.get("acceptedAnswer", {}).get("text", "")))
    if not schema_faq:
        return
    visible = []
    for m in DETAILS_RE.finditer(html):
        block = m.group(1)
        summ = SUMMARY_RE.search(block)
        if not summ:
            continue
        question = strip_tags(summ.group(1))
        # summ.END(), not len(summ.group(0)): the summary does not start at
        # position 0 of the block (there is whitespace before it), so
        # slicing by the MATCH LENGTH shifts the answer into the middle
        # of the question.
        answer = strip_tags(block[summ.end():])
        visible.append((question, answer))
    if len(visible) != len(schema_faq):
        problems.append("FAQPage has %d questions but the page shows %d"
                        % (len(schema_faq), len(visible)))
        return
    for (sq, sa), (vq, va) in zip(schema_faq, visible):
        if strip_tags(sq) != vq:
            problems.append("FAQ schema question differs from the visible one: %r" % sq[:60])
        if strip_tags(sa) != va:
            problems.append("FAQ schema answer differs from the visible one: %r" % sa[:60])


def run_checks(html, label, problems, skip_faq_parity=False):
    """The checks. Returns the list of problems found in this html."""
    found = []

    # 1. ES floor + no dynamic code, in the INLINE scripts only.
    for m in SCRIPT_RE.finditer(html):
        attrs, body = m.group(1), m.group(2)
        if "ld+json" in attrs or "src=" in attrs:
            continue
        if not body.strip():
            continue
        if "clarity" in body and len(body) < 600:
            continue
        for name, pattern in BANNED:
            if re.search(pattern, body):
                found.append("%s: inline script uses %s" % (label, name))

    # 2. Every getElementById target must exist.
    ids = set(ID_RE.findall(html))
    for target in sorted(set(GETID_RE.findall(html))):
        if target not in ids:
            found.append("%s: getElementById(%r) has no element" % (label, target))

    # 3. Title and description budgets.
    m = TITLE_RE.search(html)
    if not m:
        found.append("%s: no <title>" % label)
    else:
        title = strip_tags(m.group(1))
        if len(title) > TITLE_MAX:
            found.append("%s: title is %d characters (max %d): %r"
                         % (label, len(title), TITLE_MAX, title[:70]))
    m = DESC_RE.search(html)
    if not m:
        found.append("%s: no meta description" % label)
    else:
        desc = m.group(1)
        if len(desc) > DESC_MAX:
            found.append("%s: description is %d characters (max %d): %r"
                         % (label, len(desc), DESC_MAX, desc[:70]))

    # 4. Prices.
    check_prices(html, found)

    # 5. FAQ parity.
    if not skip_faq_parity:
        check_faq_parity(html, found)

    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page", help="the tool page to check")
    ap.add_argument("--negative-control", action="store_true",
                    help="inject a known defect and require the checker to "
                         "report it - proves the checker can fail")
    ap.add_argument("--skip-faq-parity", action="store_true",
                    help="do not compare the FAQ schema with the visible "
                         "FAQ. A language copy carries a PRE-TRANSLATED "
                         "schema while its visible FAQ is still the "
                         "English source (the middleware swaps it at "
                         "request time), so the two only match in the "
                         "served page, not in the file.")
    args = ap.parse_args()

    path = Path(args.page)
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        raise SystemExit("[FAIL] no such file: %s" % path)
    html = path.read_text(encoding="utf-8")

    problems = run_checks(html, path.name, [], skip_faq_parity=args.skip_faq_parity)

    if args.negative_control:
        broken = html.replace("<title>", "<title>xx", 1)
        broken = broken.replace("</title>",
                                " this title is deliberately far too long"
                                " so that the length check has something to"
                                " catch and report</title>", 1)
        broken = broken.replace("</head>",
                                "<p>Everything costs $99</p></head>", 1)
        broken = broken.replace('id="main-content"',
                                'id="main-content" data-broken="1"', 1)
        broken = re.sub(r'getElementById\(\s*([\'"])',
                        r'getElementById(\1no-such-element-', broken, count=1)
        control = run_checks(broken, "NEGATIVE-CONTROL", [])
        expected = ["title", "price", "getElementById"]
        hit = [p for p in control if any(e in p for e in expected)]
        if len(hit) < len(expected):
            print("[FAIL] the negative control did NOT trip every check.")
            print("       a checker that cannot fail proves nothing.")
            for p in control:
                print("   ", p)
            return 1
        print("negative control OK - the checker reports %d injected defects"
              % len(hit))
        for p in hit:
            print("   ", p)

    if problems:
        print("[FAIL] %d problem(s) in %s" % (len(problems), path.name))
        for p in problems:
            print("   ", p)
        return 1
    print("OK  %s" % path.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
