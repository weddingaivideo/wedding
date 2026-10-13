#!/usr/bin/env python3
"""Fix 5 zh cards: trailing 'Open tool →' → localized '打开工具 →'.
The middleware replaces the outer <a> inner with dict[key], so any untranslated
text in the JSON shows as English on the localized page.

Also: any other locale with a leaked 'Open tool' at the END of the value is
auto-corrected using the proper i18n key for that locale.
"""
import json
import re

LANGS = ['zh', 'es', 'fr', 'de', 'pt', 'ja', 'ru', 'ar', 'th', 'hi']

# 6 outer <a> keys per card
CARD_KEYS = [
    'tools.a.compress_wedding_photos_shrink_huge_jpg.42c67735',
    'tools.a.heic_to_jpg_converter_iphone_photos_in.b096ba35',
    'tools.a.wedding_photo_collage_maker_drop_2_12_p.6a9b9d75',
    'tools.a.crop_wedding_photo_for_reels_instantly.13e3f750',
    'tools.a.remove_background_from_portrait_strip_a.eef17433',
    'tools.a.add_text_to_wedding_photo_add_captions.55f86396',
]

# The localized "Open tool →" per locale (from tools.span.open_tool.031465d0)
OPEN_TOOL_BY_LANG = {}
for lang in LANGS:
    with open(f'i18n/{lang}.json', 'r', encoding='utf-8') as f:
        j = json.load(f)
    OPEN_TOOL_BY_LANG[lang] = j['tools.span.open_tool.031465d0']
    print(f'  {lang} open_tool = {OPEN_TOOL_BY_LANG[lang]!r}')

print()
print('=== Fixing outer <a> trailing " Open tool →" leaks ===')

total_fixed = 0

for lang in LANGS:
    path = f'i18n/{lang}.json'
    with open(path, 'r', encoding='utf-8') as f:
        j = json.load(f)

    proper_open = OPEN_TOOL_BY_LANG[lang]
    changed = 0
    for k in CARD_KEYS:
        v = j.get(k, '')
        if not v:
            continue
        # If value doesn't already end in the proper localized open_tool → skip
        if v.endswith(proper_open):
            continue
        # If value ends in some English "Open tool →" (with optional leading space) → replace
        # Be specific to avoid false positives; English form = "Open tool →"
        new_v = re.sub(r'(\s*)Open tool\s*→\s*$', lambda m: m.group(1) + proper_open, v)
        if new_v != v:
            print(f'  [{lang}] {k}')
            print(f'    BEFORE: ...{v[-50:]!r}')
            print(f'    AFTER : ...{new_v[-50:]!r}')
            j[k] = new_v
            changed += 1

    if changed:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(j, f, ensure_ascii=False, indent=2)
            f.write('\n')
        total_fixed += changed
        print(f'  → {lang}: {changed} card(s) fixed and saved')

print()
print(f'TOTAL: {total_fixed} card translation(s) fixed across all locales')
