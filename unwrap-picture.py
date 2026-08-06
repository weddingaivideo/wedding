"""
Unwrap nested <picture> elements created by the previous botched inject-srcset run.

The damage pattern looks like:
  <picture><source srcset="..." type="image/webp" sizes="...">
    <picture><source srcset="..." type="image/webp" sizes="...">
      <img src="..." srcset="..." sizes="...">
    </picture>
  </picture>

We collapse the inner <picture>...</picture> away, keeping the outer
<picture> and the <img> (which already has the right srcset).
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent

# Match an entire <picture>...</picture> block where the inner is a redundant wrap.
# Simpler approach: find any <picture> immediately after </source> (no whitespace)
# and remove the inner wrap.

# Find: </source> immediately followed by <picture>...</picture>
# Replace with: </source> (preserving the original)
# Then later, the second pass removes any remaining stray <picture>...<source>...</source></picture> if needed.

files = [p for p in ROOT.rglob("*.html") if p.name != "google-site-verification.html"]
n = 0
for f in files:
    text = f.read_text(encoding="utf-8")
    original = text

    # 1) Collapse `<source ...><picture><source ...><img ...></picture></picture>` ->
    #    `<source ...><img ...>`
    # Use a non-greedy match
    nested_pat = re.compile(
        r'(<source\s+srcset="[^"]+"\s+type="image/webp"[^>]*>)'
        r'\s*<picture>'
        r'(<source\s+srcset="[^"]+"\s+type="image/webp"[^>]*>)'
        r'\s*(<img\b[^>]*>)'
        r'\s*</picture>\s*</picture>',
        re.DOTALL
    )
    text = nested_pat.sub(r'\1\3', text)

    # 2) Any remaining `<picture><source ...><img ...></picture>` is fine but let's
    #    confirm there are no other odd patterns.
    # Count nested pictures
    nested_count = text.count("<picture><source")
    if nested_count != text.count("</picture>"):
        print(f"  [warn] {f.relative_to(ROOT)}: pictures/closes mismatch")

    if text != original:
        f.write_text(text, encoding="utf-8")
        n += 1
        print(f"[fixed] {f.relative_to(ROOT)}")

print(f"\nDone. fixed {n} file(s)")
