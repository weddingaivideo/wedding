#!/usr/bin/env python3
"""
Check the five tool pages against the rules the SERP research sets.

The rules (internal-tools/serp-research-4-tools.md, section 5, plus
internal-tools/serp-research-stationery.md):

  1. the page leads with "runs in your browser / nothing is uploaded",
  2. the entry strings are present: free, no watermark, no signup, no upload.
     "no account" counts for "no signup" and "never uploaded" counts for
     "no upload" - the SERP pages say it both ways and a gate that only
     accepts one wording flags a correct page,
  3. the page publishes its LIMITS - a stated ceiling, not a silent one,
  4. the FAQ has 6-12 questions,
  5. the page compares itself with the alternatives,
  6. NO PRICE anywhere in the tool's own copy. The footer nav carries a
     "Pricing" link on every page of the site; that is site chrome, not
     the tool's copy, so the check reads <main> only.

Usage
-----
    python scripts/check-tool-serp-rules.py
"""
import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLUGS = ["wedding-stationery-set-maker", "wedding-photo-contact-sheet",
         "wedding-pdf-editor", "wedding-photo-to-gif", "wedding-video-editor"]

# A price on a tool page contradicts the promise that the tool is free.
#
# The bare words "buy", "cost" and "pricing" are NOT prices: the pages
# say "there is nothing to buy and nothing to upgrade to", "the paper is
# the only part you buy" and "the iLovePDF pricing page, via pixeltools.io
# (checked 2026-11-04)" - the last one is a SOURCE CITATION for a free
# tier limit, which is exactly what the SERP research asks for. So the
# gate looks for MONEY and for a price CLAIM, not for the vocabulary.
PRICE = re.compile(
    r"(\$\s?\d|\b\d[\d,.]*\s?(?:USD|EUR|GBP)\b|€\s?\d|£\s?\d|¥\s?\d"
    r"|\bper month\b|/\s?month\b|\bmonthly\b|\bsubscription\b"
    r"|\bstarts at\b|\bone-time\b|\bfree trial\b|\bpaid plan\b"
    r"|\bpaid tier\b|\bpro tier\b)", re.I)

# The entry strings, with the wording variants the SERP pages use.
FREE = ["free"]
WATERMARK = ["no watermark", "without a watermark"]
SIGNUP = ["no signup", "no sign-up", "no account", "without an account",
          "no registration", "no login"]
UPLOAD = ["not uploaded", "nothing uploaded", "never uploaded",
          "never leaves", "no upload", "without uploading", "stay on your"]

COMPETITORS = ["canva", "lightroom", "picmonkey", "adobe", "greetings island",
               "smallpdf", "ilovepdf", "pdf24", "pixelcut", "remove.bg",
               "clipchamp", "capcut", "kapwing", "veed", "descript",
               "flexclip", "invideo", "davinci", "fliki", "imovie",
               "convertbox", "feelthefile", "smoothclip", "justright",
               "videotools", "freetoolsonline", "ezgif", "giphy", "shotcut",
               "ffmpeg", "local print shop", "print shop", "a print shop",
               "lightroom classic"]


def main_of(html):
    m = re.search(r"<main[^>]*>(.*)</main>", html, re.S)
    return m.group(1) if m else html


def clean(s):
    s = re.sub(r"<(script|style)\b.*?</\1>", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def has_any(text, needles):
    low = text.lower()
    return any(n in low for n in needles)


def main():
    failed = False
    for slug in SLUGS:
        path = ROOT / "tools" / slug / "index.html"
        html = path.read_text(encoding="utf-8")
        body = main_of(html)
        text = clean(body)
        low = text.lower()

        faq = [clean(f) for f in re.findall(r"<summary[^>]*>(.*?)</summary>",
                                            body, re.S)]
        faq = [f for f in faq if f]

        problems = []
        if not 6 <= len(faq) <= 12:
            problems.append("the FAQ has %d questions (6-12 wanted)"
                            % len(faq))
        for label, needles in (("free", FREE), ("no watermark", WATERMARK),
                               ("no signup", SIGNUP), ("no upload", UPLOAD)):
            if not has_any(text, needles):
                problems.append("the entry string %r is missing" % label)

        limits = re.findall(r"[^.]{0,120}(up to \d[\d,.]*\s?\w*|at most|"
                            r"limited to|limited by|maximum of|"
                            r"cannot hold|too (big|large))[^.]{0,120}\.",
                            text, re.I)
        if not limits:
            problems.append("no stated limit")

        rivals = [c for c in COMPETITORS if c in low]
        if not rivals:
            problems.append("no comparison with the alternatives")

        prices = sorted(set(m.group(0).strip() for m in PRICE.finditer(text)))
        if prices:
            problems.append("a price in the tool's own copy: %s" % prices)

        print("== %-32s FAQ=%-3d limits=%-2d rivals=%s"
              % (slug, len(faq), len(limits),
                 ",".join(sorted(set(rivals))[:4]) or "-"))
        if problems:
            failed = True
            for p in problems:
                print("   [FAIL] %s" % p)
        else:
            print("   [OK]")
    if failed:
        print("\n[FAIL] at least one tool page breaks the SERP rules")
        return 1
    print("\n[OK] all five tool pages pass the SERP rules")
    return 0


if __name__ == "__main__":
    sys.exit(main())
