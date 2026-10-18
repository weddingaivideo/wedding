"""Inspect budget-calculator JSON-LD."""
from pathlib import Path
import re

p = Path("C:/Users/qiaoshan/.openclaw/workspace/weddingai/ar/tools/wedding-budget-calculator/index.html")
text = p.read_text(encoding="utf-8", errors="ignore")
LD_RE = re.compile(r'<script type="application/ld\+json">(.+?)</script>', re.DOTALL)
m = LD_RE.search(text)
if m:
    raw = m.group(1)
    print("=== raw JSON-LD ===")
    print(raw[:1500])
