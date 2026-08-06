"""Single-worker gtx speed test, 30 items, to gauge real rate."""
import json
import sys
import time
sys.path.insert(0, "qa")
from i18n_reverse_google import call_gtx
from pathlib import Path

ROOT = Path(".")
tgt = json.loads((ROOT / "i18n" / "zh.json").read_text(encoding="utf-8"))
en = json.loads((ROOT / "i18n" / "en.json").read_text(encoding="utf-8"))

# pick 30 mid-length items
keys = [k for k in en if k != "_meta" and 60 < len(en[k]) < 200][:30]
print(f"Testing {len(keys)} items serially...")
t0 = time.time()
ok, fail = 0, 0
for k in keys:
    r = call_gtx(tgt.get(k, ""), "zh-CN")
    if r is None:
        fail += 1
    else:
        ok += 1
    print(f"  {k[:40]:40s} -> {(r or 'FAIL')[:60]}")
elapsed = time.time() - t0
print(f"\nDone: ok={ok} fail={fail} in {elapsed:.1f}s ({elapsed/max(ok,1):.2f}s/call)")
