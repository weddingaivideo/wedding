"""Remove the 2 leftover keys (_meta, index.p_text.the_real_time_editing_at_our_reception.87089643)
from the 9 non-en JSON files. They exist in zh/es/fr/de/pt/ja/ru/ar/th but not in en.json or HTML.
"""
import json
from pathlib import Path

ROOT = Path('.')
LANGS = ['zh', 'es', 'fr', 'de', 'pt', 'ja', 'ru', 'ar', 'th']

LEFTOVER = {'_meta', 'index.p_text.the_real_time_editing_at_our_reception.87089643'}

for lang in LANGS:
    p = ROOT / 'i18n' / f'{lang}.json'
    d = json.loads(p.read_text(encoding='utf-8'))
    before = len(d)
    removed_any = False
    for k in LEFTOVER:
        if k in d:
            del d[k]
            removed_any = True
    after = len(d)
    if removed_any:
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'{lang}: removed {before - after} keys, now {after} keys')

# Final verification
print('\n=== Post-cleanup verification ===')
en = json.loads((ROOT / 'i18n' / 'en.json').read_text(encoding='utf-8'))
en_keys = set(en.keys())
for lang in ['en'] + LANGS:
    d = json.loads((ROOT / 'i18n' / f'{lang}.json').read_text(encoding='utf-8'))
    print(f'{lang}: {len(d)} keys, match-en: {set(d.keys()) == en_keys}')
