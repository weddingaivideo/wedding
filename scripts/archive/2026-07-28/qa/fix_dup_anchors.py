"""
Final round: remove duplicate adjacent <a> tags where the first has no
data-i18n and the second has data-i18n. The first <a> is the i18n_inject
artifact (had its closing '>' eaten when the new <a> was inserted).

Pattern:
  <a href="X" title="Y"><a href="X" title="Y" data-i18n="Z">Text</a>
becomes:
  <a href="X" title="Y" data-i18n="Z">Text</a>

This is the breadcrumb pattern in many pages.
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


def fix_duplicate_anchors(text: str) -> tuple[str, int]:
    n = 0

    # Pattern: <a href="X" title="Y"><a href="X" title="Y" data-i18n="Z">Text</a>
    # (first <a> has same href+title as second, but no data-i18n)
    pat1 = re.compile(
        r'<a\s+href="([^"]+)"\s+title="([^"]+)">'
        r'<a\s+href="\1"\s+title="\2"\s+data-i18n="([^"]+)">',
        flags=re.IGNORECASE,
    )
    def repl1(m: re.Match) -> str:
        return f'<a href="{m.group(1)}" title="{m.group(2)}" data-i18n="{m.group(3)}">'
    text, c = pat1.subn(repl1, text)
    n += c

    # Pattern: <a href="X" title="Y" class="C"><a href="X" title="Y" class="C" data-i18n="Z">
    pat2 = re.compile(
        r'<a\s+href="([^"]+)"\s+title="([^"]+)"\s+class="([^"]+)">'
        r'<a\s+href="\1"\s+title="\2"\s+class="\3"\s+data-i18n="([^"]+)">',
        flags=re.IGNORECASE,
    )
    def repl2(m: re.Match) -> str:
        return f'<a href="{m.group(1)}" title="{m.group(2)}" class="{m.group(3)}" data-i18n="{m.group(4)}">'
    text, c = pat2.subn(repl2, text)
    n += c

    return text, n


def main() -> int:
    files = all_html()
    print(f"=== Remove duplicate adjacent <a> tags ===\n")
    files_changed = 0
    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        text = f.read_text(encoding="utf-8")
        orig = text
        text, n = fix_duplicate_anchors(text)
        if text != orig:
            f.write_text(text, encoding="utf-8")
            files_changed += 1
            if n:
                print(f"  FIX  {rel}  -{n} dup <a>")
    print(f"\nFixed {files_changed} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
