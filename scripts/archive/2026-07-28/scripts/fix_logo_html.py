"""
Move the <picture> element INSIDE the <a class="logo"> tag.

Bug: picture is currently a sibling of the <a class="logo">, so the
.logo img CSS selector doesn't match. Image falls back to global
max-width:100% and renders at container width (~1200px) instead of
the intended 356px.

Sister to: CSS fix in styles.css (defensive in case any HTML is missed).

Idempotent: re-running is a no-op once the structure is correct.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDE_DIRS = {"admin", "private", "tmp", "node_modules", ".git", "i18n", "scripts"}


def fix_logo_in_html(text: str) -> tuple[str, int]:
    """Find picture-before-anchor pattern, move picture inside anchor.

    Returns (new_text, num_fixes).
    """
    pattern = re.compile(
        # group 1: the entire <picture>...</picture> element
        r"(<picture>"
        r"<source[^>]*logo-full[^>]*>"
        r"<source[^>]*logo-full[^>]*>"
        r"<img[^>]*logo-full[^>]*>"
        r"</picture>)"
        # then the opening <a class="logo"...>
        r"(<a\s+href=\"/\"\s+class=\"logo\"[^>]*>)"
        # then any whitespace/comments until the </a>
        r"([\s\S]*?)"
        r"(</a>)",
        flags=re.IGNORECASE,
    )
    count = 0

    def repl(m: re.Match) -> str:
        nonlocal count
        picture = m.group(1)
        a_open = m.group(2)
        # m.group(3) is whitespace/comments inside <a> — discard
        a_close = m.group(4)
        count += 1
        # Move <picture> inside the <a class="logo">, drop inner whitespace
        return f"{a_open}{picture}{a_close}"

    new_text = pattern.sub(repl, text)
    return new_text, count


def main() -> int:
    html_files = []
    for f in ROOT.rglob("*.html"):
        # Skip excluded dirs
        if any(part in EXCLUDE_DIRS for part in f.relative_to(ROOT).parts):
            continue
        html_files.append(f)

    total_fixed = 0
    files_changed = 0
    for f in html_files:
        text = f.read_text(encoding="utf-8")
        new_text, count = fix_logo_in_html(text)
        if count > 0 and new_text != text:
            f.write_text(new_text, encoding="utf-8")
            files_changed += 1
            total_fixed += count
            rel = f.relative_to(ROOT)
            print(f"  FIXED {count:2d}  {rel}")
    print(f"\n{total_fixed} logos moved into <a class=\"logo\"> across {files_changed} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
