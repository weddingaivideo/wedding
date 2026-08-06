"""Replace raw double quotes inside alt= attributes with single quotes.

Why: alt values generated from subheadings can contain literal `"` characters
(e.g. for subheading `2. The "Before You" Intro`). That breaks HTML parsing
and confuses audit scripts that match `alt="([^"]*)"`.

Approach: walk every <img> tag, find its alt= attribute value (greedy until
the next `"` that is followed by ` `, `/`, or `>`), and replace any inner `"`
with `'`. Idempotent (no `'` inside to begin with in our generated alts).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"

IMG_RE = re.compile(r"<img\b[^>]*>", re.DOTALL)
ALT_RE = re.compile(r'\balt="([^"]*)"(\s|/|>|$)')


def fix_img(img: str) -> tuple[str, int]:
    n = 0
    # Try the simple case first: alt="clean value"
    m = re.search(r'\balt="([^"]*)"(\s|/|>)', img)
    if m and '"' not in m.group(1):
        return img, 0
    # Otherwise: find alt=" and parse manually — the value is everything up
    # to the first `"` followed by an attr boundary.
    out = []
    i = 0
    while i < len(img):
        idx = img.find('alt="', i)
        if idx < 0:
            out.append(img[i:])
            break
        out.append(img[i:idx + 5])  # up through alt="
        j = idx + 5
        # read until `"` followed by space, /, or >
        val_chars = []
        while j < len(img):
            ch = img[j]
            if ch == '"':
                # Look ahead for terminator
                nxt = img[j + 1] if j + 1 < len(img) else ""
                if nxt in (" ", "/", ">", "\t", "\n", ""):
                    break
                else:
                    val_chars.append("'")
                    n += 1
                    j += 1
            else:
                val_chars.append(ch)
                j += 1
        out.append("".join(val_chars))
        # Append the closing quote
        if j < len(img):
            out.append('"')
            j += 1
        i = j
    return "".join(out), n


def main() -> int:
    n_files = 0
    n_total = 0
    targets = list(BLOG.glob("*/index.html")) + [BLOG / "index.html"]
    for html_path in targets:
        if not html_path.exists():
            continue
        text = html_path.read_text(encoding="utf-8")
        new_parts = []
        n_file = 0
        for m in IMG_RE.finditer(text):
            new_tag, n = fix_img(m.group(0))
            n_file += n
            new_parts.append(new_tag)
        if n_file == 0:
            continue
        # Replace each img tag
        out = []
        idx = 0
        for m, new_tag in zip(IMG_RE.finditer(text), new_parts):
            out.append(text[idx:m.start()])
            out.append(new_tag)
            idx = m.end()
        out.append(text[idx:])
        html_path.write_text("".join(out), encoding="utf-8")
        n_files += 1
        n_total += n_file
        print(f"[ok] {html_path.relative_to(ROOT)}: {n_file} alt-quote fixes")
    print(f"\nTotal: {n_total} alt-quote fixes in {n_files} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
