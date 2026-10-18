#!/usr/bin/env python3
"""
Add missing hreflang="ru" to all /hi/blog/* index.html files.

Observed bug: hi blog pages have 11 hreflang links but MISS ru.
Audit said 23 (wrong). Real: 11 with ru missing.
Fix: insert `<link href="https://weddingai.video/ru/blog/<slug>/" hreflang="ru" rel="alternate"/>`
    right before the `<link href="https://weddingai.video/th/blog/<slug>/" hreflang="th" rel="alternate"/>` line.
"""
import re
import sys
from pathlib import Path

REPO = Path("C:/Users/qiaoshan/.openclaw/workspace/weddingai")
HI_BLOG = REPO / "hi" / "blog"

# Match: <link href=".../hi/blog/X/" hreflang="hi" rel="alternate"/>
# Insert: ru hreflang just before th, after ar
# Pattern: th is the closest known-preceding hreflang (alphabetical: en,zh,es,fr,de,pt,ja,ar,th,hi)
# The ru line should be inserted between ar and th.
HI_LINE_RE = re.compile(
    r'(<link href="https://weddingai\.video/ar/blog/[^"]+/" hreflang="ar" rel="alternate"/>)'
    r'\s*'
    r'(<link href="https://weddingai\.video/th/blog/[^"]+/" hreflang="th" rel="alternate"/>)'
)
# Get the slug from the th line so we can build the ru line
TH_LINE_RE = re.compile(r'<link href="https://weddingai\.video/th/blog/([^"]+)/" hreflang="th" rel="alternate"/>')


def fix_file(path: Path) -> tuple[bool, str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if 'hreflang="ru"' in text:
        return False, "ru already present"
    m = TH_LINE_RE.search(text)
    if not m:
        return False, "no th hreflang line found"
    slug = m.group(1)
    ru_line = f'<link href="https://weddingai.video/ru/blog/{slug}/" hreflang="ru" rel="alternate"/>'
    new_text, n = HI_LINE_RE.subn(r'\1' + ru_line + r'\2', text, count=1)
    if n != 1:
        return False, "regex subn did not match expected ar+th pair"
    # Verify the new text has ru
    if 'hreflang="ru"' not in new_text:
        return False, "ru hreflang not in result after sub"
    # Verify count of hreflang tags = 12
    cnt = len(re.findall(r'<link[^>]+hreflang="[^"]+"', new_text))
    if cnt != 12:
        return False, f"expected 12 hreflang tags, got {cnt}"
    # Atomic write
    tmp = path.with_suffix(".html.tmp")
    tmp.write_text(new_text, encoding="utf-8", newline="")
    # Re-verify tmp
    tmp_text = tmp.read_text(encoding="utf-8")
    if tmp_text != new_text:
        tmp.unlink()
        return False, "tmp write mismatch"
    import shutil
    shutil.move(str(tmp), str(path))
    return True, f"+ru link for /ru/blog/{slug}/"


def main():
    if not HI_BLOG.exists():
        print(f"ERROR: {HI_BLOG} not found")
        sys.exit(1)
    files = sorted([p for p in HI_BLOG.iterdir() if p.is_dir() and (p / "index.html").exists()])
    print(f"Found {len(files)} hi blog directories")
    fixed = 0
    skipped = 0
    for d in files:
        idx = d / "index.html"
        ok, msg = fix_file(idx)
        marker = "FIXED" if ok else "SKIP "
        if ok:
            fixed += 1
        else:
            skipped += 1
        print(f"  {marker} {d.name}: {msg}")
    print(f"\nSummary: {fixed} fixed, {skipped} skipped, {len(files)} total")


if __name__ == "__main__":
    main()
