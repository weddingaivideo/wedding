import urllib.request
urls = [
    'https://da194454.weddingai-video.pages.dev/',
    'https://da194454.weddingai-video.pages.dev/zh/',
    'https://da194454.weddingai-video.pages.dev/zh/about/',
    'https://da194454.weddingai-video.pages.dev/ja/',
    'https://da194454.weddingai-video.pages.dev/ar/about/',
    'https://da194454.weddingai-video.pages.dev/de/services/personalization/wedding-trailer/',
    'https://da194454.weddingai-video.pages.dev/about/',
    'https://da194454.weddingai-video.pages.dev/ja/blog/01-restore-old-wedding-videos/',
]
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
for u in urls:
    try:
        req = urllib.request.Request(u, headers={'User-Agent': UA})
        r = urllib.request.urlopen(req, timeout=10)
        body = r.read().decode('utf-8', errors='ignore')
        lang = '?'
        if '<html lang=' in body:
            lang = body.split('<html lang="')[1].split('"')[0]
        canon = '?'
        if '<link rel="canonical" href=' in body:
            canon = body.split('<link rel="canonical" href="')[1].split('"')[0]
        # Count hreflangs
        n_alt = body.count('hreflang=')
        dir_attr = 'ltr'
        if 'dir="rtl"' in body[:2000]:
            dir_attr = 'rtl'
        print(f'{u}')
        print(f'  status={r.status} lang={lang} dir={dir_attr}  canonical={canon}  hreflangs={n_alt}')
    except Exception as e:
        print(f'{u}  ERROR: {e}')
