"""Re-check 'worse' translations — is sim really low or is there a bug?"""
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(".")
en = json.loads(open(ROOT / "i18n/en.json", encoding="utf-8").read())
zh_new = json.loads(open(ROOT / "i18n/zh.json", encoding="utf-8").read())
rows = list(csv.DictReader(open(ROOT / "qa/i18n_fix_zh_validation.csv", encoding="utf-8")))
worse = [r for r in rows if r["verdict"] == "worse"]
print(f"Re-checking {len(worse)} worse translations with fresh reverse-translate...")
print()


def call_gtx(q, src="zh-CN", dst="en", retries=3):
    if not q:
        return q
    for attempt in range(retries):
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {"client": "gtx", "sl": src, "tl": dst, "dt": "t", "q": q}
            full = url + "?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(full, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8")
            j = json.loads(raw)
            if j and j[0]:
                return "".join(seg[0] for seg in j[0] if seg and seg[0])
        except Exception:
            if attempt < retries - 1:
                time.sleep(0.5 * (attempt + 1))
    return None


def normalize(s):
    return "".join(ch.lower() if ch.isalnum() or ch.isspace() else " " for ch in s)


def sim(a, b):
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


for r in worse[:5]:
    k = r["key"]
    en_v = en[k]
    new_zh = zh_new[k]
    back = call_gtx(new_zh, "zh-CN", "en")
    s = sim(en_v, back) if back else 0
    print(f"  {k}")
    print(f"    EN ({len(en_v)}c):  {en_v}")
    print(f"    NEW ({len(new_zh)}c): {new_zh}")
    print(f"    back ({len(back) if back else 0}c): {back}")
    print(f"    sim = {s:.3f}  (csv said 0.057)")
    print()
