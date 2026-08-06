import json
en = json.loads(open('i18n/en.json', encoding='utf-8').read())
key = 'order.p_text.we_ll_respond_within_24_hours_check_your.67979247'
print('EN:', en[key])
for lang in ['zh', 'ja', 'es', 'fr', 'de', 'pt', 'ru', 'ar', 'th']:
    d = json.loads(open(f'i18n/{lang}.json', encoding='utf-8').read())
    val = d.get(key, 'MISSING')
    print(f'{lang}: {val}')
