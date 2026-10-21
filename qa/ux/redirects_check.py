"""Probe every legacy URL declared in _redirects.

`wrangler pages dev` reported 36 invalid rules (status 404 is not a legal redirect
code) and "Maximum number of dynamic rules supported is 100. Skipping remaining
210 lines of file." This checks what a visitor actually gets for those paths:
a working 30x, or a dead 404.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import ROOT, save  # noqa: E402
from sweep import http_status, to_local  # noqa: E402


def parse_redirects():
    lines = (ROOT / "_redirects").read_text(encoding="utf-8", errors="ignore").splitlines()
    rules = []
    for i, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        src, dst = parts[0], parts[1]
        code = parts[2] if len(parts) > 2 and parts[2].isdigit() else "302"
        rules.append({"line": i, "src": src, "dst": dst, "code": code})
    return rules


def main() -> None:
    rules = parse_redirects()
    print(f"parsed {len(rules)} redirect rules from _redirects")
    out = []
    bad = []
    for r in rules:
        src = r["src"]
        if "*" in src or ":" in src.split("/")[1:2][0:1]:
            # wildcard/placeholder rules cannot be probed one-to-one
            continue
        path = src if src.endswith("/") or "." in src.split("/")[-1] else src
        st, final = http_status(to_local(path))
        rec = {**r, "probe": path, "status": st, "final": final.replace("http://127.0.0.1:8788", "")}
        out.append(rec)
        if st == 0 or st >= 400:
            bad.append(rec)
        print(f"  {path:<58} {st:>4} -> {rec['final'][:60]}", flush=True)
    save("redirects.json", {"rules": out, "dead": bad})
    print(f"\nprobed {len(out)} legacy paths; dead/404: {len(bad)}")
    for b in bad[:25]:
        print(f"   {b['status']:>4} {b['probe']} -> {b['dst']} (rule line {b['line']})")


if __name__ == "__main__":
    main()
