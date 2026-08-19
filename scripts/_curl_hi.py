"""Curl with NO redirect following to see the actual 302 chain."""
import urllib.request

urls = [
    'https://weddingai.video/hi/',
    'https://weddingai.video/hi/blog/',
    'https://weddingai.video/hi/blog/affordable-wedding-video-ai/',
    'https://weddingai.video/zh/',  # Control: zh/ already worked
]
for url in urls:
    print(f'\n=== {url} ===')
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    opener = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'hi'})
    try:
        resp = opener.open(req, timeout=15)
        print(f'  status: {resp.status}')
        print(f'  Location: {resp.headers.get("Location", "none")}')
    except urllib.error.HTTPError as e:
        print(f'  HTTP {e.code}')
        print(f'  Location: {e.headers.get("Location", "none")}')
    except Exception as e:
        print(f'  ERR: {e}')
