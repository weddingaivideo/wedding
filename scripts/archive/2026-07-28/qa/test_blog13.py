import re
import sys
from pathlib import Path
sys.path.insert(0, 'qa')
from fix_structural_v2 import fix_text
text = Path('blog/13-how-long-should-wedding-video-be/index.html').read_text(encoding='utf-8')
new_text = fix_text(text)
print(f'Changed: {new_text != text}')
strong_pat = re.compile(r'<strong<strong')
print(f'<strong<strong in original: {len(strong_pat.findall(text))}')
print(f'<strong<strong in new:      {len(strong_pat.findall(new_text))}')
import difflib
diff = list(difflib.unified_diff(text.split('\n'), new_text.split('\n'), lineterm='', n=0))
shown = 0
for d in diff:
    if d.startswith('+') or d.startswith('-'):
        if d.startswith('+++') or d.startswith('---'):
            continue
        print(d[:200])
        shown += 1
        if shown > 20: break
