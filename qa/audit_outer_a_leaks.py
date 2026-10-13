#!/usr/bin/env python3
"""Audit the 6 outer <a> data-i18n keys across all 11 locales for English leaks in the LAST line of the value."""
import json
import re

CARD_KEYS = [
    'tools.a.compress_wedding_photos_shrink_huge_jpg.42c67735',
    'tools.a.heic_to_jpg_converter_iphone_photos_in.b096ba35',
    'tools.a.wedding_photo_collage_maker_drop_2_12_p.6a9b9d75',
    'tools.a.crop_wedding_photo_for_reels_instantly.13e3f750',
    'tools.a.remove_background_from_portrait_strip_a.eef17433',
    'tools.a.add_text_to_wedding_photo_add_captions.55f86396',
]

LANGS = ['en', 'zh', 'es', 'fr', 'de', 'pt', 'ja', 'ru', 'ar', 'th', 'hi']

# Common English-only words that should NEVER appear in localized card text
EN_LEAK_PATTERNS = [
    r'\bOpen tool\b',
    r'\bCompress Wedding Photos\b',
    r'\bHEIC to JPG\b',
    r'\bWedding Photo Collage\b',
    r'\bCrop Wedding Photo\b',
    r'\bRemove Background\b',
    r'\bAdd Text\b',
    r'\bShrink huge JPGs\b',
    r'\biPhone photos in HEIC\b',
    r'\bDrop 2.12 photos\b',
    r'\bInstantly crop\b',
    r'\bStrip a clean studio\b',
    r'\bAdd captions, dates\b',
    r'\bAll bytes remain\b',
    r'\bhanding off to your videographer\b',
    r'\bbreak wedding albums\b',
    r'\bsave.the.date\b',
    r'\bsmart center.weighted framing\b',
]

LEAK_INDEX = {}

for lang in LANGS:
    with open(f'i18n/{lang}.json', 'r', encoding='utf-8') as f:
        j = json.load(f)
    for k in CARD_KEYS:
        v = j.get(k, '')
        if not v:
            continue
        # Find which EN leak tokens are present
        found = []
        for p in EN_LEAK_PATTERNS:
            if re.search(p, v, re.IGNORECASE):
                found.append(p)
        if found:
            LEAK_INDEX.setdefault(lang, []).append((k, found, v[-80:]))
            print(f'  [{lang}] {k}')
            for f in found:
                print(f'    LEAK: {f}')
            print(f'    tail: ...{v[-80:]!r}')
            print()

if not LEAK_INDEX:
    print('CLEAN: no leaked English in any outer <a> card value.')
else:
    print(f'TOTAL localizations with leaks: {len(LEAK_INDEX)}')
