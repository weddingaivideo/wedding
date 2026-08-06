"""Fix og:url, twitter:card, og:image domain across all pages.
- Adds og:url (self-ref) where missing, using canonical URL
- Adds twitter:card meta if missing
- Replaces any celebrationai.video in og:image with weddingai.video
"""
import os, re, glob, sys

BASE = 'https://weddingai.video'
DOMAIN_BUG = 'celebrationai.video'

files = sorted(glob.glob('*.html') + glob.glob('services/**/*.html', recursive=True))
files = [f for f in files if 'google-site-verification' not in f]

changes = {'og_url': 0, 'twitter': 0, 'og_image_fix': 0, 'og_added': 0}

for f in files:
    with open(f, 'r', encoding='utf-8') as fh:
        html = fh.read()
    orig = html

    # 1) Fix og:image domain bug
    if DOMAIN_BUG in html:
        html = html.replace(DOMAIN_BUG, 'weddingai.video')
        changes['og_image_fix'] += 1

    # 2) Compute canonical self-ref URL
    norm_path = '/' + f.replace(os.sep, '/')
    # index.html at root = "/"
    if norm_path == '/index.html':
        norm_path = '/'
    # services/index.html = "/services/"
    if norm_path == '/services/index.html':
        norm_path = '/services/'
    full_url = BASE + norm_path

    # 3) Inject og:url if missing
    if '<meta property="og:url"' not in html:
        # inject after og:description (or og:title as fallback)
        m = re.search(r'(<meta property="og:description"[^>]*>)', html)
        if not m:
            m = re.search(r'(<meta property="og:title"[^>]*>)', html)
        if m:
            tag = f'\n    <meta property="og:url" content="{full_url}">'
            html = html[:m.end()] + tag + html[m.end():]
            changes['og_url'] += 1

    # 4) Inject twitter:card if missing (use summary_large_image)
    if '<meta name="twitter:card"' not in html:
        m = re.search(r'(<meta property="og:url"[^>]*>)', html)
        if not m:
            m = re.search(r'(<meta property="og:description"[^>]*>)', html)
        if m:
            tag = f'\n    <meta name="twitter:card" content="summary_large_image">'
            html = html[:m.end()] + tag + html[m.end():]
            changes['twitter'] += 1

    if html != orig:
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(html)

print(f'✅ Files updated')
for k, v in changes.items():
    print(f'  {k}: {v}')
