"""
Find stray </p> in index.html.
"""
import os
import re
import bisect
from pathlib import Path

FILE = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent) / "index.html"
content = FILE.read_text(encoding="utf-8")

opens = list(re.finditer(r'<p[\s>]', content))
closes = list(re.finditer(r'</p>', content))

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

stack = []
for pos, kind, ln in events:
    if kind == 'open':
        stack.append(ln)
    else:
        if stack:
            stack.pop()
        else:
            line_start = content.rfind('\n', 0, pos) + 1
            line_end = content.find('\n', pos)
            if line_end == -1: line_end = len(content)
            print(f'STRAY </p> at line {ln}:')
            print(f'  {content[line_start:line_end].rstrip()[:200]}')
