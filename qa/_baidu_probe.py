"""Probe Baidu Translate API connectivity and report what fields are needed.

Endpoint: https://fanyi-api.baidu.com/api/trans/v1/translate
Auth:     appid + q + salt + sign
          sign = md5(appid + q + salt + secretKey).hexdigest()

We try with a fake appid to confirm the endpoint is reachable and
to see the exact error code so the user can supply real credentials.
"""
import hashlib
import json
import random
import string
import sys
import urllib.parse
import urllib.request

SECRET = "yoUb_d9kaju0hciln8mqrjqqg"
APPID = "20260728002654885"  # provided by user
ENDPOINT = "https://fanyi-api.baidu.com/api/trans/vip/translate"


def call(appid, q, src="en", dst="zh"):
    salt = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    sign = hashlib.md5(f"{appid}{q}{salt}{SECRET}".encode("utf-8")).hexdigest()
    params = {
        "q": q,
        "from": src,
        "to": dst,
        "appid": appid,
        "salt": salt,
        "sign": sign,
    }
    url = ENDPOINT + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, headers={"User-Agent": "WeddingAI-i18n-audit/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except Exception as e:
        return -1, f"{type(e).__name__}: {e}"


status, body = call(APPID, "test", "en", "zh")
print(f"APPID probe: HTTP {status}")
try:
    j = json.loads(body)
    print(f"  body: {json.dumps(j, ensure_ascii=False, indent=2)}")
except Exception:
    print(f"  raw:  {body[:500]}")
