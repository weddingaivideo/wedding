import urllib.request

urls = [
    'https://ec65b97b.weddingai-video.pages.dev/',
    'https://ec65b97b.weddingai-video.pages.dev/zh/',
    'https://ec65b97b.weddingai-video.pages.dev/zh/about/',
    'https://ec65b97b.weddingai-video.pages.dev/ja/',
    'https://ec65b97b.weddingai-video.pages.dev/ar/about/',
    'https://ec65b97b.weddingai-video.pages.dev/de/services/personalization/wedding-trailer/',
    'https://ec65b97b.weddingai-video.pages.dev/about/',
]

for url in urls:
    try:
        req = urllib.request.Request(url, method='GET')
        req.add_header('User-Agent', 'Mozilla/5.0 (Test)')
        resp = urllib.request.urlopen(req, timeout=10)
        body = resp.read().decode('utf-8', errors='ignore')
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='ignore') if hasattr(e, 'read') else str(e)
        print(f'{url}  HTTP {e.code}: {body[:300]}')
        continue
        lang = '?'
        if '<html lang="' in body:
            lang = body.split('<html lang="')[1].split('"')[0]
        canon = '?'
        if '<link rel="canonical" href="' in body:
            canon = body.split('<link rel="canonical" href="')[1].split('"')[0]
        # Check for hreflang alternates count
        alts = body.count('hreflang=')
        print(f'{url}  {resp.status}  lang={lang}  canonical={canon}  hreflangs={alts}')
    except Exception as e:
        print(f'{url}  ERROR: {e}')
