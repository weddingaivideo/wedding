"""Inspect the 360 empty-default data-i18n elements.
Show distribution: which pages, which kinds of elements, which keys.
"""
import re
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path('.')
EXCLUDE = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}

files = [p for p in ROOT.rglob('*.html') if not (set(str(x) for x in p.parts) & EXCLUDE)]

empty = []
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    # Find <tag data-i18n="key"></tag> with empty content
    for m in re.finditer(r'<([a-zA-Z][a-zA-Z0-9]*)\s+[^>]*data-i18n="([^"]+)"[^>]*>\s*</\1>', text):
        tag = m.group(1)
        key = m.group(2)
        empty.append((f.relative_to(ROOT), tag, key))

print(f'Total empty-default elements: {len(empty)}')

# By tag
tag_count = Counter(t for _, t, _ in empty)
print(f'\nBy tag: {dict(tag_count)}')

# By file (top 5)
file_count = Counter(f for f, _, _ in empty)
print(f'\nBy file (top 10):')
for f, n in file_count.most_common(10):
    print(f'  {f}: {n}')

# By key prefix (top 10)
key_prefix_count = Counter(k.rsplit('.', 1)[0] for _, _, k in empty)
print(f'\nBy key prefix (top 10):')
for k, n in key_prefix_count.most_common(10):
    print(f'  {k}: {n}')

# Show samples
print(f'\nSample (5):')
for f, tag, key in empty[:5]:
    print(f'  {f}: <{tag} data-i18n="{key}"></{tag}>')
