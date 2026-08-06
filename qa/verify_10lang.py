"""Verify P0-1 fully: For each lang JSON, how many of HTML's 6436 keys are present?"""
import re
import json
from pathlib import Path

ROOT = Path('.')
EXCLUDE = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}

files = [p for p in ROOT.rglob('*.html') if not (set(str(x) for x in p.parts) & EXCLUDE)]
all_html_keys = set()
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    all_html_keys.update(re.findall(r'data-i18n="([^"]+)"', text))

LANGS = ['en', 'zh', 'es', 'fr', 'de', 'pt', 'ja', 'ru', 'ar', 'th']
print(f'HTML unique keys: {len(all_html_keys)}\n')
for lang in LANGS:
    d = json.load(open(f'i18n/{lang}.json', encoding='utf-8'))
    keys = set(d.keys())
    matched = all_html_keys & keys
    missing = all_html_keys - keys
    print(f'{lang}: {len(matched):4d} / {len(all_html_keys):4d} keys present, {len(missing):3d} missing')
    if missing:
        for k in list(missing)[:3]:
            print(f'  missing: {k}')
