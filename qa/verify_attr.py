"""Verify applyDataI18nAttr works on real HTML."""
import re
import json
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
exec((ROOT / "qa" / "test_middleware_regex.py").read_text(encoding="utf-8").split("# --- Tests ---")[0])

zh = json.loads((ROOT / "i18n" / "zh.json").read_text(encoding="utf-8"))
index = (ROOT / "index.html").read_text(encoding="utf-8")

# Count before
n_before = len(re.findall(r"data-i18n-attr=", index))
print(f"Before: {n_before} data-i18n-attr attrs")

# Apply only the data-i18n-attr pass
out = applyDataI18nAttr(index, zh)

# Count after
n_after = len(re.findall(r"data-i18n-attr=", out))
print(f"After: {n_after} data-i18n-attr attrs (should be 0)")

# Check meta description
m = re.search(r'<meta\s+name="description"[^>]+/?>', out)
if m:
    print(f"\nMeta description tag:")
    print(f"  {m.group(0)}")

# Check the meta description content
m2 = re.search(r'<meta\s+name="description"[^>]*content="([^"]+)"', out)
if m2:
    print(f"  Content (first 100 chars): {m2.group(1)[:100]}")
