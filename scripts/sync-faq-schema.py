#!/usr/bin/env python3
"""Sync the FAQPage JSON-LD with the visible FAQ on every page.

The pre-deploy gate (internal-tools/pre-deploy-check.ps1 -> scripts/verify-schemas.py)
compares two numbers per page:

  visible  = number of <details class="faq-item"> blocks
  json-ld  = len(mainEntity) of the page's FAQPage JSON-LD block

and fails when they differ. A page that shows an FAQ but ships no FAQPage
schema gets no rich-result eligibility at all, and a page whose schema has
drifted from the visible copy is a Google structured-data violation.

Usage:
    python scripts/sync-faq-schema.py           # report only
    python scripts/sync-faq-schema.py --apply   # rewrite the JSON-LD blocks

The FAQPage block is rebuilt from the VISIBLE copy, so the schema can never
describe something the reader does not see. Markup inside an answer is
flattened to text; HTML entities are decoded. Answers are anchored as
#faq-N, and the matching id is added to each <details> so the anchor
actually resolves.
"""

import argparse
import json
import re
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Same segment list the verifier uses, so the two tools can never disagree
# about which pages are in scope. Note "tools" matches EVERY tools/ folder,
# including the localized ones (de/tools, ja/tools, ...).
SKIP_DIRS = {"tmp", ".tmp", "private", "scripts", "tests", "qa",
             "internal-tools", "tools", ".git", ".wrangler", "node_modules"}

DETAILS_RE = re.compile(r'<details([^>]*)class="faq-item"([^>]*)>(.*?)</details>', re.DOTALL)
# The OPENING TAG only. It must never capture the element body: a sub() that
# matches `<details …>…</details>` and returns just the opening tag silently
# deletes the visible answers.
DETAILS_TAG_RE = re.compile(r'<details([^>]*)class="faq-item"([^>]*)>')
SUMMARY_RE = re.compile(r"<summary[^>]*>(.*?)</summary>", re.DOTALL)
LDJSON_RE = re.compile(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
DATE_RE = re.compile(r'"date(?:Published|Modified)"\s*:\s*"(\d{4}-\d{2}-\d{2})"')
FAQ_ID_RE = re.compile(r'\bid="faq-\d+"')

SITE = "https://weddingai.video"
ORG = {
    "@type": "Organization",
    "@id": f"{SITE}/#organization",
    "name": "WeddingAI.video",
    "url": SITE,
}


def clean(text):
    """Flatten markup to plain text and decode entities."""
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def page_url(rel_path):
    rel = rel_path.as_posix()
    if rel.endswith("index.html"):
        rel = rel[: -len("index.html")]
    else:
        rel = rel[: -len(".html")]
    if rel in ("", "/"):
        return f"{SITE}/"
    if rel.endswith("/"):
        return f"{SITE}/{rel}"
    return f"{SITE}/{rel}/"


def extract_faq(html_text):
    """Return [(question, answer)] from the visible <details class="faq-item">."""
    out = []
    for m in DETAILS_RE.finditer(html_text):
        block = m.group(3)
        sm = SUMMARY_RE.search(block)
        if not sm:
            continue
        question = clean(sm.group(1))
        answer = clean(block[sm.end():])
        if question and answer:
            out.append((question, answer))
    return out


def find_faq_block(html_text):
    """Return (start, end, parsed) of the existing FAQPage JSON-LD block."""
    for m in LDJSON_RE.finditer(html_text):
        try:
            data = json.loads(m.group(1))
        except Exception:
            continue
        nodes = data if isinstance(data, list) else [data]
        for n in nodes:
            if isinstance(n, dict) and n.get("@type") == "FAQPage":
                return m.start(), m.end(), n
    return None


def build_block(faq, url, date_created):
    entities = []
    for i, (question, answer) in enumerate(faq, 1):
        entities.append({
            "@type": "Question",
            "name": question,
            "acceptedAnswer": {
                "@type": "Answer",
                "text": answer,
                "upvoteCount": 0,
                "url": f"{url}#faq-{i}",
            },
            "author": ORG,
            "dateCreated": date_created,
            "upvoteCount": 0,
        })
    payload = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": entities,
    }
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    # a literal </script inside the JSON would close the tag early
    raw = raw.replace("</", "<\\/")
    return f'<script type="application/ld+json">{raw}</script>'


def ensure_detail_ids(html_text):
    """Give each faq-item <details> the id its #faq-N anchor points at.

    Only the OPENING TAG is rewritten (DETAILS_TAG_RE). Matching the whole
    element here would replace the visible answer with an empty tag.
    """
    counter = [0]

    def repl(m):
        counter[0] += 1
        attrs = m.group(1) + m.group(2)
        if FAQ_ID_RE.search(attrs):
            return m.group(0)
        return f'<details{m.group(1)}class="faq-item"{m.group(2)} id="faq-{counter[0]}">'

    return DETAILS_TAG_RE.sub(repl, html_text)


def page_date(html_text):
    m = DATE_RE.search(html_text)
    return m.group(1) if m else None


def process(path, apply_changes, report):
    html_text = path.read_text(encoding="utf-8")
    faq = extract_faq(html_text)
    existing = find_faq_block(html_text)

    if not faq and existing is None:
        return False
    if not faq and existing is not None:
        # The page ships an FAQPage block but its visible FAQ uses markup this
        # extractor does not recognise (the tool pages use their own FAQ
        # layout). Rebuilding from an empty extraction would DELETE a working
        # schema, so leave it alone.
        return False
    if existing is not None:
        n_jsonld = len(existing[2].get("mainEntity", []) or [])
    else:
        n_jsonld = None

    if faq and n_jsonld == len(faq):
        return False

    rel = path.relative_to(ROOT)
    if existing is None:
        report.append(f"  {rel}: visible={len(faq)} json-ld=None  (ADD)")
    else:
        report.append(f"  {rel}: visible={len(faq)} json-ld={n_jsonld}  (REBUILD)")

    if not apply_changes:
        return True

    url = page_url(rel)
    date_created = page_date(html_text) or "2026-01-01"
    block = build_block(faq, url, date_created)

    new_html = ensure_detail_ids(html_text)
    if existing is not None:
        s, e, _ = existing
        new_html = new_html[:s] + block + new_html[e:]
    else:
        head_end = new_html.lower().rfind("</head>")
        if head_end == -1:
            head_end = new_html.lower().rfind("</body>")
        new_html = new_html[:head_end] + "  " + block + "\n" + new_html[head_end:]

    path.write_text(new_html, encoding="utf-8", newline="")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write the changes")
    args = ap.parse_args()

    files = []
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT)
        if rel.parts and rel.parts[0] in SKIP_DIRS:
            continue
        files.append(p)

    report = []
    changed = 0
    for p in files:
        try:
            if process(p, args.apply, report):
                changed += 1
        except Exception as e:
            report.append(f"  {p.relative_to(ROOT)}: ERROR {e}")

    if report:
        print("\n".join(report))
    mode = "applied" if args.apply else "would change"
    print(f"\n{changed} page(s) {mode}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
