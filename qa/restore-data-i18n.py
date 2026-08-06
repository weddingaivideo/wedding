"""
Restore data-i18n attributes that V1 fix accidentally dropped.

V1 fix replaced duplicate <a> patterns with:
  <a href="X" data-i18n-restored="1">TEXT</a>
losing the original data-i18n="key" attribute.

This script:
1. Finds <a ... data-i18n-restored="1">TEXT</a> patterns
2. Looks up TEXT in en.json to find the matching i18n key
3. Replaces with <a ... data-i18n="key">TEXT</a> (data-i18n-restored removed)
"""
import json
import re
from pathlib import Path

ROOT = Path(r"C:/Users/qiaoshan/.openclaw/workspace/weddingai")
EN_JSON = ROOT / "i18n" / "en.json"

# Load en.json as text-to-key lookup
en = json.loads(EN_JSON.read_text(encoding="utf-8"))
text_to_key = {v: k for k, v in en.items() if isinstance(v, str)}

# Find: <a ATTRS data-i18n-restored="1">TEXT</a>
# We need to extract ATTRS and TEXT.
RE = re.compile(
    r'<a\s+([^>]*?)data-i18n-restored="1"([^>]*)>'  # open with marker
    r'([^<]+)'                                          # text
    r'</a>',
    re.DOTALL,
)

def fix(content: str) -> tuple[str, int, int]:
    n_found = 0
    n_mapped = 0
    def repl(m):
        nonlocal n_found, n_mapped
        n_found += 1
        before = m.group(1).strip()
        after = m.group(2).strip()
        text = m.group(3).strip()
        key = text_to_key.get(text)
        if not key:
            # Try stripping the text or partial match
            for t, k in text_to_key.items():
                if t.strip() == text:
                    key = k
                    break
        if key:
            n_mapped += 1
            # Reconstruct: href + (other attrs from before) + data-i18n="key" + (after attrs) + >text</a>
            all_attrs = (before + ' ' + after).strip()
            all_attrs = re.sub(r'\s+', ' ', all_attrs)
            # data-i18n-restored is gone; add data-i18n if not present
            if 'data-i18n=' not in all_attrs:
                all_attrs = all_attrs + f' data-i18n="{key}"'
            return f'<a {all_attrs}>{text}</a>'
        else:
            # No key found — keep original (without marker)
            all_attrs = (before + ' ' + after).strip()
            all_attrs = re.sub(r'\s+', ' ', all_attrs)
            return f'<a {all_attrs}>{text}</a>'
    new = RE.sub(repl, content)
    return new, n_found, n_mapped

print("Restoring data-i18n attributes...")
print()
total_files = 0
total_fixed = 0
total_unmapped = 0
for html_file in sorted(ROOT.rglob("*.html")):
    rel = html_file.relative_to(ROOT)
    parts = rel.parts
    if 'qa' in parts or 'scripts' in parts or 'tmp' in parts or 'archive' in parts:
        continue
    content = html_file.read_text(encoding="utf-8")
    if 'data-i18n-restored=' not in content:
        continue
    new_content, n_found, n_mapped = fix(content)
    n_unmapped = n_found - n_mapped
    if n_found > 0:
        html_file.write_text(new_content, encoding="utf-8")
        total_files += 1
        total_fixed += n_mapped
        total_unmapped += n_unmapped
        marker = f"  ({n_unmapped} unmapped)" if n_unmapped else ""
        print(f"  {rel}: {n_mapped}/{n_found} mapped{marker}")

print(f"\nTotal: {total_fixed} mapped, {total_unmapped} unmapped, in {total_files} file(s)")
