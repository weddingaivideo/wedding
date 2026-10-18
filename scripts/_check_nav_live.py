"""Check live nav Free Tools / Privacy Policy text per language."""
import urllib.request
import re

NAVS = [
    ("/", "EN"),
    ("/zh/", "zh"),
    ("/es/", "es"),
    ("/fr/", "fr"),
    ("/de/", "de"),
    ("/pt/", "pt"),
    ("/ja/", "ja"),
    ("/ru/", "ru"),
    ("/ar/", "ar"),
    ("/th/", "th"),
    ("/hi/", "hi"),
]
for path, lang in NAVS:
    try:
        req = urllib.request.Request(f"https://weddingai.video{path}", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"})
        body = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", errors="ignore")
        m = re.search(r'<a href="/tools/"[^>]*?>([^<]+)</a>', body)
        free = m.group(1) if m else "NO NAV LINK"
        m2 = re.search(r'<a href="/privacy/"[^>]*?>([^<]+)</a>', body)
        priv = m2.group(1) if m2 else "NO PRIV LINK"
        print(f"{path:8} {lang:3} FreeTools={free!r:40}  Privacy={priv!r}")
    except Exception as e:
        print(f"{path:8} {lang:3} ERR: {e}")
