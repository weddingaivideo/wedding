#!/usr/bin/env python3
"""Validate all JSON-LD blocks in a page parse as legal JSON and meet SEO criteria."""
import json
import re
import sys
from pathlib import Path


def validate(path: Path) -> bool:
    content = path.read_text(encoding="utf-8")
    blocks = re.findall(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        content,
        re.DOTALL,
    )
    print(f"{path.name}: {len(blocks)} JSON-LD blocks")
    all_ok = True
    for i, b in enumerate(blocks, 1):
        try:
            data = json.loads(b)
        except Exception as e:
            print(f"  Block {i}: PARSE ERROR - {e}")
            all_ok = False
            continue
        t = data.get("@type", "Unknown")
        keys = list(data.keys())
        print(f"  Block {i}: @type={t}, keys={keys}")
        # SEO-specific checks
        if t == "Service":
            if "aggregateRating" in data:
                print("    ⚠ Service still has aggregateRating (Google risk)")
                all_ok = False
            if "review" in data:
                print("    ⚠ Service still has review block (Google risk)")
                all_ok = False
            if "provider" in data:
                print("    ✓ Service has provider")
        if t == "FAQPage":
            if "mainEntity" in data and isinstance(data["mainEntity"], list):
                print(f"    ✓ FAQPage has {len(data['mainEntity'])} Q&As")
    return all_ok


if __name__ == "__main__":
    p = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")
    if not p.exists():
        print(f"FAIL: {p} not found")
        sys.exit(1)
    ok = validate(p)
    sys.exit(0 if ok else 1)
