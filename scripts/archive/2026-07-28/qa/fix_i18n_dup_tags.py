"""
Final cleanup: fix "<BLOCK<INLINE attrs data-i18n>..." patterns where
the BLOCK tag lost its ">" and the INLINE tag is the i18n-injected one.

Catches: <p<a, <li<a, <li<strong, <p<em, etc.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDE = {"admin", "private", "tmp", "node_modules", ".git", "i18n", "scripts", "qa"}


def all_html():
    out = []
    for f in ROOT.rglob("*.html"):
        if any(p in EXCLUDE for p in f.relative_to(ROOT).parts):
            continue
        if f.name == "google-site-verification.html":
            continue
        out.append(f)
    return out


def fix_cross_tag(text: str) -> tuple[str, int]:
    """Fix <BLOCK<INLINE ... data-i18n>... by dropping the broken BLOCK tag."""
    n = 0

    # Pattern: <BLOCK<INLINE_attrs>... where BLOCK is broken (no >).
    # The pattern matches a tag name, immediately followed by another tag
    # start (which means the first one's > was eaten and replaced with the
    # second tag's <). The second tag has data-i18n.
    # Drop the broken first tag (its content is empty since i18n_inject
    # moved the text into the second tag).
    pat = re.compile(
        r"<([a-z][a-z0-9]*)<([a-z][a-z0-9]*)(\s+[^>]*?data-i18n=\"[^\"]+\")>",
        flags=re.IGNORECASE,
    )
    text, c = pat.subn(r"<\2\3>", text)
    n += c

    return text, n


def main() -> int:
    files = all_html()
    print(f"=== Cross-tag duplicate cleanup ===\n")
    files_changed = 0
    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        text = f.read_text(encoding="utf-8")
        orig = text
        text, n = fix_cross_tag(text)
        if text != orig:
            f.write_text(text, encoding="utf-8")
            files_changed += 1
            if n:
                print(f"  FIX  {rel}  +{n}")
    print(f"\nFixed {files_changed} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
