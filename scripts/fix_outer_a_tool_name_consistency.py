#!/usr/bin/env python3
"""Reconcile outer <a data-i18n> values with the localized h3 text.

The middleware replaces the entire inner of <a> with dict[key], so the
'inner' content visible to the user is the FULL outer-a value: icon + h3 text
+ p text + open_tool span.

The 6 card h3 keys are individually translated, but the 6 corresponding
outer-a keys sometimes contain English tool-name loanwords (kept by
Google Translate as proper nouns). This creates the visible inconsistency:

  Rendered de card:
    <a ...>🗜️ Wedding Photo Collage Maker Legen Sie 2–12 Fotos ab...
       (should be: 🗜️ Hochzeitsfoto-Collagen-Ersteller Legen Sie 2–12 Fotos ab...)

  But the inner <h3>Hochzeitsfoto-Collagen-Ersteller</h3> is stripped,
  so the user sees the loanword form in the body.

Fix: for each card, locate the English tool-name substring at the start
of the value (right after emoji icon) and replace it with the localized h3
text.
"""
import json
import re

CARDS = [
    # (outer_a_key, h3_key, en_h3_text)
    ('tools.a.compress_wedding_photos_shrink_huge_jpg.42c67735',
     'tools.h3.compress_wedding_photos.cbd7aea1',
     'Compress Wedding Photos'),
    ('tools.a.heic_to_jpg_converter_iphone_photos_in.b096ba35',
     'tools.h3.heic_to_jpg_converter.9ce2d19f',
     'HEIC to JPG Converter'),
    ('tools.a.wedding_photo_collage_maker_drop_2_12_p.6a9b9d75',
     'tools.h3.wedding_photo_collage_maker.525d205b',
     'Wedding Photo Collage Maker'),
    ('tools.a.crop_wedding_photo_for_reels_instantly.13e3f750',
     'tools.h3.crop_wedding_photo_for_reels.06bd6525',
     'Crop Wedding Photo for Reels'),
    ('tools.a.remove_background_from_portrait_strip_a.eef17433',
     'tools.h3.remove_background_from_portrait.85d6d707',
     'Remove Background from Portrait'),
    ('tools.a.add_text_to_wedding_photo_add_captions.55f86396',
     'tools.h3.add_text_to_wedding_photo.2a856424',
     'Add Text to Wedding Photo'),
]

LANGS = ['zh', 'es', 'fr', 'de', 'pt', 'ja', 'ru', 'ar', 'th', 'hi']

# Order matters — most specific to least
EN_H3_TO_LOCAL_H3 = {}
for lang in LANGS:
    with open(f'i18n/{lang}.json', 'r', encoding='utf-8') as f:
        j = json.load(f)
    EN_H3_TO_LOCAL_H3[lang] = {en: j[h3] for _, h3, en in CARDS if h3 in j}

# Quick sanity print
print('=== Per-locale h3 map ===')
for lang in LANGS:
    print(f'  [{lang}] {len(EN_H3_TO_LOCAL_H3[lang])}/6 h3 localized')
    for en, loc in EN_H3_TO_LOCAL_H3[lang].items():
        if loc != en:
            print(f'    {en!r:40s} → {loc!r}')

print()
total = 0
for lang in LANGS:
    path = f'i18n/{lang}.json'
    with open(path, 'r', encoding='utf-8') as f:
        j = json.load(f)

    n = 0
    for outer_key, h3_key, en_h3 in CARDS:
        v = j.get(outer_key, '')
        if not v:
            continue
        target_h3 = EN_H3_TO_LOCAL_H3[lang][en_h3]
        # If the value already contains the localized h3 (just got translated
        # correctly), skip; but the en_h3 might still be present as loanword.
        # We want to replace en_h3 with target_h3 ONLY at the start (after
        # any emoji prefix).
        # Locate: after optional emoji icon + space, the en_h3 should appear.

        # Build a regex: "^(prefix)(en_h3)$" — find prefix by skipping leading
        # emoji + whitespace.
        # Use a simple approach: try to replace the FIRST occurrence of
        # en_h3 anywhere, but only if it's not already followed by another
        # alphabetic character (loansword pattern).

        # More robust: split on the FIRST occurrence of en_h3, replace it
        idx = v.find(en_h3)
        if idx < 0:
            # Already has localized version
            continue

        new_v = v[:idx] + target_h3 + v[idx + len(en_h3):]
        if new_v != v:
            j[outer_key] = new_v
            n += 1
            print(f'  [{lang}] {outer_key}')
            print(f'    before: {v[:80]!r}...')
            print(f'    after : {new_v[:80]!r}...')
            print()

    if n:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(j, f, ensure_ascii=False, indent=2)
            f.write('\n')
        total += n
        print(f'  → {lang}: {n} card(s) updated\n')

print(f'TOTAL: {total} card(s) updated across all locales')
