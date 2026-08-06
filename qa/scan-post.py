"""
Scan a single HTML file for <a>/</a> and <p>/</p> imbalances + show line numbers.
"""
import re
import sys
from pathlib import Path

FILE = Path(sys.argv[1])
content = FILE.read_text(encoding="utf-8")

print(f"=== {FILE} ===\n")

# <a> and </a>
opens = list(re.finditer(r'<a[\s>]', content))
closes = list(re.finditer(r'</a>', content))
print(f"<a* opens: {len(opens)}, </a> closes: {len(closes)}")

# Walk and find imbalance
events = []
for o in opens:
    events.append((o.start(), 'open', o.start()))
for c in closes:
    events.append((c.start(), 'close', c.start()))
events.sort()

# Find line offsets
line_offsets = [0]
for i, ch in enumerate(content):
    if ch == '\n':
        line_offsets.append(i+1)
def get_line(pos):
    import bisect
    return bisect.bisect_right(line_offsets, pos)

stack = []
stray_closes = []
for pos, kind, _ in events:
    if kind == 'open':
        stack.append((pos, get_line(pos)))
    else:
        if stack:
            stack.pop()
        else:
            stray_closes.append((pos, get_line(pos)))

if stray_closes:
    print(f"\nStray </a> (no matching open):")
    for pos, ln in stray_closes[:5]:
        line_start = content.rfind('\n', 0, pos) + 1
        line_end = content.find('\n', pos)
        if line_end == -1: line_end = len(content)
        print(f"  L{ln}: {content[line_start:line_end].rstrip()[:200]}")

if stack:
    print(f"\nUnclosed <a> (no matching close):")
    for pos, ln in stack[:5]:
        line_start = content.rfind('\n', 0, pos) + 1
        line_end = content.find('\n', pos)
        if line_end == -1: line_end = len(content)
        print(f"  L{ln}: {content[line_start:line_end].rstrip()[:200]}")

print()
# <p> and </p>
p_opens = list(re.finditer(r'<p[\s>]', content))
p_closes = list(re.finditer(r'</p>', content))
print(f"<p* opens: {len(p_opens)}, </p> closes: {len(p_closes)}")

events = []
for o in p_opens:
    events.append((o.start(), 'open', get_line(o.start())))
for c in p_closes:
    events.append((c.start(), 'close', get_line(c.start())))
events.sort()

stack = []
stray_closes = []
for pos, kind, ln in events:
    if kind == 'open':
        stack.append((pos, ln))
    else:
        if stack:
            stack.pop()
        else:
            stray_closes.append((pos, ln))

if stray_closes:
    print(f"\nStray </p> (no matching open):")
    for pos, ln in stray_closes[:10]:
        line_start = content.rfind('\n', 0, pos) + 1
        line_end = content.find('\n', pos)
        if line_end == -1: line_end = len(content)
        print(f"  L{ln}: {content[line_start:line_end].rstrip()[:200]}")
