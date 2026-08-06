#!/usr/bin/env python3
"""
P0-1: Migrate HTML data-i18n keys from old `blog.NN-<slug>.X.Y` format
to new `blog.<slug>.X.Y` format.

en.json already uses the new format (canonical). The 4113 old keys in
HTML are leftover from the blog rename (01-* → semantic-slug) — see
_redirects lines 143-189 for the matching 301 redirects.

Algorithm:
  1. For each HTML file, find data-i18n keys matching `blog.NN-<slug>.X.Y`.
  2. Strip the `NN-` prefix to get `blog.<slug>.X.Y`.
  3. If the new key exists in en.json, replace the old key in HTML.
  4. If new key is NOT in en.json, log as "broken rename" (shouldn't happen
     if the rename map is consistent).

Safety:
  - Backup all modified files to tmp/key-migration-backup/<file>.bak
  - Report stats (X keys renamed, Y files touched, Z unresolved)
"""
import json
import re
from pathlib import Path
import shutil

ROOT = Path('.')
EXCLUDE = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}

# Load en.json (canonical key set)
en = json.load(open('i18n/en.json', encoding='utf-8'))
en_keys = set(en.keys())

# Backup directory
backup_dir = ROOT / 'tmp' / 'key-migration-backup'
backup_dir.mkdir(parents=True, exist_ok=True)

OLD_RE = re.compile(r'\bblog\.(\d{2})-([a-z0-9-]+)\.')

# Find HTML files
files = [p for p in ROOT.rglob('*.html') if not (set(str(x) for x in p.parts) & EXCLUDE)]
print(f'Scanning {len(files)} HTML files')

total_renamed = 0
total_unresolved = 0
files_touched = 0
unresolved_samples = []

for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    # Find all old-format keys in this file
    old_keys = set()
    for m in re.finditer(r'data-i18n="([^"]+)"', text):
        k = m.group(1)
        if OLD_RE.match(k):
            old_keys.add(k)
    if not old_keys:
        continue

    # Compute new keys
    rename_map = {}
    for old in old_keys:
        new = OLD_RE.sub(r'blog.\2.', old)
        rename_map[old] = new

    # Validate new keys exist in en.json
    unresolved = {old: new for old, new in rename_map.items() if new not in en_keys}
    if unresolved:
        total_unresolved += len(unresolved)
        for old, new in list(unresolved.items())[:3]:
            unresolved_samples.append((str(f.relative_to(ROOT)), old, new))

    # Apply rename (only when new key exists in en.json — leave unresolved for human review)
    new_text = text
    for old, new in rename_map.items():
        if old == new:
            continue
        if new not in en_keys:
            continue  # skip unresolved
        new_text = new_text.replace(f'data-i18n="{old}"', f'data-i18n="{new}"')

    if new_text != text:
        # Backup original
        backup_path = backup_dir / f'{f.relative_to(ROOT)}.bak'
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        if not backup_path.exists():
            shutil.copy2(f, backup_path)
        f.write_text(new_text, encoding='utf-8')
        files_touched += 1
        # Count actual renames in this file
        for old in old_keys:
            if rename_map[old] in en_keys:
                total_renamed += text.count(f'data-i18n="{old}"')

print(f'\n=== Results ===')
print(f'Files touched: {files_touched}')
print(f'Keys renamed (occurrences): {total_renamed}')
print(f'Unresolved (old key has no matching new key in en.json): {total_unresolved}')
if unresolved_samples:
    print(f'\nSample unresolved (first 10):')
    for path, old, new in unresolved_samples[:10]:
        print(f'  {path}')
        print(f'    old: {old}')
        print(f'    new (not in en.json): {new}')
print(f'\nBackup: {backup_dir}')
