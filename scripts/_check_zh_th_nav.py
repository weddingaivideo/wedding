"""Spot-check zh and th for untranslated nav items the audit flagged."""
import urllib.request
import re

for path, lang in [("/zh/", "zh"), ("/th/", "th")]:
    req = urllib.request.Request(f"https://weddingai.video{path}", headers={"User-Agent": "Mozilla/5.0"})
    body = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", errors="ignore")
    # Find any nav link with English "Services" (not localized)
    matches = re.findall(r'<a[^>]*?>([A-Z][^<]{3,30})</a>', body)
    print(f"\n=== {path} (lang={lang}) ===")
    FREE_RE = re.compile(r'<a href="/tools/"[^>]*?>([^<]+)</a>')
    PRIV_RE = re.compile(r'<a href="/privacy/"[^>]*?>([^<]+)</a>')
    SVC_RE = re.compile(r'<a[^>]*?href="(/services/?)"[^>]*?>([^<]+)</a>')
    ORD_RE = re.compile(r'<a[^>]*?href="(/order/?)"[^>]*?>([^<]+)</a>')
    PRC_RE = re.compile(r'<a[^>]*?href="(/pricing/?)"[^>]*?>([^<]+)</a>')
    free = FREE_RE.search(body)
    priv = PRIV_RE.search(body)
    print(f"  Free Tools: {free.group(1) if free else 'NONE'!r}")
    print(f"  Privacy: {priv.group(1) if priv else 'NONE'!r}")
    for m in SVC_RE.finditer(body):
        print(f"  Services nav: {m.group(2)!r}")
    for m in ORD_RE.finditer(body):
        print(f"  Order nav: {m.group(2)!r}")
    for m in PRC_RE.finditer(body):
        print(f"  Pricing nav: {m.group(2)!r}")
