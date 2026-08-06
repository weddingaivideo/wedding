"""Fix the stray-quote bug in og:url meta tags.
The bug: `content="https://weddingai.video/about"">` (extra " before >)
The fix: `content="https://weddingai.video/about/">` (replace the extra " with /)
"""
import os
import re
from pathlib import Path

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
files = list(ROOT.rglob("*.html"))
files = [f for f in files if "qa" not in f.parts and "tmp" not in f.parts and "internal-tools" not in f.parts and "admin" not in f.parts]

# Pattern matches: <meta property="og:url" content="URL">
# where URL has a stray " at the end before the >
# We need to handle: content="...about"">  →  content="...about/">
fixed = []
for f in files:
    text = f.read_text(encoding="utf-8", errors="replace")
    # Match: <meta property="og:url" content="URL"">  (stray quote before >)
    new_text, n = re.subn(
        r'(<meta\s+property="og:url"\s+content="https://weddingai\.video/[^"]+)"">',
        r'\1/">',
        text,
    )
    if n > 0:
        f.write_text(new_text, encoding="utf-8")
        rel = f.relative_to(ROOT)
        fixed.append((rel, n))

print(f"Fixed {len(fixed)} files:")
for rel, n in fixed:
    print(f"  {rel}: {n} replacement(s)")
