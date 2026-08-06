#!/usr/bin/env python3
"""
Fix duplicate h1/h2 heading in blog posts.

The bug: 15 second-batch blog posts render the article title twice:
  - <h1> in the page hero section
  - <h2> at the very top of the article body (same text)

Fix: drop the body-level <h2> line if its text equals the <h1> text.

Idempotent: re-running on already-fixed files is a no-op (regex won't match).

Usage:
    python scripts/fix-dup-h1-h2.py
    python scripts/fix-dup-h1-h2.py --slug cartoon-wedding-video   # single file
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG_DIR = ROOT / "blog"

# The 15 affected slugs (second batch with bug).
DUP_SLUGS = [
    "cartoon-wedding-video",
    "digitize-parents-wedding-video",
    "fix-shaky-wedding-video",
    "raw-wedding-footage-ideas",
    "restore-old-wedding-photos",
    "same-sex-wedding-video",
    "spring-wedding-video-trends",
    "unique-wedding-video-ideas",
    "wedding-memes",
    "wedding-photo-slideshow",
    "wedding-video-audio-fix",
    "wedding-video-for-parents",
    "wedding-video-music",
    "wedding-video-timeline",
    "weddingai-success-stories",
]

# Match a complete <h2 ...>TEXT</h2> line (captures the whole line incl. the tag).
# Allows attributes (data-i18n, etc.) between <h2 and >.
H2_LINE_RE = re.compile(
    r'^[ \t]*<h2\b[^>]*>.*?</h2>[ \t]*(?:\r\n|\r|\n)',
    re.IGNORECASE | re.DOTALL | re.MULTILINE,
)
H1_TEXT_RE = re.compile(r'<h1\b[^>]*>(.*?)</h1>', re.IGNORECASE | re.DOTALL)
H2_TEXT_RE = re.compile(r'<h2\b[^>]*>(.*?)</h2>', re.IGNORECASE | re.DOTALL)
TAG_STRIP_RE = re.compile(r'<[^>]+>')


def normalize_text(s: str) -> str:
    """Strip HTML tags + collapse whitespace + trim. Used for h1==h2 text comparison."""
    s = TAG_STRIP_RE.sub('', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def fix_file(path: Path) -> str:
    """
    Returns one of: "FIXED", "SKIPPED_NOT_DUP", "SKIPPED_NO_H1", "ALREADY_FIXED", "ERROR: ..."
    """
    if not path.exists():
        return "ERROR: not found"
    raw = path.read_bytes()
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        return "ERROR: not utf-8"

    h1_match = H1_TEXT_RE.search(text)
    if not h1_match:
        return "SKIPPED_NO_H1"
    h1_text = normalize_text(h1_match.group(1))

    # Find the first <h2 ...>TEXT</h2> line and check if its text matches h1.
    h2_match = H2_LINE_RE.search(text)
    if not h2_match:
        return "ALREADY_FIXED"

    first_h2_inner = H2_TEXT_RE.match(h2_match.group(0))
    if not first_h2_inner:
        return "ERROR: h2 regex broken"
    h2_text = normalize_text(first_h2_inner.group(1))

    if h2_text != h1_text:
        return "SKIPPED_NOT_DUP"

    # Remove the matched line (it's already the full line with line-ending).
    new_text = text[:h2_match.start()] + text[h2_match.end():]
    new_bytes = new_text.encode('utf-8')
    if new_bytes == raw:
        return "ERROR: no-op write"
    path.write_bytes(new_bytes)
    return "FIXED"


def main(argv: list[str]) -> int:
    # Optional --slug <name> for single-file mode.
    only_slug = None
    if "--slug" in argv:
        idx = argv.index("--slug")
        if idx + 1 >= len(argv):
            print("ERROR: --slug requires a value", file=sys.stderr)
            return 2
        only_slug = argv[idx + 1]

    targets = [only_slug] if only_slug else DUP_SLUGS

    fixed = 0
    skipped_already = 0
    skipped_not_dup = 0
    skipped_no_h1 = 0
    errors = 0

    for slug in targets:
        path = BLOG_DIR / slug / "index.html"
        result = fix_file(path)
        if result == "FIXED":
            fixed += 1
            print(f"FIXED    {slug}")
        elif result == "ALREADY_FIXED":
            skipped_already += 1
            print(f"OK       {slug} (already fixed)")
        elif result == "SKIPPED_NOT_DUP":
            skipped_not_dup += 1
            print(f"SKIP     {slug} (first h2 no longer equals h1)")
        elif result == "SKIPPED_NO_H1":
            skipped_no_h1 += 1
            print(f"SKIP     {slug} (no h1 found)")
        else:
            errors += 1
            print(f"ERROR    {slug}: {result}")

    print()
    print(f"Summary: fixed={fixed} already={skipped_already} not_dup={skipped_not_dup} no_h1={skipped_no_h1} errors={errors}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
