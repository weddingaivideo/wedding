"""
Dump all <a> and </a> events with line numbers to find imbalance.
"""
import os
import re
import bisect
from pathlib import Path

FILE = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent) / "blog" / "index.html"
content = FILE.read_text(encoding="utf-8")

opens = list(re.finditer(r'<a[\s>]', content))
closes = list(re.finditer(r'</a>', content))
print(f'opens: {len(opens)}, closes: {len(closes)}')

line_offsets = [0]
for i, ch in enumerate(content):
    if ch == '\n':
        line_offsets.append(i+1)

def get_line(pos):
    return bisect.bisect_right(line_offsets, pos)

events = []
for o in opens:
    events.append((o.start(), 'open', get_line(o.start())))
for c in closes:
    events.append((c.start(), 'close', get_line(c.start())))
events.sort()

# Walk and track stack
stack = []
for pos, kind, ln in events:
    if kind == 'open':
        stack.append(ln)
    else:
        if stack:
            stack.pop()
        else:
            print(f'  STRAY CLOSE L{ln}')

print(f'\nFinal stack: {len(stack)} unclosed opens: {stack[:10]}')
