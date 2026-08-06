#!/usr/bin/env python3
"""
Smarter translation audit: filter out known non-translatable items
(brand names, tech terms, emails, person names) and focus on real issues.
"""
import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path(r'C:\Users\qiaoshan\.openclaw\workspace\weddingai')
LANGS = ['zh', 'es', 'fr', 'de', 'pt', 'ja', 'ru', 'ar', 'th']

# Patterns that should NOT be translated
NON_TRANSLATABLE_PATTERNS = [
    r'@',  # email
    r'https?://',  # URL
    r'\.com|\.video|\.html',
    r'^\d+$',  # pure number
    r'^[A-Z][a-z]+ [A-Z][a-z]+$',  # person name
    r'WeddingAI',
    r'MP[34]|H\.?26[45]|HEVC|ProRes|MOV|AVI|MKV|JPG|PNG|WEBP|AVIF',
    r'VHS|DV|Hi8|MiniDVD|8mm|16mm',
    r'US|USA|UK|CA|AU|DE|FR|ES|IT|IN|CN|JP',
    r'USD|EUR|GBP|CNY|JPY|RUB|THB|AED',
    r'\$\d|\d+%|24-Hour|24 ?hours?',
    r'FAQ|AI|TikTok|Instagram|YouTube|Google|Stripe|PayPal|Resend|Product Hunt',
    r'^https?:',
]

def is_untranslatable(value):
    if not value: return True
    for pat in NON_TRANSLATABLE_PATTERNS:
        if re.search(pat, value):
            return True
    return False

def is_untranslated(value, en_value):
    """Check if value is essentially same as English (and was supposed to be translated)."""
    if not value or not en_value: return False
    # Exact match
    if value.strip().lower() == en_value.strip().lower():
        return True
    return False

def audit_lang(lang):
    en = json.loads((ROOT / 'i18n' / 'en.json').read_text(encoding='utf-8'))
    data = json.loads((ROOT / 'i18n' / f'{lang}.json').read_text(encoding='utf-8'))

    findings = Counter()
    samples = {}

    for key, value in data.items():
        if key.startswith('_meta'):
            continue
        en_value = en.get(key, '')

        # Skip non-translatable
        if is_untranslatable(value) or is_untranslatable(en_value):
            continue

        # Check if untranslated
        if is_untranslated(value, en_value):
            findings['UNTRANSLATED'] += 1
            if 'UNTRANSLATED' not in samples:
                samples['UNTRANSLATED'] = (key, value[:80])
            continue

        # Check for placeholder leaks
        if re.search(r'\[object Object\]|undefined|\{\{|\}\}|TODO', value):
            findings['PLACEHOLDER'] += 1
            if 'PLACEHOLDER' not in samples:
                samples['PLACEHOLDER'] = (key, value[:80])

    return findings, samples

for lang in LANGS:
    findings, samples = audit_lang(lang)
    if not findings:
        print(f'{lang}: ✓ clean')
        continue
    print(f'\n{lang}:')
    for name, count in findings.most_common():
        key, val = samples[name]
        print(f'  {name:18s} {count:4d}  e.g. [{key}] {val!r}')
