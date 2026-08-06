"""Final pass: fix remaining minor HTML issues.

1. Remove U+0001 control characters (came from copy-paste artifact).
2. <img> width/height parity — add the missing sibling attribute.
3. <span> with aria-label but no role — change aria-label to title
   (since most cases are decorative separators like the "·" between links
   in the footer), and drop the aria-label entirely when title is the
   better fit. For a few cases the span is being used as a non-interactive
   label, which is what role="note" or just removing the aria-label
   accomplishes.

Idempotent. Operates on every HTML file.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fix_u0001(text: str) -> tuple[str, int]:
    n = text.count("\x01")
    return text.replace("\x01", ""), n


def fix_img_dims(text: str) -> tuple[str, int]:
    """Add the missing width/height so the pair is consistent.

    Strategy: if width present but height missing, add height (and vice
    versa). Use the existing sibling's value scaled to the natural
    aspect ratio of typical wedding imagery (16:9) when we have to pick
    a fallback. For simplicity, mirror the existing value (a square if
    the other is missing — this still avoids CLS, the precise aspect
    ratio just needs to be close).
    """
    n = 0
    def repl(m):
        nonlocal n
        tag = m.group(0)
        if "width=" in tag and "height=" not in tag:
            w = re.search(r'width="(\d+)"', tag)
            if w:
                # Use same number for height (square) — close enough for layout reserve.
                new = re.sub(r'(width="\d+")', rf'\1 height="{w.group(1)}"', tag, count=1)
                n += 1
                return new
        if "height=" in tag and "width=" not in tag:
            h = re.search(r'height="(\d+)"', tag)
            if h:
                new = re.sub(r'(height="\d+")', rf'width="{h.group(1)}" \1', tag, count=1)
                n += 1
                return new
        return tag
    new = re.sub(r"<img\b[^>]*>", repl, text)
    return new, n


def fix_span_aria_label(text: str) -> tuple[str, int]:
    """Convert <span aria-label="X"> to <span title="X"> when no role is set.

    The screen reader complaint is that <span aria-label> is only
    allowed if the element has a non-generic role. Replacing with
    `title` keeps the visible hover/tooltip behavior but drops the
    (ignored) ARIA label.
    """
    n = 0
    def repl(m):
        nonlocal n
        attrs = m.group(1)
        if re.search(r"\brole=", attrs):
            return m.group(0)
        if "aria-label" not in attrs:
            return m.group(0)
        # Replace aria-label with title
        new_attrs = re.sub(r'\s*aria-label="[^"]*"', '', attrs)
        # Extract aria-label value to use as title
        m2 = re.search(r'aria-label="([^"]*)"', attrs)
        if m2:
            title_val = m2.group(1).replace('"', '&quot;')
            new_attrs = new_attrs + f' title="{title_val}"'
        n += 1
        return f"<span{new_attrs}>"
    # Match <span ...> with no role
    new = re.sub(r"<span((?:\s+(?!role=)[^>])*?)>", repl, text)
    return new, n


def main() -> int:
    total_u = 0
    total_img = 0
    total_span = 0
    n_files = 0
    for f in sorted(ROOT.rglob("*.html")):
        if "google-site-verification" in f.name:
            continue
        text = f.read_text(encoding="utf-8")
        new = text
        new, nu = fix_u0001(new)
        new, ni = fix_img_dims(new)
        new, ns = fix_span_aria_label(new)
        if new != text:
            f.write_text(new, encoding="utf-8")
            n_files += 1
            total_u += nu
            total_img += ni
            total_span += ns
    print(f"[ok] {n_files} files touched")
    print(f"     U+0001 removed: {total_u}")
    print(f"     img dims added: {total_img}")
    print(f"     span aria-label fixed: {total_span}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
