"""Find budget-calculator files with the inner-quotes-in-string bug."""
import os, re, json
from pathlib import Path
REPO = Path("C:/Users/qiaoshan/.openclaw/workspace/weddingai")
SKIP = ('.git','.en-backup','.tmp','.wrangler','__pycache__','.cowork-temp','.well-known','.github','tests','internal-tools','qa','private/.archive','private/.reverse-progress','private/.translate-progress')
LD_RE = re.compile(r'<script type="application/ld\+json">(.+?)</script>', re.DOTALL)
fails = []
for root, dirs, files in os.walk(REPO):
    dirs[:] = [d for d in dirs if d not in SKIP and not any(s in os.path.join(root, d) for s in SKIP)]
    for f in files:
        if not f.endswith('.html'): continue
        p = Path(root) / f
        if 'budget-calculator' not in str(p): continue
        try: t = p.read_text(encoding='utf-8', errors='ignore')
        except: continue
        for m in LD_RE.finditer(t):
            try: json.loads(m.group(1))
            except json.JSONDecodeError as e:
                fails.append((p.relative_to(REPO), e.pos, m.group(1)[max(0,e.pos-30):e.pos+30]))
for f, pos, ctx in fails: print(f"{f} @ {pos}: {ctx!r}")
