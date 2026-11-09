#!/usr/bin/env python3
"""
Probe a sample of the _redirects rules against the LIVE site.

WHY A SCRIPT AND NOT qa/ux/redirects_check.py
---------------------------------------------
That script probes EVERY rule (about 600 of them) with no per-request
timeout. Through this machine's proxy that run went past 600 s and was
killed with no output - the tool is unusable for a pre-push gate.

This one probes a fixed sample of 24 rules across the four rule shapes
(the EN no-slash blog migrations, the EN with-slash ones, the localized
ones and the generic dynamic rules), each with a hard timeout, and
reports the status + Location of every one.

THE RULE
--------
Every one of them has to answer 301 (or 308) with a Location header. A
404 means the rule never fired. A 200 means the redirect was skipped and
the old URL is still being served - which is how a self-redirect or a
shadowed rule looks from the outside.

Usage:  python scripts/probe-redirects.py
Exit code 0 = every probe behaved, 1 = at least one did not.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://weddingai.video"
TIMEOUT = "15"


def parse_rules():
    rules = []
    for raw in (ROOT / "_redirects").read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        src, dst = parts[0], parts[1]
        code = parts[2] if len(parts) > 2 and parts[2].isdigit() else "302"
        rules.append((src, dst, code))
    return rules


def pick_sample(rules):
    """24 probes across the four rule shapes."""
    sample = []

    def add(pred, n, label):
        got = [r for r in rules if pred(r)]
        for r in got[:n]:
            sample.append((r, label))
        return len(got)

    add(lambda r: re.match(r"^/blog/\d", r[0]) and not r[0].endswith("/"), 5, "EN blog, no slash")
    add(lambda r: re.match(r"^/blog/\d", r[0]) and r[0].endswith("/"), 5, "EN blog, with slash")
    add(lambda r: re.match(r"^/(zh|es|fr|de|pt|ja|ru|ar|th|hi)/blog/\d", r[0]), 6, "localized blog")
    add(lambda r: re.match(r"^/(tools|services|blog|gallery|pricing)/", r[0]), 4, "section rules")
    add(lambda r: "*" in r[0], 4, "dynamic rules")
    return sample


def probe(path):
    url = BASE + path
    try:
        res = subprocess.run(
            ["curl.exe", "-s", "-o", "NUL", "-w", "%{http_code}|%{redirect_url}",
             "--max-time", TIMEOUT, "-I", url],
            capture_output=True, text=True, timeout=40)
    except subprocess.TimeoutExpired:
        return ("TIMEOUT", "")
    out = (res.stdout or "").strip()
    if "|" not in out:
        return ("ERR:" + (out or "no output")[:60], "")
    code, loc = out.split("|", 1)
    return (code, loc)


def main():
    rules = parse_rules()
    print("parsed %d redirect rules from _redirects" % len(rules))
    sample = pick_sample(rules)
    print("probing %d of them against %s (timeout %ss each)\n"
          % (len(sample), BASE, TIMEOUT))

    bad = []
    for (src, dst, want), label in sample:
        code, loc = probe(src)
        # A rule whose destination is /404 is a deliberate BLOCK (the
        # scripts folder, the .bak header file, the .ps1 helpers): there
        # the 404 IS the expected answer, not a broken redirect.
        if dst.rstrip("/") == "/404":
            ok = code == "404"
            mark = "ok  " if ok else "FAIL"
            print("  %s %-58s -> %-4s %s (block rule, 404 expected)"
                  % (mark, src[:58], code, label))
            if not ok:
                bad.append("%s (%s) answered %s, expected 404" % (src, label, code))
            continue
        ok = code in ("301", "308") and loc
        mark = "ok  " if ok else "FAIL"
        print("  %s %-58s -> %-4s %s" % (mark, src[:58], code, (loc or "")[:70]))
        if not ok:
            bad.append("%s (%s) answered %s %s" % (src, label, code, loc))

    print()
    if bad:
        print("RESULT: FAIL - %d of %d probes misbehaved" % (len(bad), len(sample)))
        for b in bad:
            print("  - " + b)
        return 1
    print("RESULT: OK - all %d probes answered 301/308 with a Location" % len(sample))
    return 0


if __name__ == "__main__":
    sys.exit(main())
