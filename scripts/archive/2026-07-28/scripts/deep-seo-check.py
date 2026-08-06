import os, re, glob

files = sorted(glob.glob('*.html') + glob.glob('services/**/*.html', recursive=True))
files = [f for f in files if 'google-site-verification' not in f]
print(f'=== DEEP SEO CHECK — {len(files)} pages ===\n')
issues = {}
for f in files:
    with open(f, 'r', encoding='utf-8') as fh:
        html = fh.read()
    p = []
    # canonical
    m = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    if not m:
        p.append('NO canonical')
    else:
        can = m.group(1)
        norm = f.replace(os.sep, '/')
        if norm not in can:
            p.append(f'canonical NOT self-ref: {can}')
    # viewport
    if not re.search(r'<meta name="viewport"', html):
        p.append('NO viewport')
    # og:title
    if not re.search(r'<meta property="og:title"', html):
        p.append('NO og:title')
    # og:description
    if not re.search(r'<meta property="og:description"', html):
        p.append('NO og:description')
    # og:image
    if not re.search(r'<meta property="og:image"', html):
        p.append('NO og:image')
    # og:url
    if not re.search(r'<meta property="og:url"', html):
        p.append('NO og:url')
    # twitter card
    if not re.search(r'<meta name="twitter:card"', html):
        p.append('NO twitter:card')
    # h1 count
    h1s = re.findall(r'<h1[^>]*>', html)
    if len(h1s) != 1:
        p.append(f'h1 count={len(h1s)} (need 1)')
    # img without alt
    imgs = re.findall(r'<img[^>]*>', html)
    no_alt = [i for i in imgs if 'alt=' not in i]
    if no_alt:
        p.append(f'{len(no_alt)} imgs without alt')
    # schema type
    schemas = re.findall(r'"@type"\s*:\s*"([^"]+)"', html)
    if not schemas:
        p.append('NO schema.org')
    if p:
        issues[f] = p

for f, ps in issues.items():
    print(f'❌ {f}')
    for p in ps:
        print(f'    - {p}')

print(f'\n{len(issues)}/{len(files)} pages have issues')
