"""Debug Baidu sign computation by printing everything before sending."""
import hashlib
import json
import random
import string
import urllib.parse
import urllib.request

APPID = "20260728002654885"
SECRET = "yoUb_d9kaju0hciln8mqrjqqg"
ENDPOINT = "https://fanyi-api.baidu.com/api/trans/vip/translate"

q = "test"
src = "en"
dst = "zh"
salt = "1435660288"  # baidu docs example uses fixed salt like this

# Build sign string exactly as baidu docs say
sign_src = APPID + q + salt + SECRET
sign = hashlib.md5(sign_src.encode("utf-8")).hexdigest()
print(f"sign_src = {sign_src!r}")
print(f"sign     = {sign!r}")
print(f"sign_md5 = {hashlib.md5(sign_src.encode('utf-8')).hexdigest()!r}")

params = {
    "q": q,
    "from": src,
    "to": dst,
    "appid": APPID,
    "salt": salt,
    "sign": sign,
}
url = ENDPOINT + "?" + urllib.parse.urlencode(params)
print(f"\nURL:\n{url}\n")

req = urllib.request.Request(url, headers={"User-Agent": "WeddingAI-i18n-audit/1.0"})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode("utf-8")
        print(f"HTTP {resp.status}")
        print(json.dumps(json.loads(body), ensure_ascii=False, indent=2))
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="replace")
    print(f"HTTP {e.code}")
    try:
        print(json.dumps(json.loads(body), ensure_ascii=False, indent=2))
    except Exception:
        print(body)
