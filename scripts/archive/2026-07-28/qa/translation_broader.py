#!/usr/bin/env python3
"""
Broader translation audit - check for common machine translation issues
across all keys for non-English languages.
"""
import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path(r'C:\Users\qiaoshan\.openclaw\workspace\weddingai')
LANGS = ['zh', 'es', 'fr', 'de', 'pt', 'ja', 'ru', 'ar', 'th']

# Markers that suggest bad translation
SUSPICIOUS_PATTERNS = [
    (r'\[object Object\]', 'OBJECT_OBJECT'),
    (r'\bundefined\b', 'UNDEFINED'),
    (r'\bnull\b', 'NULL'),
    (r'TODO', 'TODO'),
    (r'FIXME', 'FIXME'),
    (r'XXX+', 'XXX'),
    (r'^\s*$', 'EMPTY'),
    (r'^\s*\.{3,}\s*$', 'ELLIPSIS_ONLY'),
    (r'\[.+?\]\(.+?\)', 'MD_LINK'),
    (r'&lt;|<[a-z/]+>|&gt;', 'HTML_ESCAPE'),
    (r'^[a-z_]+ \d+$', 'KEY_LEAK'),
    (r'\{\{|\}\}', 'TEMPLATE_VAR'),
    (r'\\n', 'NEWLINE_ESCAPE'),
    (r'\\t', 'TAB_ESCAPE'),
    (r'\\"', 'QUOTE_ESCAPE'),
    (r'\\u[0-9a-f]{4}', 'UNICODE_ESCAPE'),
]

def is_untranslated(value, en_value):
    """Check if value is essentially same as English."""
    if not value or not en_value:
        return False
    # Exact match
    if value.strip() == en_value.strip():
        return True
    # Mostly same (low Levenshtein-like check)
    if len(value) < 20 and len(en_value) < 20 and value.lower() == en_value.lower():
        return True
    return False

def audit_lang(lang):
    en = json.loads((ROOT / 'i18n' / 'en.json').read_text(encoding='utf-8'))
    data = json.loads((ROOT / 'i18n' / f'{lang}.json').read_text(encoding='utf-8'))

    findings = Counter()
    samples = {}

    for key, value in data.items():
        en_value = en.get(key, '')
        # Skip meta
        if key.startswith('_meta'):
            continue
        # Suspicious patterns
        for pat, name in SUSPICIOUS_PATTERNS:
            if re.search(pat, value):
                findings[name] += 1
                if name not in samples:
                    samples[name] = (key, value[:80])

        # Same as English (untranslated)
        if is_untranslated(value, en_value):
            findings['UNTRANSLATED'] += 1
            if 'UNTRANSLATED' not in samples:
                samples['UNTRANSLATED'] = (key, value[:80])

        # Empty
        if not value or not value.strip():
            findings['EMPTY'] += 1
            if 'EMPTY' not in samples:
                samples['EMPTY'] = (key, value)

    return findings, samples

for lang in LANGS:
    findings, samples = audit_lang(lang)
    if not findings:
        print(f'{lang}: clean ✓')
        continue
    print(f'\n{lang}:')
    for name, count in findings.most_common():
        key, val = samples[name]
        print(f'  {name:18s} {count:4d}  e.g. [{key}] {val!r}')
