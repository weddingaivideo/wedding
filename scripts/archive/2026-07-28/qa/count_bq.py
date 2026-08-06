import re
text = open('gallery/index.html', encoding='utf-8').read()
print(f'<blockquote : {len(re.findall(r"<blockquote", text))}')
print(f'</blockquote>: {len(re.findall(r"</blockquote>", text))}')
print(f'<blockquoteclass: {len(re.findall(r"<blockquoteclass", text))}')
print(f'<blockquote class: {len(re.findall(r"<blockquote class", text))}')
