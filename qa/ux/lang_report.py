"""Language-completeness roll-up + HTML-validity console noise roll-up."""
import collections
import json
import sys
from pathlib import Path

R = Path(__file__).resolve().parent / "results"

sweeps = []
for f in sorted(R.glob("sweep-*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    if d:
        sweeps += [x for x in d if x.get("probe")]

print("=== language mismatch (dominant script != URL language) ===")
mm = [r for r in sweeps if r.get("langOK") is False]
by_lang = collections.defaultdict(list)
for r in mm:
    by_lang[r["lang"]].append(r)
for lang in sorted(by_lang):
    print(f"\n  {lang}: {len(by_lang[lang])} pages")
    for r in sorted(by_lang[lang], key=lambda x: x["path"]):
        m = r.get("langScriptMismatch") or {}
        print(f"    {r['path']:<58} latin={m.get('latinRatio')} scripts={m.get('scripts')}")

print("\n=== per-language page health ===")
print(f"{'lang':<5}{'pages':>6}{'ovf':>6}{'console':>9}{'tiny24':>8}{'load>5s':>9}")
all_lang = collections.defaultdict(list)
for r in sweeps:
    all_lang[r["lang"]].append(r)
for lang in sorted(all_lang):
    rs = all_lang[lang]
    ovf = sum(1 for r in rs if (r["probe"].get("overflowX") or 0) > 2)
    con = sum(1 for r in rs if r.get("consoleErrors"))
    tiny = sum(1 for r in rs if r["probe"].get("tiny24"))
    slow = sum(1 for r in rs if (r["probe"].get("load") or 0) > 5000)
    print(f"{lang:<5}{len(rs):>6}{ovf:>6}{con:>9}{tiny:>8}{slow:>9}")

print("\n=== console noise by message class ===")
cls = collections.Counter()
examples = {}
for r in sweeps:
    for c in r.get("consoleErrors") or []:
        t = c["text"]
        if "span tag was parsed inside" in t:
            k = "invalid <span> inside <select>"
        elif "cdn-cgi" in t or "email-decode" in t:
            k = "/cdn-cgi/ email-decode (local artefact)"
        elif "Refused to load the stylesheet" in t:
            k = "CSP-blocked stylesheet"
        else:
            k = t[:70]
        cls[k] += 1
        examples.setdefault(k, []).append(r["path"])
for k, v in cls.most_common(12):
    print(f"  {v:>4}  {k}")
    print(f"        e.g. {examples[k][:3]}")

print("\n=== span-in-select pages ===")
sp = sorted({r["path"] for r in sweeps
             if any("span tag was parsed inside" in c["text"] for c in (r.get("consoleErrors") or []))})
print(f"  {len(sp)} pages: {sp}")
