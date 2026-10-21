"""Quick triage dump over sweep results (used while iterating on findings)."""
import collections
import glob
import json
import sys
from pathlib import Path

R = Path(__file__).resolve().parent / "results"
files = sys.argv[1:] or sorted(str(p) for p in R.glob("sweep-*.json"))
for f in files:
    d = json.load(open(f, encoding="utf-8"))
    if not d:
        continue
    p = lambda r: r.get("probe") or {}  # noqa: E731
    errs = [r for r in d if r.get("error")]
    print(f"\n########## {Path(f).name} — {len(d)} records, {len(errs)} load errors")
    if errs:
        print("  load errors:", [(r["path"], (r.get("error") or "")[:60]) for r in errs[:5]])

    ovf = [r for r in d if p(r).get("overflowX", 0) > 2]
    print(f"  overflowX>2 : {len(ovf)}/{len(d)}")
    for x in sorted(ovf, key=lambda r: -p(r).get("overflowX", 0))[:10]:
        off = (p(x).get("overflowOffenders") or [])[:2]
        print(f"    {p(x).get('overflowX'):>4}px {x['path']}")
        for o in off:
            print(f"          {o['tag']}.{o['cls'][:38]} w={o['w']} L={o['left']} R={o['right']}")
    seg = collections.Counter(r["path"].strip("/").split("/")[0] or "home" for r in ovf)
    tot = collections.Counter(r["path"].strip("/").split("/")[0] or "home" for r in d)
    print("  overflow by section:", {k: f"{seg[k]}/{tot[k]}" for k in sorted(tot)})

    for key, label in (("dupIds", "duplicate ids"), ("deadAnchors", "dead in-page anchors")):
        hits = [(r["path"], p(r)[key]) for r in d if p(r).get(key)]
        if hits:
            print(f"  {label}: {len(hits)} pages")
            for h in hits[:8]:
                print("     ", h[0], str(h[1])[:120])

    unl = [(r["path"], p(r)["unlabeledFields"][:2]) for r in d if p(r).get("unlabeledFieldsCount", 0)]
    if unl:
        print(f"  unlabelled form fields: {len(unl)} pages")
        for h in unl[:8]:
            print("     ", h[0], h[1])

    ce = [(r["path"], [c["text"][:100] for c in r["consoleErrors"]]) for r in d if r.get("consoleErrors")]
    if ce:
        print(f"  console errors: {len(ce)} pages")
        for h in ce[:8]:
            print("     ", h[0], h[1][:2])

    br = [(r["path"], p(r)["brokenImages"][:3]) for r in d if p(r).get("brokenImages")]
    if br:
        print(f"  broken images: {len(br)} pages")
        for h in br[:8]:
            print("     ", h[0], h[1])

    bad = [(r["path"], r["badResponses"][:3]) for r in d if r.get("badResponses")]
    if bad:
        print(f"  4xx/5xx same-origin: {len(bad)} pages")
        for h in bad[:8]:
            print("     ", h[0], h[1])

    langbad = [(r["path"], r.get("langScriptMismatch")) for r in d if r.get("langOK") is False]
    if langbad:
        print(f"  language mismatch: {len(langbad)} pages")
        for h in langbad[:10]:
            print("     ", h[0], h[1])

    tiny = [p(r).get("tiny24", 0) for r in d if "tiny24" in p(r)]
    if tiny:
        print(f"  sub-24px targets: pages={sum(1 for t in tiny if t)} max={max(tiny)} "
              f"sample={[ (r['path'], p(r)['tiny24Samples'][:2]) for r in d if p(r).get('tiny24Samples')][:2]}")

    heavy = sorted(((p(r).get("transferKB", 0), r["path"]) for r in d), reverse=True)[:5]
    print("  heaviest pages (uncompressed local):", heavy)
    slow = sorted(((p(r).get("load", 0), r["path"]) for r in d), reverse=True)[:5]
    print("  slowest load ms (local miniflare):", slow)
