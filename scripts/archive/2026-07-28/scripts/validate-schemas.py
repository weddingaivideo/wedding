"""Validate all Schema.org JSON-LD blocks in HTML files."""
import re
import json
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")

errors = []
totals = {}

for p in sorted(ROOT.rglob("*.html")):
    if p.name == "google-site-verification.html":
        continue
    if "scripts" in p.parts:
        continue
    text = p.read_text(encoding="utf-8")
    blocks = re.findall(
        r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>',
        text,
        re.DOTALL,
    )
    for i, b in enumerate(blocks):
        try:
            data = json.loads(b)
        except json.JSONDecodeError as e:
            errors.append(f"{p.name} block #{i + 1}: {e}")
            continue
        t = data.get("@type", "?")
        if isinstance(t, list):
            t = t[0] if t else "?"
        totals[t] = totals.get(t, 0) + 1
        if t == "Product":
            errors.append(f"{p.name}: still has @type:Product (should be Service)")

print("Per-file schema blocks:")
for p in sorted(ROOT.rglob("*.html")):
    if p.name == "google-site-verification.html":
        continue
    if "scripts" in p.parts:
        continue
    text = p.read_text(encoding="utf-8")
    types = re.findall(r'"@type":\s*"([^"]+)"', text)
    seen = set()
    summary = []
    for t in types:
        if t not in seen:
            seen.add(t)
            summary.append(t)
    if summary:
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        print(f"  {rel:55s}  {', '.join(summary)}")

print()
print("Total schema blocks by type:")
for t, n in sorted(totals.items()):
    print(f"  {t:25s}  {n}")

if errors:
    print()
    print("ERRORS:")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
print()
print("All schemas valid.")
