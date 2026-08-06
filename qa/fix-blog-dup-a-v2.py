"""
Fix duplicate <a> patterns - V2.

Pattern: <a href="X" [attrs]><a href="X" [attrs] data-i18n="..." [attrs]>TEXT</a>
Fix:     <a href="X" data-i18n="..." [attrs]>TEXT</a>

The V1 regex only matched exact href-only. V2 matches any attrs.
"""
import re
from pathlib import Path

ROOT = Path(r"C:/Users/qiaoshan/.openclaw/workspace/weddingai")

# Match: <a href="X" ...><a href="X" ... data-i18n="..." ...>TEXT</a>
# The key constraint: same href in both <a> openings
DUP_A_RE = re.compile(
    r'<a\s+href="([^"]+)"([^>]*)>'                  # outer <a href="X" ...>
    r'<a\s+href="\1"([^>]*\sdata-i18n="[^"]+"[^>]*)>'  # inner <a href="X" ... data-i18n>
    r'([^<]*)'                                       # text content
    r'</a>',
    re.DOTALL,
)

def fix_content(content: str) -> tuple[str, int]:
    n = 0
    def repl(m):
        nonlocal n
        href = m.group(1)
        outer_attrs = m.group(2).strip()
        inner_attrs = m.group(3).strip()
        text = m.group(4)
        n += 1
        # Build the new <a>: href + outer attrs + inner attrs (inner has data-i18n)
        # Strip any leading whitespace / duplicate spaces
        all_attrs = (outer_attrs + ' ' + inner_attrs).strip()
        # Collapse multiple spaces
        all_attrs = re.sub(r'\s+', ' ', all_attrs)
        return f'<a href="{href}" {all_attrs}>{text}</a>'
    new = DUP_A_RE.sub(repl, content)
    return new, n

print("Fixing duplicate <a> patterns (V2)...")
print()

total_files = 0
total_fixes = 0
for html_file in sorted(ROOT.rglob("*.html")):
    rel = html_file.relative_to(ROOT)
    parts = rel.parts
    if 'qa' in parts or 'scripts' in parts or 'tmp' in parts or 'archive' in parts:
        continue
    content = html_file.read_text(encoding="utf-8")
    new_content, n = fix_content(content)
    if n > 0:
        html_file.write_text(new_content, encoding="utf-8")
        total_files += 1
        total_fixes += n
        print(f"  {rel}: fixed {n}")

print(f"\nTotal: {total_fixes} duplicate <a> patterns fixed in {total_files} file(s)")
