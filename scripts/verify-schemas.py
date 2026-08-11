#!/usr/bin/env python3
"""
Site-wide sanity check for the structured-data upgrade.

For every HTML file under ROOT:
  - parse every <script type="application/ld+json"> block
  - confirm JSON is well-formed
  - collect @type counters

Then prints:
  - total @type distribution (before vs after the upgrade would have shown
    major deltas in Article.speakable, Organization.knowsLanguage, FAQ
    author/upvoteCount, etc.)
  - parse-failure list (must be empty)
  - spot-check on key pages
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = ("tmp", "private", "scripts", "tests", "qa", "internal-tools", "tools")
SCRIPT_RE = re.compile(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', re.DOTALL)
# Visible FAQ questions — source of truth for the FAQPage vs visible count check.
DETAILS_RE = re.compile(r'<details class="faq-item">')
HAS_FAQ = re.compile(r'"@type"\s*:\s*"FAQPage"')

KEY_PAGES = [
    "index.html",
    "gallery/index.html",
    "blog/index.html",
    "blog/weddingai-video-guide/index.html",
    "resources/index.html",
    "about/index.html",
    "pricing/index.html",
    "order/index.html",
    "success/index.html",
    "404.html",
    "services/personalization/ai-video-generator/index.html",
    "services/index.html",
]


def collect_nodes(data):
    if isinstance(data, dict):
        if "@type" in data:
            yield data
        if "@graph" in data:
            for n in data["@graph"]:
                yield from collect_nodes(n)
    elif isinstance(data, list):
        for n in data:
            yield from collect_nodes(n)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--quiet":
        verbose = False
    else:
        verbose = True

    type_counter = Counter()
    field_counter = Counter()
    parse_failures = []
    faq_mismatches = []  # (rel_path, visible_count, jsonld_count)
    file_blocks = 0
    file_count = 0

    for p in ROOT.rglob("*.html"):
        if not p.is_file():
            continue
        if any(seg in p.relative_to(ROOT).parts for seg in SKIP):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        blocks = SCRIPT_RE.findall(text)
        if not blocks:
            continue
        file_count += 1

        # --- FAQPage vs visible FAQ consistency check -------------------------
        # Only pages that have at least one of (visible FAQ, FAQPage JSON-LD)
        # are checked. Pages with neither are out of scope — the site has
        # hundreds of blog posts / i18n pages without a FAQ section, and
        # reporting them as "mismatches" is noise.
        n_visible = len(DETAILS_RE.findall(text))
        n_jsonld = None
        for body in blocks:
            try:
                _d = json.loads(body)
            except json.JSONDecodeError:
                continue
            if isinstance(_d, dict) and _d.get("@type") == "FAQPage":
                n_jsonld = len(_d.get("mainEntity", []) or [])
                break
        if n_visible > 0 or n_jsonld is not None:
            # Mismatch: counts differ. Triggers when one side has FAQ and
            # the other doesn't, or when both have FAQ but the count differs.
            if n_visible != n_jsonld:
                faq_mismatches.append(
                    (p.relative_to(ROOT), n_visible, n_jsonld)
                )
        # ---------------------------------------------------------------------

        for body in blocks:
            file_blocks += 1
            try:
                data = json.loads(body)
            except json.JSONDecodeError as e:
                parse_failures.append((p, str(e)))
                continue
            for node in collect_nodes(data):
                t = node.get("@type")
                if isinstance(t, str):
                    type_counter[t] += 1
                elif isinstance(t, list):
                    for x in t:
                        type_counter[x] += 1
                # track a few key fields
                if "speakable" in node:
                    field_counter["speakable"] += 1
                if "articleSection" in node:
                    field_counter["articleSection"] += 1
                if "knowsLanguage" in node:
                    field_counter["knowsLanguage"] += 1
                if node.get("founder"):
                    field_counter["founder"] += 1
                if node.get("@type") == "FAQPage":
                    for q in node.get("mainEntity", []) or []:
                        if "upvoteCount" in q:
                            field_counter["faq.question.upvoteCount"] += 1
                        if "author" in q:
                            field_counter["faq.question.author"] += 1
                        ans = q.get("acceptedAnswer", {}) or {}
                        if "url" in ans:
                            field_counter["faq.answer.url"] += 1
                        if "upvoteCount" in ans:
                            field_counter["faq.answer.upvoteCount"] += 1
                if node.get("@type") == "Review":
                    field_counter["Review"] += 1
                if node.get("@type") == "CreativeWork":
                    field_counter["CreativeWork"] += 1
                if node.get("@type") == "VideoObject":
                    field_counter["VideoObject"] += 1
                if node.get("@type") == "LearningResource":
                    field_counter["LearningResource"] += 1
                if node.get("@type") == "WebApplication":
                    field_counter["WebApplication"] += 1
                if node.get("@type") == "AboutPage":
                    field_counter["AboutPage"] += 1
                if node.get("@type") == "ItemList":
                    field_counter["ItemList"] += 1

    print(f"=== Site-wide schema check ===")
    print(f"HTML files with JSON-LD: {file_count}")
    print(f"Total JSON-LD blocks:    {file_blocks}")
    print(f"JSON parse failures:     {len(parse_failures)}")
    if parse_failures:
        for p, err in parse_failures[:10]:
            print(f"  - {p.relative_to(ROOT)}: {err}")
    print(f"FAQ consistency:         {len(faq_mismatches)} mismatches")
    if faq_mismatches:
        # One row per offending page. visible=number of
        # <details class="faq-item">, jsonld=mainEntity size of the
        # FAQPage block. Re-run scripts/sync-faq-schema.py --apply to fix.
        for rel, vis, jl in faq_mismatches:
            print(f"  - {rel}: visible={vis}, json-ld={jl}  "
                  f"(run scripts/sync-faq-schema.py --apply)")
    print()
    print("=== @type distribution (top 30) ===")
    for t, n in type_counter.most_common(30):
        print(f"  {n:5d}  {t}")
    print()
    print("=== Key field coverage ===")
    for k in sorted(field_counter):
        print(f"  {n if (n := field_counter[k]) else 0:5d}  {k}")
    print()
    print("=== Key page spot check ===")
    for f in KEY_PAGES:
        path = ROOT / f
        if not path.exists():
            print(f"  - {f}: NOT FOUND")
            continue
        text = path.read_text(encoding="utf-8")
        blocks = SCRIPT_RE.findall(text)
        types = []
        for b in blocks:
            try:
                d = json.loads(b)
            except json.JSONDecodeError:
                types.append("PARSE-ERR")
                continue
            for n in collect_nodes(d):
                t = n.get("@type")
                if isinstance(t, str):
                    types.append(t)
                elif isinstance(t, list):
                    types.extend(t)
        uniq = sorted(set(types))
        print(f"  {f}: {len(blocks)} blocks, {len(uniq)} unique @types")
        if verbose:
            for t in uniq:
                print(f"      - {t}")

    # Treat FAQ mismatches and JSON parse failures as fatal so this script
    # can gate deploys. Pass --quiet in CI if you only want the summary.
    if parse_failures or faq_mismatches:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
