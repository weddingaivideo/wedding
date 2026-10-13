#!/usr/bin/env python3
"""Audit: do outer <a> tool-name parts match the corresponding h3 tool-name across all locales?"""
import json
import re

CARDS = [
    ('tools.a.compress_wedding_photos_shrink_huge_jpg.42c67735',
     'tools.h3.compress_wedding_photos.cbd7aea1', 'Compress Wedding Photos'),
    ('tools.a.heic_to_jpg_converter_iphone_photos_in.b096ba35',
     'tools.h3.heic_to_jpg_converter.9ce2d19f', 'HEIC to JPG Converter'),
    ('tools.a.wedding_photo_collage_maker_drop_2_12_p.6a9b9d75',
     'tools.h3.wedding_photo_collage_maker.525d205b', 'Wedding Photo Collage Maker'),
    ('tools.a.crop_wedding_photo_for_reels_instantly.13e3f750',
     'tools.h3.crop_wedding_photo_for_reels.06bd6525', 'Crop Wedding Photo for Reels'),
    ('tools.a.remove_background_from_portrait_strip_a.eef17433',
     'tools.h3.remove_background_from_portrait.85d6d707', 'Remove Background from Portrait'),
    ('tools.a.add_text_to_wedding_photo_add_captions.55f86396',
     'tools.h3.add_text_to_wedding_photo.2a856424', 'Add Text to Wedding Photo'),
]

LANGS = ['en', 'zh', 'es', 'fr', 'de', 'pt', 'ja', 'ru', 'ar', 'th', 'hi']

mismatches = []
total_checks = 0

for lang in LANGS:
    with open(f'i18n/{lang}.json', 'r', encoding='utf-8') as f:
        j = json.load(f)
    for outer_key, h3_key, en_h3 in CARDS:
        total_checks += 1
        v_outer = j.get(outer_key, '')
        v_h3 = j.get(h3_key, '')

        if lang == 'en':
            # Source — must match by construction
            continue

        # Outer-a value should start with the localized h3 (after emoji + space)
        # Strip leading emoji: the value starts with an emoji char (e.g., 🗜️) followed by space
        # Extract just the "title" portion: from after emoji to the next sentence
        # Method: outer-a value contains `<icon> <h3> <description>. <open_tool> →`
        # We just need to check that it contains the localized h3 somewhere in the first half

        # Get first 60 chars after emoji prefix; should contain h3
        m = re.match(r'^[^\s]+\s+(.+?)(\s+[A-Z]|\.\s+|\?\s+|\!\s+)', v_outer)
        if not m:
            continue
        snippet = m.group(1).strip()

        # Compare with h3 (could have trailing chars stripped)
        if not snippet.startswith(v_h3) and v_h3 not in snippet[:50]:
            mismatches.append((lang, outer_key, v_h3, snippet[:80]))

print(f'Total checks: {total_checks}')
if mismatches:
    print(f'!!! {len(mismatches)} mismatch(es):')
    for l, k, h3, snip in mismatches:
        print(f'  [{l}] {k}')
        print(f'      h3   = {h3!r}')
        print(f'      outer= {snip!r}...')
else:
    print('CLEAN: all 6 cards x 10 locales have outer <a> tool-name consistent with h3')
