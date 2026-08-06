import json
en = json.loads(open('i18n/en.json', encoding='utf-8').read())
miss = '?'
for lang in ['zh', 'es', 'fr', 'de', 'pt', 'ja', 'ru', 'ar', 'th']:
    d = json.loads(open(f'i18n/{lang}.json', encoding='utf-8').read())
    print(f'\n=== {lang} ===')
    keys = [k for k in en if k.startswith('order.h1_') or k.startswith('order.h2_') or k.startswith('order.p_text')][:5]
    for k in keys:
        v = d.get(k, miss)
        print(f'  EN: {en[k][:60]}')
        print(f'  {lang}: {v[:60]}')
