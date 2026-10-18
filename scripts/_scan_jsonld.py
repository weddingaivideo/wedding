"""Scan all HTML for remaining JSON-LD parse errors."""
import os
import re
import json
from pathlib import Path

REPO = Path("C:/Users/qiaoshan/.openclaw/workspace/weddingai")
SKIP = ('.git', '.en-backup', '.tmp', '.wrangler', '__pycache__', '.cowork-temp',
        '.well-known', '.github', 'tests', 'internal-tools', 'qa',
        'private/.archive', 'private/.reverse-progress', 'private/.translate-progress')
LD_RE = re.compile(r'<script type="application/ld\+json">(.+?)</script>', re.DOTALL)
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
for f, e in fails[:20]:
    print(f"  {f}: {e}")
