import urllib.request
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
urls = [
    'https://da194454.weddingai-video.pages.dev/blog/01-restore-old-wedding-videos/',
    'https://da194454.weddingai-video.pages.dev/zh/blog/01-restore-old-wedding-videos/',
    'https://da194454.weddingai-video.pages.dev/ja/blog/01-restore-old-wedding-videos/',
    'https://da194454.weddingai-video.pages.dev/services/personalization/cartoon-style/',
    'https://da194454.weddingai-video.pages.dev/de/services/personalization/cartoon-style/',
    'https://da194454.weddingai-video.pages.dev/order/',
    'https://da194454.weddingai-video.pages.dev/zh/order/',
    'https://da194454.weddingai-video.pages.dev/ru/order/',
]
for u in urls:
    try:
        req = urllib.request.Request(u, headers={'User-Agent': UA})
        r = urllib.request.urlopen(req, timeout=10)
        body = r.read().decode('utf-8', errors='ignore')
        # Extract lang
        lang = '?'
        if '<html lang="' in body:
            lang = body.split('<html lang="')[1].split('"')[0]
        # Extract canonical
        canon = '?'
        if 'rel="canonical" href="' in body:
            canon = body.split('rel="canonical" href="')[1].split('"')[0]
        n_alt = body.count('hreflang=')
        print(f'{u}')
        print(f'  status={r.status} lang={lang}  canonical={canon}  hreflangs={n_alt}')
    except Exception as e:
        print(f'{u}  ERROR: {e}')
