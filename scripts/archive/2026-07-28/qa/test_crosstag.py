import re
text = '<li><strong<a href="X"><a href="X">label</a></strong></li>'
pattern = re.compile(r'<([a-zA-Z][a-zA-Z0-9]*)((?:[^<>]*?))<([a-zA-Z][a-zA-Z0-9]*)')
def repl(m):
    tag1 = m.group(1)
    middle = m.group(2)
    tag2 = m.group(3)
    return f'<{tag1}><{tag2}' if not middle else f'<{tag1}{middle}><{tag2}'
result = pattern.sub(repl, text)
print(f'Before: {text}')
print(f'After:  {result}')

# Test idempotency
result2 = pattern.sub(repl, result)
print(f'After2: {result2}')
print(f'Idempotent: {result == result2}')
