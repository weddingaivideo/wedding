#!/usr/bin/env python3
"""检查所有 HTML 页面的 title 和 meta description 长度。"""
import os
import re
import sys
from html import unescape
from pathlib import Path

# Force UTF-8 stdout — Windows CI runners default to cp1252 which crashes
# on the ✅ / ❌ / ⚠️ status glyphs below. Belt-and-suspenders alongside
# the PYTHONIOENCODING=utf-8 env var set in the workflow.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
TITLE_MAX = 60
DESC_MAX = 160

title_pat = re.compile(r'<title>(.*?)</title>', re.DOTALL)
desc_pat = re.compile(r'<meta\s+name="description"\s+content="(.*?)"', re.DOTALL)


def visible_len(s):
    """HTML entity decode + strip whitespace, count visible characters."""
    return len(unescape(s).strip())


def main():
    files = []
    for root, dirs, names in os.walk(ROOT):
        if "scripts\\archive" in root or "scripts/archive" in root:
            continue
        if "tmp\\" in root or "tmp/" in root:
            continue
        for name in names:
            if not name.endswith(".html"):
                continue
            if name == "google-site-verification.html":
                continue
            files.append(os.path.join(root, name))

    rows = []
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        rel = os.path.relpath(path, ROOT).replace("\\", "/")

        m_t = title_pat.search(content)
        m_d = desc_pat.search(content)
        title = unescape(m_t.group(1)).strip() if m_t else "(no <title>)"
        desc = unescape(m_d.group(1)).strip() if m_d else "(no description)"
        t_len = len(title)
        d_len = len(desc)
        t_flag = "❌" if t_len > TITLE_MAX else ("⚠️" if t_len > TITLE_MAX - 5 else "✅")
        d_flag = "❌" if d_len > DESC_MAX else ("⚠️" if d_len > DESC_MAX - 10 else "✅")
        rows.append((rel, t_flag, t_len, title, d_flag, d_len, desc[:80] + ("…" if len(desc) > 80 else "")))

    rows.sort(key=lambda r: (-r[2], r[0]))

    print(f"{'Page':<46} {'T-len':>6}  {'D-len':>6}")
    print("=" * 120)
    for rel, tf, tl, title, df, dl, desc in rows:
        if tf == "❌" or df == "❌":
            print(f"\n{rel}")
            print(f"  title ({tl}): {title}")
            print(f"  desc  ({dl}): {desc}{'…' if len(desc) > 80 else ''}")

    print()
    print("=" * 120)
    print(f"{'Page':<46} {'T':<3}{'len':>5}  {'D':<3}{'len':>5}  Status")
    print("-" * 120)
    bad_t = bad_d = ok = 0
    for rel, tf, tl, title, df, dl, _ in rows:
        status = f"{tf}{tl}  {df}{dl}"
        if tf == "❌" or df == "❌":
            if tf == "❌": bad_t += 1
            if df == "❌": bad_d += 1
        else:
            ok += 1
        print(f"{rel:<46} {tf} {tl:>3}  {df} {dl:>3}")
    print()
    print(f"Summary: {ok} OK, {bad_t} title over 60, {bad_d} description over 160")

    # Exit code: 1 if any page exceeds limits (for CI / pre-deploy-check)
    import sys
    if bad_t > 0 or bad_d > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
