"""Targeted source inspection for findings raised by the sweep."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def show(title, text, needle, before=350, after=250, n=1):
    print(f"\n--- {title} ---")
    for i, m in enumerate(re.finditer(re.escape(needle), text)):
        if i >= n:
            break
        s = max(0, m.start() - before)
        print(text[s:m.start() + after].replace("\n", " ")[:900])


styles_dir = ROOT / "styles"
print("styles dir:", [p.name for p in styles_dir.glob("*")][:20])
for p in styles_dir.glob("*.css"):
    t = p.read_text(encoding="utf-8", errors="ignore")
    hits = re.findall(r"[^{}]*overflow-x\s*:\s*(auto|scroll|hidden)[^}]*}", t)
    if hits:
        print(f"\n{p.name}: {len(hits)} overflow-x rules, e.g.:")
        for h in hits[:4]:
            print("   ", h.strip()[:160])
    tbl = re.findall(r"[^{}]*full-pricing-table[^{}]*\{[^}]*\}", t)
    if tbl:
        print(f"\n{p.name}: .full-pricing-table rules:")
        for r in tbl[:3]:
            print("   ", r.strip()[:300])

pricing = (ROOT / "pricing" / "index.html").read_text(encoding="utf-8")
show("pricing table markup", pricing, "full-pricing-table", 400, 300)

order = (ROOT / "order" / "index.html").read_text(encoding="utf-8")
show("order honeypot field", order, "botcheck", 500, 300)

tool = (ROOT / "tools" / "compress-wedding-photos" / "index.html").read_text(encoding="utf-8")
show("tool file input", tool, 'id="file-input"', 450, 250)

collage = (ROOT / "tools" / "wedding-photo-collage" / "index.html").read_text(encoding="utf-8")
print("\n--- google fonts refs in collage tool ---")
for m in re.findall(r"https://fonts\.[a-z]+\.com[^\"')]*", collage):
    print("   ", m[:120])
print("other tools referencing google fonts:")
for p in (ROOT / "tools").glob("*/index.html"):
    t = p.read_text(encoding="utf-8", errors="ignore")
    if "fonts.googleapis.com" in t:
        print("   ", p.parent.name)

hdr = (ROOT / "_headers").read_text(encoding="utf-8") if (ROOT / "_headers").exists() else ""
print("\n--- _headers CSP style/font directives ---")
for line in hdr.splitlines():
    if "style-src" in line or "font-src" in line or "Content-Security" in line:
        print("   ", line.strip()[:300])

mw = (ROOT / "functions" / "_middleware.js").read_text(encoding="utf-8", errors="ignore")
print("\n--- middleware CSP construction ---")
for m in re.findall(r"[^\n]*style-src[^\n]*", mw):
    print("   ", m.strip()[:300])
for m in re.findall(r"[^\n]*fonts\.googleapis[^\n]*", mw):
    print("   ", m.strip()[:300])
