#!/usr/bin/env python3
"""
Translation quality audit: sample high-impact keys across all 9 languages.
Check for:
 - Same as English (untranslated)
 - Empty / whitespace only
 - Way too long (>3x English)
 - Way too short (<0.3x English)
 - Contains suspicious markers (TODO, FIXME, undefined, [object Object], etc.)
 - HTML entities / tags leaking
"""
import json
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(r'C:\Users\qiaoshan\.openclaw\workspace\weddingai')
LANGS = ['en', 'zh', 'es', 'fr', 'de', 'pt', 'ja', 'ru', 'ar', 'th']

# High-impact keys (visible on landing page, order form, navigation)
HIGH_IMPACT = [
    'index.h1_text.make_every_wedding_moment_unforgettable.26538929',
    'index.h2_text.everything_you_need_for_the_perfect_wedd.47351285',
    'index.a_text.get_a_free_quote.53673839',
    'index.a_text.explore_our_services.49519743',
    'index.a_text.learn_more.12869768',
    'order.h1_text.get_your_free_wedding_video_quote.93480914',
    'order.h2_text.free_no_obligation_quote.86642841',
    'order.h2_text.24_hour_response.50138433',
    'order.h2_text.100_satisfaction.60111635',
    'order.input_placeholder.e_g_sarah_johnson.45211033',
    'order.label_text.how_did_you_find_us.35777558',
    '404.a_text.services.84864121',
    '404.a_text.gallery.96646935',
    '404.a_text.blog.95723762',
    '404.a_text.about.69447212',
    '404.a_text.get_a_quote.03314957',
    '404.a_text.skip_to_main_content.85143743',
    'index.h2_text.ready_to_get_started.57000224',
    'index.h2_text.what_couples_are_saying.46757273',
    'order.p_text.we_ll_respond_within_24_hours_check_your.67979247',
    'order.h2_text.transparent_pricing.59026430',
    'order.h2_text.what_happens_after_you_submit.08255829',
    '404.h3_text.contact.47569808',
    '404.h3_text.company.16024258',
]

def audit_translation(value, en_value):
    issues = []
    if not value or not value.strip():
        issues.append('EMPTY')
    if value == en_value:
        issues.append('UNTRANSLATED')
    if len(value) > len(en_value) * 3.5 and len(en_value) > 5:
        issues.append(f'TOO_LONG ({len(value)} vs {len(en_value)})')
    if len(value) < len(en_value) * 0.3 and len(en_value) > 10:
        issues.append(f'TOO_SHORT ({len(value)} vs {len(en_value)})')
    if re.search(r'\[object Object\]|undefined|\{\{|\}\}|TODO|FIXME|XXX', value):
        issues.append('PLACEHOLDER_LEAK')
    if re.search(r'<[a-z]+[^>]*>|<\\|>', value):
        issues.append('HTML_LEAK')
    return issues

def main():
    en = json.loads((ROOT / 'i18n' / 'en.json').read_text(encoding='utf-8'))
    langs_data = {}
    for lang in LANGS:
        path = ROOT / 'i18n' / f'{lang}.json'
        if path.exists():
            langs_data[lang] = json.loads(path.read_text(encoding='utf-8'))

    print(f'High-impact translation audit ({len(HIGH_IMPACT)} keys × {len(LANGS)} langs)\n')

    for key in HIGH_IMPACT:
        if key not in en:
            continue
        en_value = en[key]
        print(f'EN [{key}]: {en_value[:80]}')
        all_ok = True
        for lang in LANGS:
            if lang == 'en':
                continue
            if lang not in langs_data:
                print(f'  {lang}: MISSING FILE')
                all_ok = False
                continue
            value = langs_data[lang].get(key, '')
            issues = audit_translation(value, en_value)
            if issues:
                print(f'  ⚠ {lang}: {value[:60]!r}  — {issues}')
                all_ok = False
        if all_ok:
            print('  ✓ All langs OK')
        print()

if __name__ == '__main__':
    main()
