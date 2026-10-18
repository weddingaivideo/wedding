from pathlib import Path
import re
import json
p = Path("C:/Users/qiaoshan/.openclaw/workspace/weddingai/es/tools/wedding-budget-calculator/index.html")
t = p.read_text(encoding="utf-8", errors="ignore")
LD_RE = re.compile(r'<script type="application/ld\+json">(.+?)</script>', re.DOTALL)
matches = list(LD_RE.finditer(t))
print(f"Total JSON-LD blocks: {len(matches)}")
for i, m in enumerate(matches):
    raw = m.group(1)
    try:
        json.loads(raw)
        print(f"  block {i}: OK")
    except json.JSONDecodeError as e:
        print(f"  block {i}: FAIL at char {e.pos}: {e.msg}")
        print(f"    context: {raw[max(0,e.pos-100):e.pos+150]!r}")
        # show char-by-char around the error
        lo = max(0, e.pos-30)
        hi = min(len(raw), e.pos+30)
        for i in range(lo, hi):
            c = raw[i]
            mark = " <-- ERR" if i == e.pos else ""
            print(f"    [{i}] {c!r}{mark}")


