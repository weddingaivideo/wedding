"""
Find unbalanced <a> tags in a file.
Reports lines that open or close <a> tags in suspicious patterns.
"""
import re
import sys
from pathlib import Path

FILE = Path(r"C:/Users/qiaoshan/.openclaw/workspace/weddingai/blog/index.html")
content = FILE.read_text(encoding="utf-8")

# Find all <a opening tags and all </a> closing tags
# Use a stateful scan
stack = []  # list of (line_num, full_match)
opens = list(re.finditer(r'<a[\s>][^>]*>', content, re.DOTALL))
closes = list(re.finditer(r'</a>', content))

# Walk through content linearly, alternating opens/closes
pos = 0
open_idx = 0
close_idx = 0
line_num = 1
events = []  # (position, type, line_num, text)

for m in opens:
    events.append((m.start(), 'open', line_num, m.group()))
for m in closes:
    events.append((m.start(), 'close', line_num, m.group()))

# Sort by position
events.sort(key=lambda x: x[0])

# Walk and report mismatches
stack = []
for pos, kind, ln, text in events:
    if kind == 'open':
        stack.append((pos, ln, text))
    else:
        if stack:
            stack.pop()
        else:
            print(f"UNMATCHED </a> at line {ln}: {text!r}")

if stack:
    print(f"UNCLOSED <a> tags ({len(stack)}):")
    for pos, ln, text in stack:
        # Find line in original content
        line_start = content.rfind('\n', 0, pos) + 1
        line_end = content.find('\n', pos)
        if line_end == -1: line_end = len(content)
        print(f"  line {ln}: {content[line_start:line_end].strip()[:200]}")
else:
    print("All <a> tags balanced.")
