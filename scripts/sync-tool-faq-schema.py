#!/usr/bin/env python3
"""Rebuild a TOOL PAGE's FAQPage JSON-LD from the FAQ the reader can see.

WHY THE REPO'S sync-faq-schema.py DOES NOT COVER THIS
----------------------------------------------------
`scripts/sync-faq-schema.py` parses `<details class="faq-item">`. The
tool pages ship their FAQ inside `<div class="qa-block">` with a plain
`<details>`, so that script refuses them - correctly, because it would
otherwise not know which `<details>` on the page is the FAQ.

WHY THE DRIFT MATTERS
---------------------
The stationery tool page's schema said "the names of the hosts if they
are hosting" while the visible answer said "the hosts' names if they are
hosting", and "5 x 7 inch" while the page said "5 x 7 inch" with a
MULTIPLICATION SIGN. A search engine reads the schema as a promise about
the page; when the two disagree the structured data is a liability, and
Google can mark it down as content that does not match the page.

HOW IT WORKS
------------
The visible copy is the source of truth. The schema is rebuilt FROM it,
so the two can never drift again: after this runs, a schema answer IS the
visible answer, character for character.

The visible markup is NOT touched - only the JSON-LD block is rewritten,
and it is rewritten atomically.

Usage:
    python scripts/sync-tool-faq-schema.py tools/<slug>/index.html
    python scripts/sync-tool-faq-schema.py tools/<slug>/index.html --apply
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The FAQ block on a tool page: <div class="qa-block"> ... <details>.
QA_BLOCK_RE = re.compile(r'<div\s+class="qa-block"[^>]*>(.*?)</div>\s*(?:</section>|</div>)',
                         re.DOTALL)
DETAILS_RE = re.compile(r"<details[^>]*>(.*?)</details>", re.DOTALL)
SUMMARY_RE = re.compile(r"<summary[^>]*>(.*?)</summary>", re.DOTALL)
LDJSON_RE = re.compile(r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>',
                        re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")


def strip_tags(text):
    return re.sub(r"\s+", " ", TAG_RE.sub("", text)).strip()


def visible_faq(html):
    """The visible FAQ: [(question, answer)]."""
    out = []
    for m in DETAILS_RE.finditer(html):
        block = m.group(1)
        summ = SUMMARY_RE.search(block)
        if not summ:
            continue
        question = strip_tags(summ.group(1))
        answer = strip_tags(block[summ.end():])
        if question and answer:
            out.append((question, answer))
    return out


def find_faq_block(html):
    """Return (start, end, parsed) of the FAQPage JSON-LD block."""
    for m in LDJSON_RE.finditer(html):
        try:
            obj = json.loads(m.group(1))
        except Exception:  # noqa: BLE001
            continue
        if isinstance(obj, dict) and obj.get("@type") == "FAQPage":
            return m.start(1), m.end(1), obj
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page")
    ap.add_argument("--apply", action="store_true",
                    help="rewrite the block (default: report only)")
    args = ap.parse_args()

    path = Path(args.page)
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        raise SystemExit("[FAIL] no such file: %s" % path)
    html = path.read_text(encoding="utf-8")

    visible = visible_faq(html)
    found = find_faq_block(html)
    if not found:
        print("[FAIL] %s has no FAQPage JSON-LD block" % path.name)
        return 1
    start, end, obj = found
    schema = [(q.get("name", ""), q.get("acceptedAnswer", {}).get("text", ""))
              for q in obj.get("mainEntity", [])]

    if len(visible) != len(schema):
        # A different COUNT is not automatically a broken page: a question
        # may simply have been added to the visible FAQ. What decides it
        # is whether the schema's questions are still THERE.
        #
        #   schema questions ⊆ visible questions  -> the visible copy grew,
        #        rebuild the schema from it (this is the normal case when
        #        a new FAQ entry was added),
        #   a schema question is MISSING from the visible copy -> the
        #        parse picked up something that is not the FAQ, so refuse.
        #
        # The old rule refused on any count difference, which meant a new
        # question could never be added without hand-editing the JSON-LD
        # - and a hand-edited schema drifts from the page, which is the
        # exact problem this script exists to prevent.
        schema_questions = set(q for q, _ in schema)
        visible_questions = set(q for q, _ in visible)
        lost = schema_questions - visible_questions
        if lost:
            print("[FAIL] %s: the page shows %d FAQ items but the schema has "
                  "%d, and %d schema question(s) are not on the page"
                  % (path.name, len(visible), len(schema), len(lost)))
            for q in sorted(lost)[:5]:
                print("       %s" % q)
            return 1
        print("[note] %s: the visible FAQ has %d entries and the schema has %d "
              "- rebuilding from the visible copy"
              % (path.name, len(visible), len(schema)))

    drift = []
    for i, (v, s) in enumerate(zip(visible, schema), 1):
        if v[0] != s[0]:
            drift.append("#%d question\n    schema : %s\n    visible: %s"
                         % (i, s[0], v[0]))
        if v[1] != s[1]:
            drift.append("#%d answer\n    schema : %s\n    visible: %s"
                         % (i, s[1][:120], v[1][:120]))

    if not drift:
        print("OK  %s - the FAQPage schema already matches the visible FAQ"
              % path.name)
        return 0

    print("[DRIFT] %s: %d FAQ field(s) differ" % (path.name, len(drift)))
    for d in drift:
        print("   ", d)

    if not args.apply:
        print("\nrun with --apply to rebuild the schema from the visible copy")
        return 1

    obj["mainEntity"] = [
        {"@type": "Question", "name": q,
         "acceptedAnswer": {"@type": "Answer", "text": a}}
        for q, a in visible
    ]
    new_body = json.dumps(obj, ensure_ascii=False, indent=2)
    out = html[:start] + new_body + html[end:]
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(out)
        fh.flush()
        import os
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    print("\napplied: the FAQPage schema now mirrors the visible FAQ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
