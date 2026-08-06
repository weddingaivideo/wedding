from pathlib import Path
a = Path('about.html').read_text(encoding='utf-8')
b = Path('about/index.html').read_text(encoding='utf-8')
import re
patterns = ['<p<', '<li<', '<a<picture', '<ahref', 'listyle=']
for name, t in [('about.html', a), ('about/index.html', b)]:
    print(f'{name}:')
    for pat in patterns:
        n = t.count(pat)
        if n > 0:
            print(f'  {pat}: {n}')
    # Check for /i18n path differences
    has_slash = '/images/' in t and '/favicon.svg' in t
    print(f'  uses /images/ path: {has_slash}')
