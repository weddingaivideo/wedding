"""Fix two cross-file HTML bugs:
1. canonical href has trailing extra double-quote: href="URL"">  →  href="URL">
2. footer privacy/terms links use relative path ../../privacy  →  /privacy/
"""
import os
import re

ROOT = r'C:\Users\qiaoshan\.openclaw\workspace\weddingai'

CANON_RE = re.compile(r'(<link rel="canonical" href="https://weddingai\.video/[^"]+")">')
RELPATH_RE = re.compile(r'href="\.\./\.\./(privacy|terms)"')

def fix_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    original = text
    n_canon = 0
    n_relpath = 0
    # Fix 1: canonical double-quote
    def canon_sub(m):
        return m.group(1) + '>'
    text, n_canon = CANON_RE.subn(canon_sub, text)
    # Fix 2: relative privacy/terms → absolute
    def relpath_sub(m):
        return f'href="/{m.group(1)}/"'
    text, n_relpath = RELPATH_RE.subn(relpath_sub, text)
    if text != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
    return n_canon, n_relpath

def main():
    total_canon = 0
    total_relpath = 0
    files_fixed = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # Skip tmp, node_modules
        dirnames[:] = [d for d in dirnames if d not in ('tmp', 'node_modules', '.git', 'functions')]
        for fn in filenames:
            if not fn.endswith('.html'):
                continue
            path = os.path.join(dirpath, fn)
            n_canon, n_relpath = fix_file(path)
            if n_canon or n_relpath:
                relpath = os.path.relpath(path, ROOT)
                print(f'  {relpath}: canon={n_canon} relpath={n_relpath}')
                total_canon += n_canon
                total_relpath += n_relpath
                files_fixed.append(relpath)
    print(f'\nTotal: {len(files_fixed)} files, {total_canon} canonical, {total_relpath} relpath')

if __name__ == '__main__':
    main()
