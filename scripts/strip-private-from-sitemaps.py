#!/usr/bin/env python3
"""
Remove the bogus /private/architecture/ entries from the language sitemaps.

Why this exists
---------------
`private/` is a LOCAL TOOLING directory in this repo (audit scripts, progress
files). It has never been a site page and there is no `private/architecture/`
html source anywhere. The 10 language sitemaps nevertheless carried a full
<url> block for it -- 1 <loc> plus 12 xhtml:link alternates each -- so every
language sitemap advertised a URL that:

  * returns HTTP 404 live (verified against the pinned edge IP), and
  * is explicitly listed in robots.txt as `Disallow: /private/`.

Submitting a robots-disallowed, 404 URL in a sitemap is the worst of both
worlds: it tells crawlers the page exists and then serves them nothing.

The edit is text-level on purpose: everything outside the removed block is
left byte-identical (UTF-8, no BOM, LF, same indentation, same namespaces).

What it removes
---------------
  1. the whole <url>...</url> block whose <loc> contains /private/architecture/
  2. any leftover <xhtml:link> line whose href points at /private/architecture/
     (defensive: today these only occur inside the removed block)

`sitemap-en.xml` and `sitemap.xml` never contained the entry and are not
touched.

Exit code 0 = all edits applied and verified.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Languages that carry a localized sitemap.  `en` is sitemap-en.xml and is
# excluded on purpose: it never had the entry.
LANGUAGES = ["ar", "de", "es", "fr", "hi", "ja", "pt", "ru", "th", "zh"]

MARKER = "/private/architecture/"

URL_BLOCK_RE = re.compile(r"[ \t]*<url>.*?</url>\n?", re.DOTALL)
XHTML_LINK_RE = re.compile(
    r"^[ \t]*<xhtml:link\b[^>]*" + re.escape(MARKER) + r"[^>]*/>[ \t]*\n?",
    re.MULTILINE,
)


def count_markers(text):
    return text.count(MARKER)


def main():
    failures = []
    print("=" * 90)
    print("STRIP /private/architecture/ FROM LANGUAGE SITEMAPS")
    print("=" * 90)

    for lang in LANGUAGES:
        name = f"sitemap-{lang}.xml"
        path = REPO / name
        if not path.exists():
            failures.append(f"{name}: missing")
            continue

        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            failures.append(f"{name}: unexpected UTF-8 BOM before edit")
            continue
        if b"\r\n" in raw:
            failures.append(f"{name}: CRLF line endings before edit")
            continue

        text = raw.decode("utf-8")
        before_markers = count_markers(text)
        before_urls = text.count("<url>")

        if before_markers == 0:
            print(f"  {name}: nothing to strip (0 markers) - skipped")
            continue

        # 1. drop the whole <url> block
        def _drop_block(m):
            return "" if MARKER in m.group(0) else m.group(0)

        new = URL_BLOCK_RE.sub(_drop_block, text)

        # 2. drop any surviving xhtml:link line that points at the path
        new = XHTML_LINK_RE.sub("", new)

        after_markers = count_markers(new)
        after_urls = new.count("<url>")

        if after_markers != 0:
            failures.append(f"{name}: {after_markers} marker(s) survived the edit")
            continue
        if after_urls >= before_urls:
            failures.append(
                f"{name}: <url> count did not shrink ({before_urls} -> {after_urls})")
            continue

        # byte-level invariants that must survive the rewrite
        out = new.encode("utf-8")
        if out.startswith(b"\xef\xbb\xbf"):
            failures.append(f"{name}: BOM introduced")
            continue
        if b"\r\n" in out:
            failures.append(f"{name}: CRLF introduced")
            continue
        if not out.endswith(b"\n"):
            failures.append(f"{name}: trailing newline lost")
            continue

        path.write_bytes(out)
        print(f"  {name}: {before_urls} -> {after_urls} <url>, "
              f"{before_markers} -> {after_markers} markers  OK")

    # final sweep: no sitemap may still mention the path
    print("\n--- final sweep ---")
    for path in sorted(REPO.glob("sitemap*.xml")):
        hits = count_markers(path.read_text(encoding="utf-8"))
        status = "clean" if hits == 0 else f"{hits} HITS"
        print(f"  {path.name:<20} {status}")
        if hits:
            failures.append(f"{path.name}: still references {MARKER}")

    print()
    if failures:
        print(f"RESULT: {len(failures)} FAILURE(S)")
        for f in failures:
            print("  - " + f)
        return 1
    print("RESULT: ALL SITEMAPS CLEAN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
