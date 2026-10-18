"""Find <img> tags without alt= attribute in heic-to-jpg tool pages (and similar)."""
import os
import re
from pathlib import Path

REPO = Path("C:/Users/qiaoshan/.openclaw/workspace/weddingai")
SKIP = ('.git', '.en-backup', '.tmp', '.wrangler', '__pycache__', '.cowork-temp',
        '.well-known', '.github', 'tests', 'internal-tools', 'qa',
        'private/.archive', 'private/.reverse-progress', 'private/.translate-progress')

# img without alt
NO_ALT_RE = re.compile(r'<img\s+[^>]*?>', re.DOTALL)
HAS_ALT_RE = re.compile(r'\salt\s*=')
# img with alt=""
EMPTY_ALT_RE = re.compile(r'\salt\s*=\s*""')

per_lang = {}
for root, dirs, files in os.walk(REPO):
    dirs[:] = [d for d in dirs if d not in SKIP and not any(s in os.path.join(root, d) for s in SKIP)]
    for f in files:
        if not f.endswith(".html"):
            continue
        p = Path(root) / f
        if "heic-to-jpg" not in str(p):
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        rel = p.relative_to(REPO)
        lang = rel.parts[0] if len(rel.parts) > 1 else "root"
        no_alt = []
        empty_alt = []
        for m in NO_ALT_RE.finditer(t):
            tag = m.group(0)
            if not HAS_ALT_RE.search(tag):
                no_alt.append(tag[:200])
            elif EMPTY_ALT_RE.search(tag):
                empty_alt.append(tag[:200])
        per_lang[lang] = (no_alt, empty_alt)
        if no_alt or empty_alt:
            print(f"{rel}: no_alt={len(no_alt)} empty_alt={len(empty_alt)}")
            for x in no_alt[:3]:
                print(f"  no_alt: {x[:160]}")
            for x in empty_alt[:3]:
                print(f"  empty_alt: {x[:160]}")

print("\n=== Per lang summary ===")
for lang, (no, em) in sorted(per_lang.items()):
    print(f"  {lang}: no_alt={len(no)} empty_alt={len(em)}")
