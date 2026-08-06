#!/usr/bin/env python3
"""
Fix broken local hrefs that point to blog posts.
The blog posts are at /blog/NN-slug/ but links often omit the NN- prefix.
"""
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
BLOG_DIR = ROOT / "blog"

def build_slug_index():
    """Build {slug: actual_path} for all blog posts."""
    idx = {}
    if not BLOG_DIR.exists():
        return idx
    for d in BLOG_DIR.iterdir():
        if d.is_dir() and re.match(r"^\d{2}-", d.name):
            # Strip numeric prefix
            slug = re.sub(r"^\d{2}-", "", d.name)
            idx[slug] = d.name
    return idx

def fix_text(text: str, slug_index: dict) -> str:
    """Replace /blog/SLUG/ with /blog/NN-SLUG/ if SLUG exists with prefix."""
    def repl(m):
        prefix, slug = m.group(1), m.group(2)
        if slug in slug_index:
            return f'href="{prefix}{slug_index[slug]}/"'
        return m.group(0)
    return re.sub(r'href="(/blog/)([^"/]+)/?"', repl, text)

def main(dry_run: bool = False):
    slug_index = build_slug_index()
    print(f"Indexed {len(slug_index)} blog slugs")
    total = 0
    for p in sorted(ROOT.rglob("*.html")):
        if not p.is_relative_to(BLOG_DIR) and "blog" not in p.parts:
            continue
        text = p.read_text(encoding='utf-8', errors='ignore')
        new_text = fix_text(text, slug_index)
        if new_text != text:
            n = text.count('/blog/')  # rough
            if not dry_run:
                p.write_text(new_text, encoding='utf-8')
            print(f"  {p.relative_to(ROOT)}")
            total += 1
    print(f"\nTotal: {total} files updated")

if __name__ == '__main__':
    dry = '--dry' in sys.argv
    main(dry_run=dry)
