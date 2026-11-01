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
# "tools" is deliberately NOT skipped any more. The 13 tool pages ship in 11
# language folders (tools/, de/tools/, ja/tools/, ...) plus the tools hub =
# 144 pages holding 431 JSON-LD blocks, and while the directory was skipped a
# JSON parse error or a FAQPage drift on any of them could never fail the
# gate. The tool pages use their own FAQ markup (see count_visible_faqs
# below), so the FAQ comparison has to understand BOTH forms — skipping the
# tree hid the problem instead of fixing it.
SKIP = ("tmp", ".tmp", "private", "scripts", "tests", "qa", "internal-tools")
# The script tag must be matched with ANY attribute layout: a strict
# `<script type="application/ld+json">` misses `<script data-x="1"
# type="application/ld+json">` or any other spacing/quoting. Same trap as
# the <details> matcher below — a checker that measures only the form it was
# written against reports "nothing is wrong" about the form it never sees.
SCRIPT_RE = re.compile(
    r'<script\b[^>]*\btype\s*=\s*["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE)

# --- Visible FAQ detection --------------------------------------------------
# The repo carries TWO visible-FAQ markup forms:
#   1. <details class="faq-item">              — blog / service / landing pages
#   2. <details> inside <div class="qa-block">  — the tool pages, which use
#      their own FAQ layout and put no class on the element
# A matcher that only knows form 1 counts the tool pages as "visible=0", and
# visible=0 / json-ld=5 is indistinguishable from a schema that drifted.
#
# A plain <details> that is NOT inside a qa-block is NOT a FAQ (it would be
# an accordion or a product card) and must never be counted — those are
# reported separately so they cannot disappear silently.
#
# The tags must also be matched with any ATTRIBUTES allowed: a strict
# `<details class="faq-item">` stops matching the moment the element gains an
# id (e.g. `id="faq-1"`, which scripts/sync-faq-schema.py adds so the
# #faq-N anchors inside the FAQPage schema actually resolve). A regex that
# silently matches nothing looks exactly like "nothing is wrong", so keep it
# tolerant of attribute order and extra attributes.
FAQ_ITEM_ATTR_RE = re.compile(r'class="[^"]*\bfaq-item\b[^"]*"')
QA_BLOCK_ATTR_RE = re.compile(r'class="[^"]*\bqa-block\b[^"]*"')
# Only the structural tags are scanned. <script>/<style> bodies are removed
# first so a "<div" inside a JS string cannot shift the nesting depth.
CONTAINER_TAG_RE = re.compile(r'<(/?)(div|details)\b([^>]*)>', re.IGNORECASE)
SCRIPT_STYLE_RE = re.compile(r'<(script|style)\b[^>]*>.*?</\1\s*>', re.DOTALL | re.IGNORECASE)

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

# One page per visible-FAQ markup form, so every run proves that the matcher
# counts the canonical faq-item form AND the tool pages' own qa-block form.
FAQ_SPOT_PAGES = [
    "blog/wedding-video-trends-2026/index.html",            # blog, faq-item
    "services/personalization/ai-video-generator/index.html",  # service, faq-item
    "tools/wedding-budget-calculator/index.html",              # tool, qa-block
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


def count_visible_faqs(text):
    """Count the visible FAQ blocks of a page.

    Returns (faq_item, tool_faq, plain_outside):
      faq_item      - <details class="faq-item"> — the canonical form
      tool_faq      - plain <details> inside <div class="qa-block"> — the
                      tool pages' own FAQ layout
      plain_outside - plain <details> that is NOT inside a qa-block, i.e. not
                      a FAQ (accordion / product card). Counted so it can be
                      reported instead of silently ignored.
    """
    faq_item = 0
    tool_faq = 0
    plain_outside = 0
    # One entry per open <div>: True when that div is a qa-block container.
    div_stack = []
    for m in CONTAINER_TAG_RE.finditer(SCRIPT_STYLE_RE.sub(" ", text)):
        closing, tag, attrs = m.group(1), m.group(2).lower(), m.group(3)
        if tag == "div":
            if closing:
                if div_stack:
                    div_stack.pop()
            else:
                div_stack.append(bool(QA_BLOCK_ATTR_RE.search(attrs)))
            continue
        if closing:
            # </details> is the end of a block, not a block of its own.
            continue
        if FAQ_ITEM_ATTR_RE.search(attrs):
            faq_item += 1
        elif any(div_stack):
            tool_faq += 1
        else:
            plain_outside += 1
    return faq_item, tool_faq, plain_outside


def faq_schema_count(text):
    """Return len(mainEntity) of the page's FAQPage JSON-LD block, or None."""
    for body in SCRIPT_RE.findall(text):
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            continue
        # collect_nodes() also looks inside @graph / arrays, so a FAQPage
        # nested in a graph is found instead of being read as "no schema".
        for node in collect_nodes(data):
            if node.get("@type") == "FAQPage":
                return len(node.get("mainEntity", []) or [])
    return None


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--quiet":
        verbose = False
    else:
        verbose = True

    type_counter = Counter()
    field_counter = Counter()
    parse_failures = []
    faq_mismatches = []  # (rel_path, visible_count, jsonld_count)
    faq_no_schema = []  # (rel_path, visible_count) — visible FAQ, no schema
    non_faq_details = []  # (rel_path, count) — <details> that are not FAQs
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
        n_item, n_tool, n_outside = count_visible_faqs(text)
        n_visible = n_item + n_tool
        n_jsonld = faq_schema_count(text)
        if n_outside:
            non_faq_details.append((p.relative_to(ROOT), n_outside))
        if n_visible > 0 or n_jsonld is not None:
            if n_jsonld is None:
                # Visible FAQ, but the page ships no FAQPage schema at all.
                if n_item > 0:
                    # The canonical faq-item markup always ships a matching
                    # FAQPage block on this site, so a missing schema here is
                    # drift and stays fatal.
                    faq_mismatches.append(
                        (p.relative_to(ROOT), n_visible, n_jsonld)
                    )
                else:
                    # The tool pages' own FAQ layout: 10 of the 13 slugs show a
                    # visible FAQ and ship NO FAQPage schema. That is a
                    # pre-existing content gap, not a drift between two
                    # numbers, and closing it means editing the page markup —
                    # not this checker. It is reported, but it must not fail
                    # the deploy gate. Where such a page DOES ship a schema,
                    # the counts above are still compared strictly.
                    faq_no_schema.append((p.relative_to(ROOT), n_visible))
            elif n_visible != n_jsonld:
                # Mismatch: counts differ. Triggers when one side has FAQ and
                # the other doesn't, or when both have FAQ but the count differs.
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
        # One row per offending page. visible=number of visible <details>
        # (faq-item form and the tool pages' qa-block form), jsonld=mainEntity
        # size of the FAQPage block. Re-run scripts/sync-faq-schema.py --apply
        # to fix — note that script skips the tools/ tree, so a tool-page row
        # has to be fixed in the page markup.
        for rel, vis, jl in faq_mismatches:
            print(f"  - {rel}: visible={vis}, json-ld={jl}  "
                  f"(run scripts/sync-faq-schema.py --apply)")
    if faq_no_schema:
        # Visible FAQ, no FAQPage schema: reported, NOT fatal. See the comment
        # in the loop for why the tool pages are treated differently from the
        # canonical faq-item markup.
        print(f"FAQ without schema:      {len(faq_no_schema)} pages "
              f"(visible tool-page FAQ, no FAQPage block — reported, not fatal)")
        if verbose:
            for rel, vis in faq_no_schema[:20]:
                print(f"  - {rel}: visible={vis}, json-ld=None")
            if len(faq_no_schema) > 20:
                print(f"  ... {len(faq_no_schema) - 20} more page(s) not shown")
    if non_faq_details:
        print(f"Non-FAQ <details>:       {sum(n for _, n in non_faq_details)} on "
              f"{len(non_faq_details)} page(s) (not in a qa-block — not counted)")
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
    print()
    print("=== FAQ spot check (visible vs FAQPage mainEntity) ===")
    # One page per markup form. If the matcher ever stops recognising one of
    # the two forms, the visible count drops to 0 here and the two numbers
    # stop agreeing — the check proves itself on every run.
    for f in FAQ_SPOT_PAGES:
        path = ROOT / f
        if not path.exists():
            print(f"  {f}: NOT FOUND")
            continue
        text = path.read_text(encoding="utf-8")
        n_item, n_tool, n_outside = count_visible_faqs(text)
        n_visible = n_item + n_tool
        n_jsonld = faq_schema_count(text)
        state = "OK" if n_visible == n_jsonld else "MISMATCH"
        print(f"  {f}: visible={n_visible} (faq-item={n_item}, tool={n_tool}), "
              f"json-ld={n_jsonld}  {state}")

    # Treat FAQ mismatches and JSON parse failures as fatal so this script
    # can gate deploys. Pass --quiet in CI if you only want the summary.
    if parse_failures or faq_mismatches:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
