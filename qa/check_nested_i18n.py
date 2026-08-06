"""Check how many data-i18n elements have nested tags inside."""
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
# Find all HTML files (not in qa/ or internal-tools/)
files = list(ROOT.rglob("*.html"))
files = [f for f in files if "qa" not in f.parts and "internal-tools" not in f.parts and "admin" not in f.parts]

total = 0
nested = 0
for f in files:
    try:
        html = f.read_text(encoding="utf-8")
    except Exception:
        continue
    # Match: <tag attrs data-i18n="key">inner</tag>
    # Use backreference to find matching closing tag
    for m in re.finditer(r'<([a-zA-Z][a-zA-Z0-9]*)\b[^>]*\bdata-i18n="([^"]+)"[^>]*>(.*?)</\1>', html, re.DOTALL):
        total += 1
        inner = m.group(3)
        if "<" in inner:
            nested += 1
            if nested < 8:
                rel = f.relative_to(ROOT)
                print(f"NESTED in {rel} [{m.group(1)} key={m.group(2)}]:")
                print(f"  snippet: {m.group(0)[:250]}")
                print()

print(f"---")
print(f"Total data-i18n elements scanned: {total}")
print(f"With nested tags inside: {nested} ({100.0*nested/total:.2f}%)")
