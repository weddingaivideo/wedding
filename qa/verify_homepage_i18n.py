"""Verify the homepage has all the required JSON-LD blocks AND middleware will
correctly rewrite inLanguage for non-EN pages."""
import os
import json
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
# Reuse functions
exec((ROOT / "qa" / "test_middleware_regex.py").read_text(encoding="utf-8").split("# --- Tests ---")[0])

html = (ROOT / "index.html").read_text(encoding="utf-8")
zh_dict = json.loads((ROOT / "i18n" / "zh.json").read_text(encoding="utf-8"))

# Apply full pipeline for zh
out = html
out = setOgLocale(out, "zh")
out = rewriteInLanguage(out, "zh")
out = fixOgUrlTrailingSlash(out)
out = applyDataI18n(out, zh_dict)
out = applyDataI18nAttr(out, zh_dict)

# Find all JSON-LD blocks
blocks = re.findall(r'<script[^>]+ld\+json[^>]*>([\s\S]*?)</script>', out)
print(f"Found {len(blocks)} JSON-LD blocks in homepage (after middleware for zh):")
for i, b in enumerate(blocks):
    try:
        obj = json.loads(b)
        atype = obj.get("@type", "?")
        inlang = obj.get("inLanguage", "(none)")
        agg = obj.get("aggregateRating", "(none)")
        print(f"  Block {i+1}: @type={atype}, inLanguage={inlang}, aggregateRating={'YES' if agg != '(none)' else 'no'}")
    except Exception as e:
        print(f"  Block {i+1}: PARSE ERROR: {e}")

# Also verify: schema types covered
types = set()
for b in blocks:
    try:
        obj = json.loads(b)
        t = obj.get("@type")
        if t: types.add(t)
    except Exception:
        pass
print(f"\nTypes present: {sorted(types)}")
print(f"  Organization: {'✓' if 'Organization' in types else '✗'}")
print(f"  WebSite: {'✓' if 'WebSite' in types else '✗'}")
print(f"  FAQPage: {'✓' if 'FAQPage' in types else '✗'}")
print(f"  Service: {'✓' if 'Service' in types else '✗'}")
print(f"  AggregateRating (as field): {'✓' if any('aggregateRating' in b for b in blocks) else '✗'}")
