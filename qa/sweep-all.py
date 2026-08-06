"""
Final sweep: check tag balance on all changed files.
"""
import re
from pathlib import Path

ROOT = Path(r"C:/Users/qiaoshan/.openclaw/workspace/weddingai")

# Files we touched
files = [
    "404.html",
    "index.html",
    "order/index.html",
    "blog/index.html",
    "blog/restore-vhs-wedding-footage/index.html",
    "blog/ai-wedding-video-generator-guide/index.html",
    "blog/wedding-slow-motion-effect/index.html",
    "blog/wedding-video-from-photos/index.html",
    "blog/include-remote-family-wedding-video/index.html",
    "blog/pet-wedding-videos/index.html",
    "blog/cinematic-wedding-trailer-guide/index.html",
    "blog/honor-deceased-parent-wedding/index.html",
    "blog/vhs-to-digital-wedding-cost/index.html",
]

def count(content, pattern):
    return len(re.findall(pattern, content))

print(f"{'file':<60} {'<a':>4}/{'</a>':>5} {'<p':>4}/{'</p>':>5} {'<h3':>4}/{'</h3>':>5} {'<div':>5}/{'</div>':>6}")
print("-" * 110)

problems = []
for rel in files:
    f = ROOT / rel
    if not f.exists():
        print(f"  MISSING: {rel}")
        continue
    c = f.read_text(encoding="utf-8")
    a_o, a_c = count(c, r'<a[\s>]'), count(c, r'</a>')
    p_o, p_c = count(c, r'<p[\s>]'), count(c, r'</p>')
    h_o, h_c = count(c, r'<h3[\s>]'), count(c, r'</h3>')
    d_o, d_c = count(c, r'<div[\s>]'), count(c, r'</div>')
    short = rel.replace('weddingai.video/', '')[:58]
    print(f"  {short:<58} {a_o:>4}/{a_c:>5} {p_o:>4}/{p_c:>5} {h_o:>4}/{h_c:>5} {d_o:>5}/{d_c:>6}")
    if a_o != a_c: problems.append(f"{rel}: <a> {a_o} vs </a> {a_c}")
    if p_o != p_c: problems.append(f"{rel}: <p> {p_o} vs </p> {p_c}")
    if h_o != h_c: problems.append(f"{rel}: <h3> {h_o} vs </h3> {h_c}")
    if d_o != d_c: problems.append(f"{rel}: <div> {d_o} vs </div> {d_c}")

print("-" * 110)
if problems:
    print("PROBLEMS:")
    for p in problems:
        print(f"  - {p}")
else:
    print("ALL BALANCED ✓")
