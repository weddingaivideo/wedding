import re
import sys

names = ['about.html', 'about/index.html', 'gallery.html', 'gallery/index.html', 'order.html', 'order/index.html',
         'success.html', 'success/index.html', 'privacy.html', 'privacy/index.html',
         'resources.html', 'resources/index.html', 'terms.html', 'terms/index.html',
         '404.html', 'blog.html', 'blog/index.html', 'search.html', 'search/index.html',
         'index.html', 'services/index.html', 'services.html']

for name in names:
    try:
        text = open(name, encoding='utf-8').read()
    except FileNotFoundError:
        continue
    n_keys = len(re.findall(r'data-i18n="', text))
    n_open = len(re.findall(r'<li[\s>]', text))
    n_close = len(re.findall(r'</li>', text))
    n_cross = len(re.findall(r'<([a-zA-Z][a-zA-Z0-9]*)(<[a-zA-Z][a-zA-Z0-9]*)', text))
    print(f'{name:50s}  keys={n_keys:4d}  li={n_open}/{n_close}  cross={n_cross}')
