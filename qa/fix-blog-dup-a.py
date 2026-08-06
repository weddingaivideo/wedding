"""
Find and fix duplicate <a> patterns across the site.

Pattern: <a href="X"><a href="X" data-i18n="key">TEXT</a>
Fix:     <a href="X" data-i18n="key">TEXT</a>

This bug was introduced by an old version of i18n_inject.py (now archived).
The injector should have REPLACED the original <a> open tag with one that
has data-i18n, but the buggy version left the original AND inserted a new
<a> with data-i18n before the text.

After fix, also check for the related bug:
  Pattern: <a href="X">...<a href="X" data-i18n="key">TEXT</a>  (any inner content)
  Or:      <a><a ...>TEXT</a>  (open without attrs)
  Or:      </p> orphan closes
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
# Match: <a href="X"><a href="X" data-i18n="Y">TEXT</a>
# Or:     <a href="X"><a href="X" data-i18n="Y" ...attrs>TEXT</a>
DUP_A_RE = re.compile(
    r'<a\s+href="([^"]+)"\s*>'                    # outer <a href="X">
    r'<a\s+href="\1"\s+data-i18n="[^"]+"'          # inner <a href="X" data-i18n="...">
    r'([^>]*)'                                      # any extra attrs on inner
    r'>'                                            # close of inner
    r'([^<]*)'                                      # text content
    r'</a>',                                        # close of inner
    re.DOTALL,
)

# Also handle: <a><a href="..." data-i18n="...">TEXT</a>
DUP_A_NO_HREF_RE = re.compile(
    r'<a\s*>'
    r'<a\s+href="[^"]+"\s+data-i18n="[^"]+"\s*([^>]*)>'
    r'([^<]*)'
    r'</a>',
    re.DOTALL,
)

def fix_content(content: str) -> tuple[str, int, int]:
    n1 = 0
    n2 = 0
    def repl1(m):
        nonlocal n1
        n1 += 1
        href = m.group(1)
        extra_attrs = m.group(2).strip()
        text = m.group(3)
        attr_str = f' {extra_attrs}' if extra_attrs else ''
        return f'<a href="{href}" data-i18n-restored="1"{attr_str}>{text}</a>'
    def repl2(m):
        nonlocal n2
        n2 += 1
        extra_attrs = m.group(1).strip()
        text = m.group(2)
        attr_str = f' {extra_attrs}' if extra_attrs else ''
        # Original outer <a> had no href — use placeholder
        return f'<a href="#" data-i18n-restored="1"{attr_str}>{text}</a>'
    new = DUP_A_RE.sub(repl1, content)
    new = DUP_A_NO_HREF_RE.sub(repl2, new)
    return new, n1, n2

print("Scanning for duplicate <a> patterns...")
print()

total_files = 0
total_fixes = 0
for html_file in sorted(ROOT.rglob("*.html")):
    rel = html_file.relative_to(ROOT)
    parts = rel.parts
    if 'qa' in parts or 'scripts' in parts or 'tmp' in parts or 'archive' in parts:
        continue
    content = html_file.read_text(encoding="utf-8")
    if '<a href="' not in content:
        continue
    new_content, n1, n2 = fix_content(content)
    total = n1 + n2
    if total > 0:
        html_file.write_text(new_content, encoding="utf-8")
        total_files += 1
        total_fixes += total
        print(f"  {rel}: fixed {total} ({n1} href-match, {n2} no-href)")

print(f"\nTotal: {total_fixes} duplicate <a> patterns fixed in {total_files} file(s)")
