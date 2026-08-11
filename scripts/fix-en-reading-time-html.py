#!/usr/bin/env python3
"""
fix-en-reading-time-html.py

The reading-time line in the EN blog HTML is hardcoded as
"11 min read · Updated YYYY-MM-DD" inside the <p> element with a
data-i18n attribute. applyDataI18n does NOT run for EN paths (it only
runs for /<lang>/ pages), so the visible EN text is the HTML body
itself, NOT the i18n dict value.

This script updates the HTML body to match the correct reading time
(calculated from actual word count) so the EN page shows the right
number.

It only touches the data-i18n element's INNER text (not the i18n dict
or other elements) so we don't break the i18n path.

Idempotent: detects existing "X min read" and updates only the minute
count.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

WPM = 250
LANGS_OF_INTEREST = ["en"]  # only EN — i18n paths use the dict value


def count_words(html: str) -> int:
    text = re.sub(r'<script\b[\s\S]*?</script>', ' ', html, flags=re.IGNORECASE)
    text = re.sub(r'<style\b[\s\S]*?</style>', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = (
        text.replace('&nbsp;', ' ').replace('&mdash;', '—')
            .replace('&ndash;', '–').replace('&rsquo;', "'")
            .replace('&lsquo;', "'").replace('&ldquo;', '"')
            .replace('&rdquo;', '"').replace('&hellip;', '…')
            .replace('&amp;', '&').replace('&quot;', '"')
    )
    return len([w for w in re.split(r'\s+', text) if w.strip()])


def reading_minutes(word_count: int, wpm: int = WPM) -> int:
    if word_count == 0:
        return 0
    return max(1, -(-word_count // wpm))


# Match the data-i18n element wrapping the reading-time line.
# The data-i18n key always contains "_min_read" in its name.
# We capture the current inner text and replace only the leading
# "<N> min read" part with the new value, preserving the rest
# (the "·" separator, the "Updated YYYY-MM-DD" part).
ELEMENT_RE = re.compile(
    r'(<p[^>]*data-i18n="blog\.[^"]*min_read[^"]*"[^>]*>)\s*\d+\s*min\s*read(\s*[^<]*)(</p>)',
    re.IGNORECASE,
)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=".")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"root not a directory: {root}", file=sys.stderr)
        return 2

    en_blog = root / "blog"
    if not en_blog.is_dir():
        print("no /blog dir", file=sys.stderr)
        return 2

    targets: list[Path] = []
    for d in en_blog.iterdir():
        if d.is_dir() and (d / "index.html").is_file():
            targets.append(d / "index.html")

    print(f"Processing {len(targets)} EN blog posts...")
    n_html = 0
    sample_lines: list[str] = []
    for html_path in sorted(targets):
        try:
            text = html_path.read_text(encoding="utf-8")
        except Exception:
            continue
        word_count = count_words(text)
        minutes = reading_minutes(word_count)
        new_text = ELEMENT_RE.sub(
            lambda m: f"{m.group(1)}{minutes} min read{m.group(2)}{m.group(3)}",
            text,
        )
        if new_text != text:
            if not args.dry_run:
                html_path.write_text(new_text, encoding="utf-8")
            n_html += 1
            if len(sample_lines) < 8:
                rel = html_path.relative_to(root)
                old = re.search(r'(\d+)\s*min\s*read', text)
                old_str = f"{old.group(1)} min read" if old else "?"
                sample_lines.append(
                    f"  {rel}: words={word_count}, {old_str} → {minutes} min read"
                )

    print("Sample updates:")
    for s in sample_lines:
        print(s)
    mode = "DRY RUN" if args.dry_run else "DONE"
    print(f"\n{mode}: EN HTML body updated={n_html}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
