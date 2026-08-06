from pathlib import Path
import re
text = Path('about.html').read_text(encoding='utf-8')
orig = text
pattern = re.compile(r'<([a-zA-Z][a-zA-Z0-9]*)((?:[^<>]*?))<([a-zA-Z][a-zA-Z0-9]*)')
def repl(m):
    tag1 = m.group(1)
    middle = m.group(2)
    tag2 = m.group(3)
    if not middle:
        return f'<{tag1}><{tag2}'
    else:
        return f'<{tag1}{middle}><{tag2}'
text = pattern.sub(repl, text)
text = re.sub(r'<ahref=', '<a href=', text)
text = re.sub(r'<listyle=', '<li style=', text)
new_lines = []
for line in text.split('\n'):
    li_opens = len(re.findall(r'<li[\s>]', line))
    li_closes = len(re.findall(r'</li>', line))
    if li_closes > li_opens:
        n_needed = li_closes - li_opens
        m = re.match(r'^(\s*)(.*)$', line)
        if m:
            ws, content = m.group(1), m.group(2)
            line = ws + '<li>' * n_needed + content
    new_lines.append(line)
text = '\n'.join(new_lines)
import difflib
diff = list(difflib.unified_diff(orig.split('\n'), text.split('\n'), lineterm='', n=0))
minus = [d for d in diff if d.startswith('-') and not d.startswith('---')]
plus = [d for d in diff if d.startswith('+') and not d.startswith('+++')]
print(f'Lines removed: {len(minus)}, added: {len(plus)}')
for d in diff[:40]:
    if d.startswith('-') or d.startswith('+'):
        if d.startswith('---') or d.startswith('+++'):
            continue
        print(d[:250])
