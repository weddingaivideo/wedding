"""P3-1: Remove dead i18n keys from all 10 language JSON files.

'Dead' = key exists in en.json but no HTML data-i18n attribute references it.

Caution: 10 lang files have the SAME key set (verified in earlier scan).
Removing a dead key from all 10 keeps the sets aligned.

Safety:
  - Backup each JSON before editing
  - Verify post-write that all HTML-referenced keys still present
  - Verify all 10 langs still have identical key sets
"""
import json
import re
import shutil
from pathlib import Path

ROOT = Path('.')
LANGS = ['en', 'zh', 'es', 'fr', 'de', 'pt', 'ja', 'ru', 'ar', 'th']

# Collect all HTML data-i18n keys
EXCLUDE = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}
files = [p for p in ROOT.rglob('*.html') if not (set(str(x) for x in p.parts) & EXCLUDE)]
all_html_keys = set()
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    all_html_keys.update(re.findall(r'data-i18n="([^"]+)"', text))

print(f'HTML unique keys: {len(all_html_keys)}')

# Backup + read each lang JSON
backup = ROOT / 'tmp' / 'dead-keys-cleanup-backup'
backup.mkdir(parents=True, exist_ok=True)

lang_dicts = {}
for lang in LANGS:
    p = ROOT / 'i18n' / f'{lang}.json'
    bp = backup / f'{lang}.json.bak'
    if not bp.exists():
        shutil.copy2(p, bp)
    lang_dicts[lang] = json.loads(p.read_text(encoding='utf-8'))

# Find dead keys (in en.json but not in HTML)
en = lang_dicts['en']
dead_keys = set(en.keys()) - all_html_keys
print(f'Dead keys (in en.json, not in HTML): {len(dead_keys)}')

# Cross-check: same dead keys in all langs?
for lang in LANGS:
    d = lang_dicts[lang]
    lang_dead = set(d.keys()) - all_html_keys
    if lang_dead != dead_keys:
        print(f'WARNING: {lang} has different dead key set! diff={lang_dead - dead_keys} extra={dead_keys - lang_dead}')

# Sample dead keys
print('\nSample dead keys (first 10):')
for k in list(dead_keys)[:10]:
    print(f'  {k}: en={en[k]!r}')

# Remove from all 10 langs
removed = 0
for lang in LANGS:
    p = ROOT / 'i18n' / f'{lang}.json'
    d = lang_dicts[lang]
    before = len(d)
    for k in dead_keys:
        d.pop(k, None)
    after = len(d)
    removed += (before - after)
    # Write back
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')

print(f'\nRemoved {removed} keys across {len(LANGS)} files (avg {removed // len(LANGS)} per file)')

# Verify: post-write checks
print('\n=== Post-write verification ===')
all_lang_sets = {}
for lang in LANGS:
    d = json.loads((ROOT / 'i18n' / f'{lang}.json').read_text(encoding='utf-8'))
    all_lang_sets[lang] = set(d.keys())
    print(f'{lang}: {len(d)} keys')

# All 10 langs have identical key sets
ref = all_lang_sets['en']
for lang in LANGS:
    if all_lang_sets[lang] != ref:
        diff = all_lang_sets[lang] - ref
        print(f'  WARNING: {lang} differs from en by {len(diff)} keys')
    else:
        pass  # OK

# All HTML keys still present
final = json.loads((ROOT / 'i18n' / 'en.json').read_text(encoding='utf-8'))
final_keys = set(final.keys())
missing = all_html_keys - final_keys
print(f'\nHTML keys still in en.json: {len(all_html_keys & final_keys)} / {len(all_html_keys)}')
if missing:
    print(f'WARNING: {len(missing)} HTML keys missing after cleanup!')
    for k in list(missing)[:5]:
        print(f'  - {k}')

print(f'\nBackup: {backup}')
