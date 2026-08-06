"""
Sweep all 50 blog posts + key pages for tag balance.
"""
import os
import re
from pathlib import Path

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
def count(content, pattern):
    return len(re.findall(pattern, content))

# Check all blog posts + key pages
targets = []
for d in [ROOT / "blog", ROOT / "services", ROOT]:
    if d.is_dir():
        for f in d.rglob("index.html"):
            if any(s in f.parts for s in ("qa", "scripts", "tmp", "archive")):
                continue
            targets.append(f)

# Plus top-level HTMLs
for f in ROOT.glob("*.html"):
    if f.is_file():
        targets.append(f)

targets = sorted(set(targets))
print(f"Checking {len(targets)} files")
print()

problems = []
for f in targets:
    rel = f.relative_to(ROOT)
    c = f.read_text(encoding="utf-8")
    a_o, a_c = count(c, r'<a[\s>]'), count(c, r'</a>')
    p_o, p_c = count(c, r'<p[\s>]'), count(c, r'</p>')
    h3_o, h3_c = count(c, r'<h3[\s>]'), count(c, r'</h3>')
    d_o, d_c = count(c, r'<div[\s>]'), count(c, r'</div>')
    bad = []
    if a_o != a_c: bad.append(f"a {a_o}/{a_c}")
    if p_o != p_c: bad.append(f"p {p_o}/{p_c}")
    if h3_o != h3_c: bad.append(f"h3 {h3_o}/{h3_c}")
    if d_o != d_c: bad.append(f"div {d_o}/{d_c}")
    if bad:
        problems.append((rel, bad))
        print(f"  ✗ {rel}: {', '.join(bad)}")

print()
if problems:
    print(f"PROBLEMS: {len(problems)} files")
else:
    print("ALL BALANCED ✓✓✓")
