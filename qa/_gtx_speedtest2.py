"""Concurrent gtx speed test."""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, "qa")
from i18n_reverse_google import call_gtx
from pathlib import Path

ROOT = Path(".")
tgt = json.loads((ROOT / "i18n" / "zh.json").read_text(encoding="utf-8"))
en = json.loads((ROOT / "i18n" / "en.json").read_text(encoding="utf-8"))

keys = [(k, en[k], tgt.get(k, "")) for k in en
        if k != "_meta" and 60 < len(en[k]) < 200][:50]
print(f"Testing {len(keys)} items with 8 workers...")
t0 = time.time()
ok, fail = 0, 0
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(call_gtx, t_v, "zh-CN"): (k, en_v)
            for k, en_v, t_v in keys if t_v}
    for fut in as_completed(futs):
        try:
            r = fut.result()
            if r is None: fail += 1
            else: ok += 1
        except Exception:
            fail += 1
elapsed = time.time() - t0
print(f"\nDone: ok={ok} fail={fail} in {elapsed:.1f}s ({elapsed/max(ok+fail,1):.2f}s/call effective, "
      f"{ok/elapsed:.2f} calls/s)")
