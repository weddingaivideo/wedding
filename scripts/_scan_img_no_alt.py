"""Find all HTML files with <img> tags missing alt attribute, ANY file."""
import os
import re
from pathlib import Path

REPO = Path("C:/Users/qiaoshan/.openclaw/workspace/weddingai")
SKIP = ('.git', '.en-backup', '.tmp', '.wrangler', '__pycache__', '.cowork-temp',
        '.well-known', '.github', 'tests', 'internal-tools', 'qa',
        'private/.archive', 'private/.reverse-progress', 'private/.translate-progress')

NO_ALT_RE = re.compile(r'<img\s+[^>]*?>', re.DOTALL)
HAS_ALT_RE = re.compile(r'\salt\s*=')
EMPTY_ALT_RE = re.compile(r'\salt\s*=\s*""')

count = 0
files = 0
for root, dirs, fls in os.walk(REPO):
    dirs[:] = [d for d in dirs if d not in SKIP and not any(s in os.path.join(root, d) for s in SKIP)]
    for f in fls:
        if not f.endswith(".html"):
            continue
        p = Path(root) / f
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in NO_ALT_RE.finditer(t):
            tag = m.group(0)
            if not HAS_ALT_RE.search(tag):
                count += 1
                files += 1
                if files <= 10:
                    print(f"NO ALT: {p.relative_to(REPO)}: {tag[:200]!r}")
                break
print(f"\nFiles with <img> missing alt: {files}")
print(f"Total such tags: {count}")
