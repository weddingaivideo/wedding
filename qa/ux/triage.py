"""Triage the interaction FAILs: real defect vs harness artefact."""
import json
import re
from pathlib import Path

R = Path(__file__).resolve().parent / "results"
ROOT = Path(__file__).resolve().parents[2]
inter = json.loads((R / "interactions.json").read_text(encoding="utf-8"))

print("=== keyboard reachability of upload controls (all 13 tools) ===")
for x in inter:
    if x["id"].endswith("-KBD"):
        print(f"  {x['status']:<5} {x['page']:<52} {x['detail'][:150]}")

print("\n=== every FAIL grouped ===")
for x in inter:
    if x["status"] == "FAIL":
        print(f"  {x['id']:<32} {x['page']:<44} {x['detail'][:130]}")

print("\n=== every WARN ===")
for x in inter:
    if x["status"] == "WARN":
        print(f"  {x['id']:<32} {x['page']:<44} {x['detail'][:140]}")

print("\n=== source checks ===")
home = (ROOT / "index.html").read_text(encoding="utf-8", errors="ignore")
ids = set(re.findall(r'id="([^"]+)"', home))
for anchor in ["services", "pricing", "tools", "gallery", "faq", "how-it-works", "reviews"]:
    print(f"  home has #{anchor}: {anchor in ids}")

nav_html = (ROOT / "index.html").read_text(encoding="utf-8", errors="ignore")
m = re.search(r'<nav class="main-nav".*?</nav>', nav_html, re.S)
if m:
    links = re.findall(r'href="([^"]+)"', m.group(0))
    print(f"  header nav hrefs: {links}")

search = (ROOT / "search" / "index.html").read_text(encoding="utf-8", errors="ignore")
print("\n  --- search page: how are results produced? ---")
print("   has fetch/XHR:", bool(re.search(r"fetch\(|XMLHttpRequest|search-index|index\.json", search)))
for mm in re.finditer(r"(fetch\([^)]*\)|searchIndex[^;\n]{0,80}|/search/[^'\"\s]{0,40})", search):
    print("    ", mm.group(0)[:110])
js = (ROOT / "js" / "main.js").read_text(encoding="utf-8", errors="ignore")
print("   main.js mentions search:", "search" in js.lower())
for f in (ROOT / "js").glob("*.js"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "search" in t.lower():
        print(f"   {f.name}: mentions search ({len(re.findall('search', t, re.I))} times)")

quote = (ROOT / "functions" / "api" / "quote.js").read_text(encoding="utf-8", errors="ignore")
print("\n  --- /api/quote behaviour ---")
for mm in re.finditer(r"^\s*(return Response\.redirect|.*30[0-9]|RESEND|status.*pending).*$", quote, re.M):
    line = mm.group(0).strip()
    if line:
        print("   ", line[:150])
