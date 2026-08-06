"""Check order/index.html og:url line."""
import re
text = open('order/index.html', encoding='utf-8').read()
m = re.search(r'og:url"\s+content="https://weddingai\.video/order">', text)
print(f'Old typo pattern match: {bool(m)}')
for line in text.split('\n'):
    if 'og:url' in line:
        print(repr(line))
