import json
en = json.loads(open('i18n/en.json', encoding='utf-8').read())
for lang in ['zh', 'es', 'fr', 'de', 'pt', 'ja', 'ru', 'ar', 'th']:
    d = json.loads(open(f'i18n/{lang}.json', encoding='utf-8').read())
    print(f'\n=== {lang} ===')
    keys = [k for k in en if 'order.label_text' in k or 'order.input_placeholder' in k or 'order.button_text' in k][:10]
    for k in keys:
        v = d.get(k, '?')
        en_v = en[k]
        print(f'  [{k.split(".")[-1][:30]}] {en_v[:50]} -> {v[:50]}')
