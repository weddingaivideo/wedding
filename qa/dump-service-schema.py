#!/usr/bin/env python3
"""Dump the Service JSON-LD block from index.html for inspection."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
content = (ROOT / "index.html").read_text(encoding="utf-8")

# Find each JSON-LD block
blocks = re.findall(
    r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
    content,
    re.DOTALL,
)

print(f"Found {len(blocks)} JSON-LD blocks in index.html")
print()
for i, block in enumerate(blocks, 1):
    # @type is in the first line of the JSON
    m = re.search(r'"@type"\s*:\s*"([^"]+)"', block)
    if m:
        print(f"=== Block {i}: {m.group(1)} ===")
        print(block)
        print()
