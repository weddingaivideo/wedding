"""Scan all HTML for remaining JSON-LD parse errors."""
import os
import re
import json
from pathlib import Path

REPO = Path("C:/Users/qiaoshan/.openclaw/workspace/weddingai")
SKIP = ('.git', '.en-backup', '.tmp', '.wrangler', '__pycache__', '.cowork-temp',
        '.well-known', '.github', 'tests', 'internal-tools', 'qa',
        'private/.archive', 'private/.reverse-progress', 'private/.translate-progress')
# The script tag must be matched with ANY attribute layout. A strict
# `<script type="application/ld+json">` misses `<script data-x="1"
# type="application/ld+json">`, single quotes or a different spacing — and a
# block that is never matched is never parsed, so its parse error is never
# reported. Same trap as the visible-FAQ matcher in verify-schemas.py: a
# checker that measures only the form it was written against reports "nothing
# is wrong" about every form it never sees.
LD_RE = re.compile(
    r'<script\b[^>]*\btype\s*=\s*["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE)
# How many failures are printed in full. The TOTAL is always printed, and the
# number of failures that were NOT shown is printed too: a silently truncated
# list reads exactly like the whole truth, which is how "20 problems" gets
# believed when there are 200.
MAX_SHOWN = 20
fails = []
total_ld = 0
for root, dirs, files in os.walk(REPO):
    dirs[:] = [d for d in dirs if d not in SKIP and not any(s in os.path.join(root, d) for s in SKIP)]
    for f in files:
        if not f.endswith(".html"):
            continue
        p = Path(root) / f
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in LD_RE.finditer(t):
            total_ld += 1
            try:
                json.loads(m.group(1))
            except json.JSONDecodeError as e:
                fails.append((p.relative_to(REPO), str(e)))
print(f"Total JSON-LD blocks: {total_ld}")
print(f"Still-failing: {len(fails)}")
if fails:
    shown = fails[:MAX_SHOWN]
    print(f"Showing first {len(shown)} of {len(fails)} failure(s):")
    for f, e in shown:
        print(f"  {f}: {e}")
    if len(fails) > len(shown):
        print(f"  ... {len(fails) - len(shown)} more failure(s) not shown")
