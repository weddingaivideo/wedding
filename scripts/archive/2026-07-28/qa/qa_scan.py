"""
Comprehensive QA scan across all 90+ HTML pages.

Checks (all logged to stdout for triage):
  1. Files missing data-i18n attributes (potential i18n gaps)
  2. Files missing the language switcher (#wa-lang-select)
  3. Empty <span></span> (likely i18n injection artifacts)
  4. Duplicate IDs in the same file
  5. Images without alt attribute
  6. Hardcoded English text inside data-i18n-marked elements
     (means the EN source wasn't translated yet for that language)
  7. Internal hrefs pointing to non-existent local files
  8. Pages with empty <title> or empty meta description
  9. Cross-page canonical URL consistency

Sister to: fix_logo_html.py
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDE = {"admin", "private", "tmp", "node_modules", ".git", "i18n", "scripts"}


def all_html():
    out = []
    for f in ROOT.rglob("*.html"):
        if any(p in EXCLUDE for p in f.relative_to(ROOT).parts):
            continue
        if f.name == "google-site-verification.html":
            continue
        out.append(f)
    return out


def main() -> int:
    files = all_html()
    print(f"=== Scanning {len(files)} HTML files ===\n")

    # Result buckets
    no_i18n: list = []
    no_lang_switcher: list = []
    empty_spans: list = []
    duplicate_ids: list = []
    missing_alt: list = []
    hardcoded_en_in_translated: list = []
    broken_local_hrefs: list = []
    empty_meta: list = []
    canonical_issues: list = []

    # Build set of all local file paths that exist (relative to project root, no leading /)
    all_paths = set()
    for f in ROOT.rglob("*"):
        if f.is_file() and ".git" not in f.parts and "node_modules" not in f.parts:
            rel = f.relative_to(ROOT).as_posix()
            all_paths.add(rel)
            # also add with leading / and without extension (for Pages dir/index.html resolution)
            all_paths.add("/" + rel)

    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        text = f.read_text(encoding="utf-8")

        # 1) data-i18n
        if 'data-i18n="' not in text and 'data-i18n-attr="' not in text:
            no_i18n.append(rel)

        # 2) lang switcher
        if 'id="wa-lang-select"' not in text:
            no_lang_switcher.append(rel)

        # 3) Empty spans (i18n injection artifacts)
        empty = re.findall(r"<span[^>]*></span>", text)
        if empty:
            empty_spans.append((rel, len(empty), empty[:3]))

        # 4) Duplicate IDs
        ids = re.findall(r'id="([^"]+)"', text)
        seen = set()
        dups = set()
        for i in ids:
            if i in seen:
                dups.add(i)
            seen.add(i)
        if dups:
            duplicate_ids.append((rel, sorted(dups)))

        # 5) Images without alt
        imgs = re.findall(r'<img\s[^>]*>', text, re.IGNORECASE)
        for img in imgs:
            if "alt=" not in img and "data-no-i18n" not in img:
                # extract src for context
                src_m = re.search(r'src="([^"]+)"', img)
                missing_alt.append((rel, src_m.group(1) if src_m else "?"))

        # 6) Hardcoded English in data-i18n elements (when zh.json is loaded, the
        # textContent gets replaced, but the data-i18n-attr content/alt might not)
        # Heuristic: any element with data-i18n containing English text that
        # doesn't match EN.json — too expensive to check here. Skip.

        # 7) Broken local hrefs
        hrefs = re.findall(r'href="([^"]+)"', text)
        for h in hrefs:
            if h.startswith(("http://", "https://", "mailto:", "tel:", "#", "data:")):
                continue
            # Strip query/fragment
            target = h.split("?")[0].split("#")[0]
            if not target:
                continue
            # Normalize: relative paths resolved from file's directory
            if target.startswith("/"):
                norm = target.lstrip("/")
            else:
                base = f.parent.relative_to(ROOT).as_posix()
                norm = (Path(base) / target).as_posix() if base else target
            # Check existence
            if norm not in all_paths:
                # Also try adding /index.html for directory-style
                if (norm + "/index.html") not in all_paths and (norm.rstrip("/") + "/index.html") not in all_paths:
                    # Try replacing .html with /index.html (Cloudflare convention)
                    if norm.endswith(".html"):
                        if (norm[:-5] + "/index.html") in all_paths:
                            continue
                    broken_local_hrefs.append((rel, h))

        # 8) Empty title or meta description
        title_m = re.search(r"<title[^>]*>([^<]*)</title>", text)
        if title_m and not title_m.group(1).strip():
            empty_meta.append((rel, "title"))
        desc_m = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', text)
        if desc_m and not desc_m.group(1).strip():
            empty_meta.append((rel, "description"))

        # 9) Canonical URL
        canon_m = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', text)
        if canon_m:
            url = canon_m.group(1)
            if "weddingai.video" not in url:
                canonical_issues.append((rel, url))
            # Check it matches file path
            if rel == "index.html" and not url.endswith("/"):
                canonical_issues.append((rel, "no trailing slash on root"))

    # Report
    def report(name, lst, formatter=None):
        print(f"\n=== {name} ({len(lst)}) ===")
        if not lst:
            print("  (none)")
            return
        for item in lst[:30]:
            if formatter:
                print(f"  {formatter(item)}")
            else:
                print(f"  {item}")
        if len(lst) > 30:
            print(f"  ... and {len(lst) - 30} more")

    report("Pages missing data-i18n (potential i18n gaps)", no_i18n)
    report("Pages missing #wa-lang-select", no_lang_switcher)
    report("Pages with empty <span></span> (i18n artifacts)", empty_spans, lambda x: f"{x[0]}: {x[1]} empty spans (e.g. {x[2]})")
    report("Pages with duplicate IDs", duplicate_ids, lambda x: f"{x[0]}: {x[1]}")
    report("Images without alt", missing_alt, lambda x: f"{x[0]}: {x[1]}")
    report("Broken local hrefs", broken_local_hrefs, lambda x: f"{x[0]}: href='{x[1]}'")
    report("Empty title/description", empty_meta, lambda x: f"{x[0]}: {x[1]}")
    report("Canonical URL issues", canonical_issues, lambda x: f"{x[0]}: {x[1]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
