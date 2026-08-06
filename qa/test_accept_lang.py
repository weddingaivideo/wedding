import urllib.request
import urllib.error
BASE = 'https://3f615e80.weddingai-video.pages.dev'

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None

opener = urllib.request.build_opener(NoRedirect)

def do_req(path, accept_lang='', cookies=''):
    url = BASE + path
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    if accept_lang:
        req.add_header('Accept-Language', accept_lang)
    if cookies:
        req.add_header('Cookie', cookies)
    try:
        r = opener.open(req, timeout=10)
        return r.status, r.headers.get('Location', ''), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('Location', ''), e.read()

# (path, accept-lang, cookies, expected_status, expected_location_or_status_code)
cases = [
    # 1. No prefix, browser wants zh → 302 to /zh/
    ('/', 'zh-CN,zh;q=0.9,en;q=0.8', '', 302, '/zh/'),
    # 2. No prefix, browser wants ja → 302 to /ja/
    ('/', 'ja,en;q=0.5', '', 302, '/ja/'),
    # 3. No prefix, browser wants English → no redirect (200)
    ('/', 'en-US,en;q=0.9', '', 200, None),
    # 4. No prefix, browser wants es → 302 to /es/
    ('/', 'es-ES,es;q=0.9,en;q=0.8', '', 302, '/es/'),
    # 5. /about/ + browser zh → 302 to /zh/about/
    ('/about/', 'zh-CN,zh;q=0.9', '', 302, '/zh/about/'),
    # 6. /about/ + browser de → 302 to /de/about/
    ('/about/', 'de-DE,de;q=0.9', '', 302, '/de/about/'),
    # 7. /about/ + browser ar → 302 to /ar/about/
    ('/about/', 'ar,en;q=0.5', '', 302, '/ar/about/'),
    # 8. / + browser zh + auto cookie set → no redirect
    ('/', 'zh-CN,zh;q=0.9', 'wa_lang_auto=1', 200, None),
    # 9. / + browser ja + user cookie set → no redirect
    ('/', 'ja,en;q=0.5', 'wa_lang_user=fr', 200, None),
    # 10. /zh/ already has prefix → no redirect
    ('/zh/', 'en-US,en;q=0.9', '', 200, None),
    # 11. CSS file (has extension) → skipped, no redirect
    ('/styles.min.css', 'zh-CN,zh;q=0.9', '', 200, None),
    # 12. API endpoint → skipped, no redirect
    ('/api/quote', 'zh-CN,zh;q=0.9', '', 405, None),  # 405 method not allowed (POST only)
    # 13. i18n JSON → skipped, no redirect
    ('/i18n/zh.json', 'ja,en;q=0.5', '', 200, None),
    # 14. /order/ + browser fr → 302 to /fr/order/
    ('/order/', 'fr-FR,fr;q=0.9', '', 302, '/fr/order/'),
    # 15. /blog/ + browser ru → 302 to /ru/blog/
    ('/blog/', 'ru-RU,ru;q=0.9', '', 302, '/ru/blog/'),
    # 16. Deep path /services/personalization/wedding-trailer/ + th → 302
    ('/services/personalization/wedding-trailer/', 'th-TH,th;q=0.9', '', 302, '/th/services/personalization/wedding-trailer/'),
]

passed = 0
for path, accept, cookies, expect_status, expect_loc in cases:
    status, loc, _ = do_req(path, accept, cookies)
    loc_path = loc.replace(BASE, '') if loc else ''
    ok = status == expect_status
    if expect_loc:
        ok = ok and loc_path == expect_loc
    mark = '✓' if ok else '✗'
    if ok: passed += 1
    print(f'{mark}  {path:50s}  AL={accept[:25]:25s}  → {status}  loc={loc_path}')

print(f'\n{passed}/{len(cases)} passed')
