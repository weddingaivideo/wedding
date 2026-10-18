"""Scan all HTML files for relative vs absolute hero image srcset patterns."""
import os
SKIP_DIRS = ('.git', '.en-backup', '.tmp', '.wrangler', 'node_modules', '__pycache__',
             '.cowork-temp', '.well-known', '.github', 'tests', 'internal-tools',
             'private/.archive', 'private/.reverse-progress', 'private/.translate-progress')

REL_PATTERN = 'srcset="hero-wedding-vineyard'   # relative
ABS_PATTERN = 'srcset="/images/hero-wedding-vineyard'  # absolute

rel = []
abs_ = []
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not any(s in os.path.join(root, d) for s in SKIP_DIRS)]
    for f in files:
        if not f.endswith('.html'):
            continue
        p = os.path.join(root, f)
        try:
            t = open(p, encoding='utf-8', errors='ignore').read()
        except Exception:
            continue
        if REL_PATTERN in t:
            rel.append(p)
        if ABS_PATTERN in t:
            abs_.append(p)
print(f"RELATIVE hero srcset: {len(rel)}")
for h in rel[:30]:
    print("  ", h)
print(f"\nABSOLUTE /images/ hero srcset: {len(abs_)}")
for h in abs_[:5]:
    print("  ", h)
