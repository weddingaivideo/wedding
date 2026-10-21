"""Root-cause checks for the console/DOM findings."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

print("=== i18n dictionary coverage ===")
en = json.loads((ROOT / "i18n" / "en.json").read_text(encoding="utf-8"))
print(f"  en.json keys: {len(en)}")
for lang in ["zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]:
    p = ROOT / "i18n" / f"{lang}.json"
    if not p.exists():
        print(f"  {lang}: MISSING FILE")
        continue
    d = json.loads(p.read_text(encoding="utf-8"))
    have = sum(1 for k in d if d.get(k))
    same = sum(1 for k, v in d.items() if isinstance(v, str) and isinstance(en.get(k), str) and v.strip() == en[k].strip() and v.strip())
    print(f"  {lang}: {have}/{len(en)} filled ({100*have/len(en):.1f}%), "
          f"{same} identical to English ({100*same/len(en):.1f}%)")

print("\n=== <select> containing non-<option> children (source HTML) ===")
targets = ["order/index.html", "es/order/index.html", "ja/order/index.html",
           "ru/order/index.html", "th/order/index.html", "pt/order/index.html"]
for rel in targets:
    p = ROOT / rel
    if not p.exists():
        print(f"  {rel}: file missing")
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    bad = []
    for m in re.finditer(r"<select\b[^>]*>(.*?)</select>", t, re.S):
        inner = m.group(1)
        stripped = re.sub(r"<option\b[^>]*>.*?</option>", "", inner, flags=re.S)
        stripped = re.sub(r"\s+", " ", stripped).strip()
        if stripped:
            bad.append(stripped[:120])
    print(f"  {rel}: {'; '.join(bad) if bad else 'clean'}")

print("\n=== does /es/order/ come from middleware or a static file? ===")
for lang in ["es", "ja", "ru", "th", "pt", "zh"]:
    d = ROOT / lang / "order"
    print(f"  {lang}/order/index.html exists: {(d / 'index.html').exists()}")

print("\n=== breadcrumb / footer-badge markup (tap-target evidence) ===")
about = (ROOT / "about" / "index.html").read_text(encoding="utf-8", errors="ignore")
for cls in ["footer-badge", "breadcrumb"]:
    m = re.search(rf'[^<>]*class="[^"]*{cls}[^"]*"[^>]*>', about)
    print(f"  {cls}: {m.group(0).strip()[:160] if m else 'not found on /about/'}")

print("\n=== wa-tool-card width (overflow evidence) ===")
iv = (ROOT / "tools" / "wedding-video-invitation-maker" / "index.html").read_text(encoding="utf-8", errors="ignore")
for m in re.finditer(r"wa-tool-card[^>]{0,200}", iv):
    print("  ", m.group(0)[:200])
    break
tcss = (ROOT / "styles" / "tools.css").read_text(encoding="utf-8", errors="ignore")
for m in re.finditer(r"[^{}]*wa-tool-card[^{}]*\{[^}]*\}", tcss):
    print("  CSS:", m.group(0).strip()[:220])

print("\n=== seating-panel (overflow evidence) ===")
sc = (ROOT / "tools" / "wedding-seating-chart-maker" / "index.html").read_text(encoding="utf-8", errors="ignore")
for m in re.finditer(r"[^{}]*seating-(panel|layout-wrap)[^{}]*\{[^}]*\}", tcss + sc):
    print("  ", m.group(0).strip()[:220])
