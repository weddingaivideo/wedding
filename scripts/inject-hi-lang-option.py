#!/usr/bin/env python3
"""
One-off: add <option value="hi">HI</option> to the language switcher in
every HTML file that has one.

Idempotent: skips files that already have a 'hi' option.

Run from repo root:
    python scripts/inject-hi-lang-option.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDE = {"internal-tools", "qa", "private", "admin", "functions", "__pycache__", "node_modules", ".git"}

# Match: <option value="th">TH</option> (or any of the existing langs)
# and insert <option value="hi">HI</option> after the last one.
# We anchor on the </select> closing tag — there should be one switcher per file.
LANG_OPTION_RE = re.compile(
    r'(<option\s+value="(?:en|zh|es|fr|de|pt|ja|ru|ar|th)"[^>]*>[^<]*</option>\s*)+(?=</select>)',
    re.IGNORECASE,
)
HI_OPTION = '<option value="hi">HI</option>\n                    '


def main() -> int:
    changed = 0
    skipped = 0
    affected = []
    for p in ROOT.rglob("*.html"):
        if set(p.parts) & EXCLUDE:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "wa-lang-select" not in text:
            continue
        # Idempotency: already has hi option
        if re.search(r'<option\s+value="hi"', text, re.IGNORECASE):
            skipped += 1
            continue
        new_text, n = LANG_OPTION_RE.subn(lambda m: m.group(0) + "\n                    " + HI_OPTION.strip(), text, count=1)
        if n == 0:
            # No lang block matched — skip with warning
            print(f"  [WARN] no option block matched: {p.relative_to(ROOT)}")
            continue
        if new_text != text:
            p.write_text(new_text, encoding="utf-8")
            changed += 1
            affected.append(p.relative_to(ROOT))
    print(f"Changed: {changed} files")
    print(f"Skipped (already had hi): {skipped}")
    if changed:
        print("Sample files (first 5):")
        for f in affected[:5]:
            print(f"  {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
