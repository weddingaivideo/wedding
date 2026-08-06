"""Fix <span class="stars" aria-label="N stars"> — replace with role="img"
+ aria-label so the aria-label is actually exposed to screen readers,
or just drop aria-label since the visible text is sufficient.

We'll go with the role="img" approach because the star glyphs are
decorative and we want the count announced to screen readers.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Match: <span class="stars" aria-label="N stars">
PAT = re.compile(r'<span class="stars" aria-label="(\d+ stars)">')


def main() -> int:
    n = 0
    files = 0
    for f in sorted(ROOT.rglob("*.html")):
        if "google-site-verification" in f.name:
            continue
        text = f.read_text(encoding="utf-8")
        new, count = PAT.subn(r'<span class="stars" role="img" aria-label="\1">', text)
        if new != text:
            f.write_text(new, encoding="utf-8")
            n += count
            files += 1
    print(f"[ok] {files} files, {n} star spans fixed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
