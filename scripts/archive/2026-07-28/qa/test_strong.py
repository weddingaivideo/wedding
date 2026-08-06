import re
text = '<li><strong<strong>0:00-0:30</strong>: Getting ready footage</li>'
pattern = re.compile(r'<([a-zA-Z][a-zA-Z0-9]*)((?:[^<>]*?))<([a-zA-Z][a-zA-Z0-9]*)')
matches = list(pattern.finditer(text))
print(f'Matches: {len(matches)}')
for m in matches:
    print(f'  tag1={m.group(1)!r} middle={m.group(2)!r} tag2={m.group(3)!r}')

def repl(m):
    tag1 = m.group(1)
    middle = m.group(2)
    tag2 = m.group(3)
    return f'<{tag1}><{tag2}>' if not middle else f'<{tag1}{middle}><{tag2}>'

new = pattern.sub(repl, text)
print(f'After: {new}')
