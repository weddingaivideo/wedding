"""Verify: P0-1 fixed. Recheck key coverage."""
import re
import json
from pathlib import Path

ROOT = Path('.')
en = json.load(open('i18n/en.json', encoding='utf-8'))
en_keys = set(en.keys())
EXCLUDE = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}

files = [p for p in ROOT.rglob('*.html') if not (set(str(x) for x in p.parts) & EXCLUDE)]
all_html_keys = set()
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    all_html_keys.update(re.findall(r'data-i18n="([^"]+)"', text))

print(f'HTML unique keys: {len(all_html_keys)}')
print(f'en.json keys: {len(en_keys)}')
inter = all_html_keys & en_keys
print(f'Intersection: {len(inter)}')
print(f'In HTML only: {len(all_html_keys - en_keys)}')
print(f'In en.json only: {len(en_keys - all_html_keys)}')

# What 4xxx en.json keys aren't in HTML? Are they all reasonable?
unmatched = en_keys - all_html_keys
print(f'\nUnmatched en.json keys (in JSON but not in HTML): {len(unmatched)}')
# Sample
for k in list(unmatched)[:5]:
    print(f'  {k}')

# What HTML keys are unmatched?
html_only = all_html_keys - en_keys
print(f'\nHTML-only keys: {len(html_only)}')
for k in list(html_only)[:5]:
    print(f'  {k}')
