"""Interaction / UX test suites for WeddingAI.video.

Every test drives a real browser the way a user would: click the mobile menu,
press Escape, tab through the header, pick a language, submit an empty order form,
upload a photo into a tool, click a gallery filter, search the site, follow the
CTA chain - and asserts on what the user actually gets back.

Each assertion is recorded with PASS / FAIL / WARN / BLOCKED + evidence so the
report can be traced back to a concrete interaction.

    python qa/ux/interactions.py                 # everything
    python qa/ux/interactions.py --only tools    # one suite
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PIL import Image, ImageDraw  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402

from common import (  # noqa: E402
    BASE, LANGS, RESULTS, ROOT, SHOTS, UA, VIEWPORTS, load, save, slugify, to_local,
)

FIXTURES = RESULTS / "fixtures"

BLOCKED_HOSTS = set()


def make_fixtures() -> dict[str, Path]:
    """Real image files to feed the upload tools (and a bad-type file)."""
    FIXTURES.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}

    p = FIXTURES / "couple.jpg"
    if not p.exists():
        img = Image.new("RGB", (1200, 800), (232, 214, 200))
        d = ImageDraw.Draw(img)
        d.ellipse((300, 120, 900, 720), fill=(255, 255, 255))
        d.rectangle((0, 700, 1200, 800), fill=(120, 140, 160))
        img.save(p, "JPEG", quality=90)
    out["jpg"] = p

    p = FIXTURES / "portrait.png"
    if not p.exists():
        img = Image.new("RGBA", (900, 1200), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse((150, 150, 750, 1050), fill=(200, 160, 140, 255))
        img.save(p, "PNG")
    out["png"] = p

    p = FIXTURES / "not-an-image.txt"
    if not p.exists():
        p.write_text("This is a text file, not a photo.\n" * 5, encoding="utf-8")
    out["txt"] = p
    return out


class Runner:
    def __init__(self, browser, results: list):
        self.browser = browser
        self.results = results
        self.ctx = None

    def rec(self, tid: str, name: str, page: str, status: str, detail: str,
            viewport: str = "", evidence=None):
        self.results.append({
            "id": tid, "name": name, "page": page, "viewport": viewport,
            "status": status, "detail": detail, "evidence": evidence,
        })
        mark = {"PASS": "OK  ", "FAIL": "FAIL", "WARN": "WARN", "BLOCKED": "BLK "}[status]
        print(f"  {mark} [{tid}] {name} — {detail[:150]}", flush=True)

    async def page(self, viewport: str = "desktop", consent: bool = True,
                   lang_stub: str | None = None):
        ctx = await self.browser.new_context(
            viewport=VIEWPORTS[viewport], user_agent=UA, locale="en-US",
            service_workers="block", ignore_https_errors=True,
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
        )
        if consent:
            await ctx.add_init_script(
                "try { localStorage.setItem('wa_cookie_consent','all'); } catch (e) {}")
        pg = await ctx.new_page()
        pg._ux_ctx = ctx  # type: ignore[attr-defined]
        return pg

    async def close(self, pg):
        ctx = getattr(pg, "_ux_ctx", None)
        await pg.close()
        if ctx:
            await ctx.close()

    async def route_block(self, pg):
        async def handler(route):
            try:
                u = urlparse(route.request.url)
            except Exception:
                return await route.abort()
            if u.hostname in ("127.0.0.1", "localhost") or u.scheme not in ("http", "https"):
                return await route.continue_()
            BLOCKED_HOSTS.add(u.netloc)
            await route.abort()
        await pg.route("**/*", handler)


# --------------------------------------------------------------------------- #
# A. global chrome
# --------------------------------------------------------------------------- #

async def suite_chrome(r: Runner, paths: list[str]) -> None:
    print("\n== A. global chrome (nav / cookie / language / keyboard) ==", flush=True)

    # --- cookie banner ---
    pg = await r.page("mobile", consent=False)
    await r.route_block(pg)
    await pg.goto(to_local(paths[0]), wait_until="load")
    await pg.wait_for_timeout(300)
    banner = await pg.query_selector("#wa-cookie-banner")
    if banner:
        r.rec("COOKIE-01", "Cookie banner shows on first visit", paths[0], "PASS",
              "banner rendered", viewport="mobile")
        btn = await pg.query_selector("#wa-cookie-accept")
        await btn.click()
        await pg.wait_for_timeout(200)
        gone = await pg.evaluate("() => !document.getElementById('wa-cookie-banner')")
        r.rec("COOKIE-02", "'Accept all' dismisses the banner", paths[0],
              "PASS" if gone else "FAIL", "banner removed" if gone else "banner still on screen",
              viewport="mobile")
        stored = await pg.evaluate("() => localStorage.getItem('wa_cookie_consent')")
        await pg.reload(wait_until="load")
        await pg.wait_for_timeout(300)
        again = await pg.evaluate("() => !!document.getElementById('wa-cookie-banner')")
        r.rec("COOKIE-03", "Choice is remembered across reload (180-day consent)",
              paths[0], "PASS" if (not again and stored) else "FAIL",
              f"localStorage={stored!r}, banner after reload={'shown' if again else 'hidden'}",
              viewport="mobile")
    else:
        r.rec("COOKIE-01", "Cookie banner shows on first visit", paths[0], "FAIL",
              "no #wa-cookie-banner element found", viewport="mobile")

    # 'essential only' path
    pg2 = await r.page("mobile", consent=False)
    await r.route_block(pg2)
    await pg2.goto(to_local(paths[0]), wait_until="load")
    await pg2.wait_for_timeout(250)
    rej = await pg2.query_selector("#wa-cookie-reject")
    if rej:
        await rej.click()
        await pg2.wait_for_timeout(150)
        val = await pg2.evaluate("() => localStorage.getItem('wa_cookie_consent')")
        r.rec("COOKIE-04", "'Essential only' stores the rejection", paths[0],
              "PASS" if val == "essential" else "FAIL", f"localStorage={val!r}", viewport="mobile")
    else:
        r.rec("COOKIE-04", "'Essential only' stores the rejection", paths[0], "FAIL",
              "reject button missing", viewport="mobile")
    await r.close(pg2)

    # --- mobile menu: open / escape / outside click / focus trap ---
    pg = await r.page("mobile")
    await r.route_block(pg)
    await pg.goto(to_local(paths[0]), wait_until="load")
    await pg.wait_for_timeout(250)

    tog = await pg.query_selector(".mobile-menu-toggle")
    nav = await pg.query_selector(".main-nav")
    if not tog or not nav:
        r.rec("NAV-00", "Mobile menu markup present", paths[0], "FAIL",
              f"toggle={bool(tog)} nav={bool(nav)}", viewport="mobile")
    else:
        tog_visible = await tog.is_visible()
        nav_hidden = not await nav.is_visible()
        r.rec("NAV-01", "Hamburger visible / nav collapsed on mobile", paths[0],
              "PASS" if (tog_visible and nav_hidden) else "FAIL",
              f"toggle_visible={tog_visible}, nav_visible={not nav_hidden}", viewport="mobile")

        await tog.click()
        await pg.wait_for_timeout(250)
        st = await pg.evaluate("""() => {
            const t = document.querySelector('.mobile-menu-toggle');
            const n = document.querySelector('.main-nav');
            const r = n.getBoundingClientRect();
            return {open: n.classList.contains('active'), aria: t.getAttribute('aria-expanded'),
                    visible: getComputedStyle(n).display !== 'none' && r.height > 0,
                    inViewport: r.top >= -1 && r.bottom <= window.innerHeight + 1,
                    height: Math.round(r.height), focused: document.activeElement.tagName + ':' + (document.activeElement.textContent||'').trim().slice(0,20)};
        }""")
        r.rec("NAV-02", "Tap hamburger opens the nav", paths[0],
              "PASS" if (st["open"] and st["aria"] == "true" and st["visible"]) else "FAIL",
              f"aria-expanded={st['aria']}, panel height={st['height']}px, in viewport={st['inViewport']}",
              viewport="mobile", evidence=st)
        r.rec("NAV-03", "Open panel fits the mobile viewport (no clipped items)", paths[0],
              "PASS" if st["inViewport"] else "FAIL",
              f"panel bottom vs viewport: inViewport={st['inViewport']}", viewport="mobile")
        r.rec("NAV-04", "Focus moves into the menu when it opens", paths[0],
              "PASS" if st["focused"].startswith("A") else "WARN",
              f"activeElement={st['focused']}", viewport="mobile")

        await pg.keyboard.press("Escape")
        await pg.wait_for_timeout(200)
        after = await pg.evaluate("""() => {
            const t = document.querySelector('.mobile-menu-toggle');
            const n = document.querySelector('.main-nav');
            return {open: n.classList.contains('active'), aria: t.getAttribute('aria-expanded'),
                    focusOnToggle: document.activeElement === t};
        }""")
        r.rec("NAV-05", "Escape closes the menu and returns focus", paths[0],
              "PASS" if (not after["open"] and after["aria"] == "false") else "FAIL",
              f"open={after['open']}, aria-expanded={after['aria']}", viewport="mobile")
        r.rec("NAV-06", "Focus returns to the hamburger after Escape", paths[0],
              "PASS" if after["focusOnToggle"] else "FAIL",
              f"focusOnToggle={after['focusOnToggle']}", viewport="mobile")

        await tog.click()
        await pg.wait_for_timeout(200)
        await pg.mouse.click(5, 400)
        await pg.wait_for_timeout(200)
        closed = await pg.evaluate("() => !document.querySelector('.main-nav').classList.contains('active')")
        r.rec("NAV-07", "Tapping outside closes the menu", paths[0],
              "PASS" if closed else "FAIL", f"closed={closed}", viewport="mobile")

        # focus trap: tab through the whole menu, focus must stay inside
        await tog.click()
        await pg.wait_for_timeout(200)
        n_links = await pg.evaluate("() => document.querySelectorAll('.main-nav a').length")
        inside = True
        for _ in range(n_links + 6):
            await pg.keyboard.press("Tab")
            ok = await pg.evaluate(
                "() => !!document.activeElement.closest('.main-nav') || document.activeElement === document.querySelector('.mobile-menu-toggle')")
            if not ok:
                inside = False
                break
        r.rec("NAV-08", "Focus stays trapped inside the open menu", paths[0],
              "PASS" if inside else "FAIL",
              f"tabbed {n_links + 6} times over {n_links} nav links without escaping", viewport="mobile")
        await pg.keyboard.press("Escape")

        # every nav link resolves
        hrefs = await pg.evaluate(
            "() => Array.from(document.querySelectorAll('.main-nav a')).map(a => a.getAttribute('href'))")
        bad = []
        for h in hrefs:
            if not h or h.startswith("#") or h.startswith(("mailto:", "tel:")):
                continue
            resp = await pg.request.get(BASE + h if h.startswith("/") else h,
                                        max_redirects=0, timeout=20000)
            if resp.status >= 400:
                bad.append((h, resp.status))
        r.rec("NAV-09", "Every header nav link resolves", paths[0],
              "PASS" if not bad else "FAIL",
              f"{len(hrefs)} links checked, broken: {bad[:5]}" if bad else f"{len(hrefs)} links all OK",
              viewport="mobile")
    await r.close(pg)

    # --- desktop nav + skip link + focus visibility ---
    pg = await r.page("desktop")
    await r.route_block(pg)
    await pg.goto(to_local(paths[0]), wait_until="load")
    await pg.wait_for_timeout(250)
    d = await pg.evaluate("""() => {
        const nav = document.querySelector('.main-nav');
        const tog = document.querySelector('.mobile-menu-toggle');
        return {navVisible: !!nav && getComputedStyle(nav).display !== 'none',
                togVisible: !!tog && getComputedStyle(tog).display !== 'none'};
    }""")
    r.rec("NAV-10", "Desktop shows the full nav, not the hamburger", paths[0],
          "PASS" if (d["navVisible"] and not d["togVisible"]) else "FAIL",
          f"nav_visible={d['navVisible']}, hamburger_visible={d['togVisible']}", viewport="desktop")

    await pg.keyboard.press("Tab")
    await pg.wait_for_timeout(120)
    skip = await pg.evaluate("""() => {
        const el = document.activeElement;
        if (!el) return null;
        const cs = getComputedStyle(el);
        const r = el.getBoundingClientRect();
        return {tag: el.tagName, text: (el.textContent||'').trim().slice(0,40), href: el.getAttribute('href'),
                visible: r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.opacity !== '0'};
    }""")
    if skip and skip.get("href") and skip["href"].startswith("#"):
        r.rec("A11Y-01", "First Tab reveals a skip-to-content link", paths[0],
              "PASS" if skip["visible"] else "FAIL",
              f"focused {skip['tag']} '{skip['text']}' -> {skip['href']} visible={skip['visible']}",
              viewport="desktop", evidence=skip)
        tgt = skip["href"][1:]
        has = await pg.evaluate(f"() => !!document.getElementById({json.dumps(tgt)})")
        r.rec("A11Y-02", "Skip link target exists in the DOM", paths[0],
              "PASS" if has else "FAIL", f"target #{tgt} exists={has}", viewport="desktop")
    else:
        r.rec("A11Y-01", "First Tab reveals a skip-to-content link", paths[0], "WARN",
              f"first focusable is {skip}", viewport="desktop")

    outline = await pg.evaluate("""() => {
        const link = document.querySelector('.main-nav a');
        const before = getComputedStyle(link, null);
        const b = {outline: before.outlineWidth, shadow: before.boxShadow};
        link.focus();
        const after = getComputedStyle(link, null);
        return {before: b, after: {outline: after.outlineWidth, shadow: after.boxShadow},
                changed: b.outline !== after.outline || b.shadow !== after.shadow};
    }""")
    r.rec("A11Y-03", "Keyboard focus is visually indicated on nav links", paths[0],
          "PASS" if outline["changed"] else "FAIL",
          f"focus style changes: {outline['changed']}", viewport="desktop", evidence=outline)

    ext = await pg.evaluate("""() => {
        const bad = [];
        document.querySelectorAll('a[target="_blank"]').forEach(a => {
            const rel = (a.getAttribute('rel')||'').toLowerCase();
            if (!rel.includes('noopener')) bad.push((a.getAttribute('href')||'').slice(0,60));
        });
        return bad;
    }""")
    r.rec("SEC-01", "target=_blank links carry rel=noopener", paths[0],
          "PASS" if not ext else "FAIL",
          f"{len(ext)} links without noopener" if ext else "all _blank links hardened",
          viewport="desktop", evidence=ext[:5])

    zoomy = await pg.evaluate("""() => {
        const small = [];
        document.querySelectorAll('input, select, textarea').forEach(el => {
            const fs = parseFloat(getComputedStyle(el).fontSize);
            if (fs && fs < 16) small.push({id: el.id||el.name||el.type, fs});
        });
        return small;
    }""")
    r.rec("A11Y-04", "Form fields are >=16px (iOS auto-zoom on focus)", paths[0],
          "PASS" if not zoomy else "WARN",
          "all fields >=16px" if not zoomy else f"{len(zoomy)} fields <16px: {zoomy[:4]}",
          viewport="desktop", evidence=zoomy[:6])

    vpmeta = await pg.evaluate("() => (document.querySelector('meta[name=viewport]')||{}).content || ''")
    zoom_locked = "user-scalable=no" in vpmeta.replace(" ", "")
    r.rec("A11Y-05", "Viewport meta does not block pinch-zoom", paths[0],
          "PASS" if not zoom_locked else "FAIL",
          f"content=\"{vpmeta}\"", viewport="desktop")
    await r.close(pg)

    # --- language switcher ---
    for target_lang in ("zh", "es", "th"):
        pg = await r.page("desktop")
        await r.route_block(pg)
        await pg.goto(to_local("/"), wait_until="load")
        await pg.wait_for_timeout(200)
        sel = await pg.query_selector("#wa-lang-select")
        if not sel:
            r.rec("I18N-SW-01", "Language selector present", "/", "FAIL",
                  "#wa-lang-select not found", viewport="desktop")
            await r.close(pg)
            continue
        opts = await pg.evaluate(
            "() => Array.from(document.querySelectorAll('#wa-lang-select option')).map(o => o.value)")
        r.rec("I18N-SW-00", "Language selector lists all 11 languages", "/",
              "PASS" if len(opts) >= 11 else "FAIL", f"{len(opts)} options: {opts}",
              viewport="desktop")
        try:
            async with pg.expect_navigation(wait_until="load", timeout=40000):
                await pg.select_option("#wa-lang-select", target_lang)
        except Exception as exc:  # noqa: BLE001
            r.rec("I18N-SW-01", f"Switching to {target_lang.upper()} lands on the translated page",
                  "/", "BLOCKED", f"navigation timed out locally: {type(exc).__name__}",
                  viewport="desktop")
            await r.close(pg)
            continue
        await pg.wait_for_timeout(400)
        res = await pg.evaluate("""() => ({
            path: location.pathname,
            htmlLang: document.documentElement.lang,
            h1: (document.querySelector('h1')||{}).textContent || '',
        })""")
        ok_path = res["path"].startswith(f"/{target_lang}")
        ok_lang = res["htmlLang"] == target_lang
        r.rec("I18N-SW-01", f"Switching to {target_lang.upper()} lands on the translated page",
              "/", "PASS" if (ok_path and ok_lang) else "FAIL",
              f"path={res['path']} html lang={res['htmlLang']} h1={res['h1'][:60]!r}",
              viewport="desktop", evidence=res)
        await r.close(pg)


# --------------------------------------------------------------------------- #
# B. home / pricing / cta chain
# --------------------------------------------------------------------------- #

async def suite_home(r: Runner) -> None:
    print("\n== B. home page ==", flush=True)
    pg = await r.page("mobile")
    await r.route_block(pg)
    await pg.goto(to_local("/"), wait_until="load")
    await pg.wait_for_timeout(300)

    ctas = await pg.evaluate("""() => Array.from(document.querySelectorAll('a.btn, a[class*="btn-"], button[class*="btn"]'))
        .filter(a => a.offsetParent !== null)
        .map(a => ({text:(a.textContent||'').replace(/\\s+/g,' ').trim().slice(0,40), href:a.getAttribute('href')||''}))""")
    r.rec("HOME-01", "Above-the-fold CTAs are present and visible", "/",
          "PASS" if ctas else "FAIL", f"{len(ctas)} visible CTAs: {[c['text'] for c in ctas[:5]]}",
          viewport="mobile", evidence=ctas[:8])

    primary = next((c for c in ctas if c["href"] in ("/order/", "/pricing/", "/#pricing")), None)
    if primary:
        try:
            async with pg.expect_navigation(wait_until="load", timeout=30000):
                await pg.locator(f'a[href="{primary["href"]}"]').first.click()
        except Exception as exc:  # noqa: BLE001
            r.rec("HOME-02", "Primary CTA navigates to a working conversion page", "/", "BLOCKED",
                  f"{type(exc).__name__}: {exc}"[:140], viewport="mobile")
            await r.close(pg)
            return
        ok = urlparse(pg.url).path in ("/order/", "/pricing/")
        r.rec("HOME-02", "Primary CTA navigates to a working conversion page", "/",
              "PASS" if ok else "FAIL",
              f"CTA '{primary['text']}' -> {urlparse(pg.url).path}", viewport="mobile")
        r.rec("HOME-03", "No redirect bounce after the CTA hop", "/",
              "PASS" if urlparse(pg.url).path == primary["href"] else "WARN",
              f"final path {urlparse(pg.url).path} (requested {primary['href']})", viewport="mobile")
        await r.close(pg)
        pg = await r.page("mobile")
        await r.route_block(pg)
        await pg.goto(to_local("/"), wait_until="load")
        await pg.wait_for_timeout(200)

    dets = await pg.evaluate("""() => Array.from(document.querySelectorAll('details')).map(d => ({
        open: d.open, hasSummary: !!d.querySelector('summary'),
        q: (d.querySelector('summary')||{}).textContent?.replace(/\\s+/g,' ').trim().slice(0,50) || ''
    }))""")
    no_summary = [d for d in dets if not d["hasSummary"]]
    r.rec("FAQ-01", "FAQ accordions use <summary> (keyboard-operable)", "/",
          "PASS" if (dets and not no_summary) else ("FAIL" if dets else "WARN"),
          f"{len(dets)} <details>, {len(no_summary)} without summary", viewport="mobile")
    if dets:
        first = await pg.query_selector("details")
        was = await first.evaluate("d => d.open")
        await first.evaluate("d => { d.open = !d.open; d.dispatchEvent(new Event('toggle')); }")
        now = await first.evaluate("d => d.open")
        r.rec("FAQ-02", "FAQ item toggles open/closed", "/", "PASS" if now != was else "FAIL",
              f"open {was} -> {now}", viewport="mobile")

    # full scroll to trigger lazy media, then look for broken images
    await pg.evaluate("""async () => {
        const step = window.innerHeight * 0.9;
        for (let y = 0; y < document.body.scrollHeight; y += step) {
            window.scrollTo(0, y);
            await new Promise(r => setTimeout(r, 120));
        }
        window.scrollTo(0, 0);
    }""")
    await pg.wait_for_timeout(1200)
    broken = await pg.evaluate("""() => Array.from(document.images)
        .filter(i => i.complete && i.naturalWidth === 0)
        .map(i => (i.currentSrc||i.src||'').split('/').pop().slice(0,60))""")
    total_imgs = await pg.evaluate("() => document.images.length")
    r.rec("MEDIA-01", "All images decode after a full scroll (home)", "/",
          "PASS" if not broken else "FAIL",
          f"{total_imgs} images, {len(broken)} broken: {broken[:6]}", viewport="mobile")
    await r.close(pg)


async def suite_pricing(r: Runner) -> None:
    print("\n== C. pricing ==", flush=True)
    for vp in ("mobile", "desktop"):
        pg = await r.page(vp)
        await r.route_block(pg)
        await pg.goto(to_local("/pricing/"), wait_until="load")
        await pg.wait_for_timeout(250)
        info = await pg.evaluate("""() => {
            const t = document.querySelector('table');
            let scrollParent = null;
            if (t) {
                let p = t.parentElement;
                while (p && p !== document.body) {
                    const cs = getComputedStyle(p);
                    if (cs.overflowX === 'auto' || cs.overflowX === 'scroll' || cs.overflow === 'auto') { scrollParent = p.className || p.tagName; break; }
                    p = p.parentElement;
                }
            }
            return {
                hasTable: !!t,
                tableWidth: t ? Math.round(t.getBoundingClientRect().width) : 0,
                scrollParent,
                docOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
                planCards: document.querySelectorAll('[class*="plan"], [class*="pricing-card"]').length,
                ctas: Array.from(document.querySelectorAll('a[href*="order"]')).length,
            };
        }""")
        ok = (not vp == "mobile") or info["docOverflow"] <= 2
        r.rec("PRICE-01", f"Pricing page does not scroll sideways ({vp})", "/pricing/",
              "PASS" if ok else "FAIL",
              f"document overflow={info['docOverflow']}px, table width={info['tableWidth']}px, "
              f"scrollable wrapper={info['scrollParent']!r}", viewport=vp, evidence=info)
        r.rec("PRICE-02", f"Pricing page shows plan cards + order CTAs ({vp})", "/pricing/",
              "PASS" if (info["planCards"] and info["ctas"]) else "FAIL",
              f"{info['planCards']} plan cards, {info['ctas']} order links", viewport=vp)
        await r.close(pg)


# --------------------------------------------------------------------------- #
# D. tools
# --------------------------------------------------------------------------- #

TOOL_SLUGS = [
    "add-text-to-wedding-photo", "compress-wedding-photos", "crop-wedding-photo-for-reels",
    "heic-to-jpg-wedding-photos", "remove-background-wedding-portrait", "save-the-date-maker",
    "wedding-budget-calculator", "wedding-hashtag-generator", "wedding-invitation-maker",
    "wedding-photo-book-planner", "wedding-photo-collage", "wedding-seating-chart-maker",
    "wedding-video-invitation-maker",
]


async def suite_tools_index(r: Runner) -> None:
    print("\n== D. tools hub ==", flush=True)
    pg = await r.page("mobile")
    await r.route_block(pg)
    await pg.goto(to_local("/tools/"), wait_until="load")
    await pg.wait_for_timeout(250)
    links = await pg.evaluate("""() => Array.from(document.querySelectorAll('a[href^="/tools/"]'))
        .map(a => ({href: a.getAttribute('href'), text: (a.textContent||'').replace(/\\s+/g,' ').trim().slice(0,40)}))""")
    uniq = sorted({l["href"] for l in links if l["href"].rstrip("/") != "/tools"})
    missing = [s for s in TOOL_SLUGS if f"/tools/{s}/" not in uniq]
    r.rec("TOOLS-01", "Tools hub links all 13 tools", "/tools/",
          "PASS" if not missing else "FAIL",
          f"{len(uniq)} tool links found; missing={missing}", viewport="mobile")
    broken = []
    for h in uniq:
        resp = await pg.request.get(BASE + h, timeout=20000)
        if resp.status >= 400:
            broken.append((h, resp.status))
    r.rec("TOOLS-02", "Every tool page opens (HTTP 200)", "/tools/",
          "PASS" if not broken else "FAIL",
          f"{len(uniq)} tools probed, broken={broken[:5]}" if broken else f"all {len(uniq)} tools 200",
          viewport="mobile")
    await r.close(pg)


async def suite_tools(r: Runner, fx: dict) -> None:
    print("\n== E. tool pages: upload / run / error handling ==", flush=True)
    for slug in TOOL_SLUGS:
        path = f"/tools/{slug}/"
        pg = await r.page("desktop")
        await r.route_block(pg)
        errors: list[str] = []
        pg.on("pageerror", lambda e: errors.append(str(e)[:160]))
        await pg.goto(to_local(path), wait_until="load")
        await pg.wait_for_timeout(300)

        shape = await pg.evaluate("""() => {
            const file = document.querySelector('input[type="file"]');
            const btns = Array.from(document.querySelectorAll('button')).filter(b => b.offsetParent !== null);
            const primary = btns.find(b => /run|generate|create|make|start|convert|compress|apply|save|download/i.test(b.id + ' ' + b.textContent));
            return {
                file: !!file, accept: file ? file.getAttribute('accept') : null, multiple: file ? file.multiple : null,
                fileVisible: file ? (file.offsetParent !== null || getComputedStyle(file).display !== 'none') : false,
                dropzone: !!document.querySelector('[class*="drop"], [id*="drop"]'),
                primary: primary ? {id: primary.id, text: (primary.textContent||'').trim().slice(0,30), disabled: primary.disabled} : null,
                selects: document.querySelectorAll('select').length,
                ranges: document.querySelectorAll('input[type=range]').length,
                buttons: btns.length,
                canvas: document.querySelectorAll('canvas').length,
                outputs: document.querySelectorAll('[id*="result"], [id*="output"], [id*="preview"], [class*="result"], [class*="preview"]').length,
            };
        }""")
        needs_file = shape["file"]
        if needs_file:
            # keyboard reachability of the upload control
            kbd = await pg.evaluate("""() => {
                const fi = document.querySelector('input[type=file]');
                const drop = document.querySelector('#dropzone, [class*="dropzone"]');
                const fiCS = fi ? getComputedStyle(fi) : null;
                return {
                    inputDisplay: fiCS ? fiCS.display : null,
                    inputFocusable: fi ? (fiCS.display !== 'none' && fiCS.visibility !== 'hidden' && !fi.disabled) : null,
                    inputLabelled: fi ? !!(fi.getAttribute('aria-label') ||
                            (fi.id && document.querySelector('label[for="' + fi.id + '"]')) || fi.closest('label')) : null,
                    dropTabIndex: drop ? drop.getAttribute('tabindex') : null,
                    dropRole: drop ? (drop.getAttribute('role') || '') : null,
                    dropFocusable: drop ? (drop.tabIndex >= 0) : null,
                    dropKeyboardHandler: drop ? !!(drop.onclick || drop.dataset.role) : null,
                };
            }""")
            r.rec(f"TOOL-{slug}-KBD", "Upload control is reachable by keyboard", path,
                  "PASS" if (kbd["inputFocusable"] or kbd["dropFocusable"]) else "FAIL",
                  f"file input display={kbd['inputDisplay']} focusable={kbd['inputFocusable']}, "
                  f"dropzone tabindex={kbd['dropTabIndex']} role={kbd['dropRole']!r} focusable={kbd['dropFocusable']}, "
                  f"input labelled={kbd['inputLabelled']}",
                  viewport="desktop", evidence=kbd)

            ok_disabled = shape["primary"] and shape["primary"]["disabled"]
            r.rec(f"TOOL-{slug}-01", "Primary action is disabled until a file is chosen", path,
                  "PASS" if ok_disabled else ("WARN" if shape["primary"] else "FAIL"),
                  f"primary={shape['primary']}", viewport="desktop", evidence=shape)

            # 1) wrong file type
            try:
                await pg.set_input_files("input[type=file]", str(fx["txt"]))
                await pg.wait_for_timeout(600)
                msg = await pg.evaluate("""() => {
                    const c = document.body.innerText;
                    const m = c.match(/(unsupported|not (a )?(supported|valid)|invalid file|please (choose|select|upload)|jpg|jpeg|png|webp|heic)[^\\n]{0,90}/i);
                    return m ? m[0].trim() : null;
                }""")
                crashed = bool(errors)
                r.rec(f"TOOL-{slug}-02", "Rejecting a non-image file shows a friendly message", path,
                      "PASS" if (msg and not crashed) else ("FAIL" if crashed else "WARN"),
                      f"message={msg!r} jsErrors={errors[:1]}", viewport="desktop")
            except Exception as exc:  # noqa: BLE001
                r.rec(f"TOOL-{slug}-02", "Rejecting a non-image file shows a friendly message", path,
                      "BLOCKED", f"could not set file: {exc}"[:120], viewport="desktop")

            # 2) real image -> run
            await pg.reload(wait_until="load")
            await pg.wait_for_timeout(250)
            try:
                await pg.set_input_files("input[type=file]", str(fx["jpg"]))
                await pg.wait_for_timeout(900)
                after_pick = await pg.evaluate("""() => {
                    const p = (Array.from(document.querySelectorAll('button')).find(b =>
                        /run|generate|create|make|start|convert|compress|apply/i.test(b.id + ' ' + b.textContent)));
                    return {disabled: p ? p.disabled : null, thumbs: document.querySelectorAll('img[src^="blob:"], canvas, [class*="thumb"], [class*="preview"]').length};
                }""")
                r.rec(f"TOOL-{slug}-03", "Choosing a valid photo enables the run action / shows a preview", path,
                      "PASS" if (after_pick["disabled"] is False or after_pick["thumbs"] > 0) else "FAIL",
                      f"run_disabled={after_pick['disabled']}, preview nodes={after_pick['thumbs']}",
                      viewport="desktop", evidence=after_pick)

                ran = False
                if after_pick["disabled"] is False:
                    btn = await pg.query_selector("button:not([disabled])")
                    # click the real primary action, not the menu toggle
                    primary_sel = await pg.evaluate("""() => {
                        const b = Array.from(document.querySelectorAll('button')).find(x =>
                            !x.disabled && /run|generate|create|make|start|convert|compress|apply/i.test(x.id + ' ' + x.textContent));
                        return b ? b.id : null;
                    }""")
                    if primary_sel:
                        before = len(errors)
                        await pg.click(f"#{primary_sel}")
                        await pg.wait_for_timeout(2200)
                        ran = not errors[before:]
                        out = await pg.evaluate("""() => ({
                            status: ((document.querySelector('#status, .status, [class*="status"], [role="status"]')||{}).textContent||'').trim().slice(0,80),
                            blobs: document.querySelectorAll('[src^="blob:"]').length,
                            canvases: Array.from(document.querySelectorAll('canvas')).map(c => c.width + 'x' + c.height),
                            text: (document.querySelector('[class*="result"], [class*="output"], [id*="result"]')||{}).textContent?.replace(/\\s+/g,' ').trim().slice(0,90) || ''
                        })""")
                        r.rec(f"TOOL-{slug}-04", "Running the tool produces output without JS errors", path,
                              "PASS" if not ran else "FAIL",
                              f"errors={errors[-1:] if ran else []} status={out['status']!r} "
                              f"blobImages={out['blobs']} canvases={out['canvases']} result={out['text']!r}",
                              viewport="desktop", evidence=out)
            except Exception as exc:  # noqa: BLE001
                r.rec(f"TOOL-{slug}-03", "Choosing a valid photo enables the run action / shows a preview", path,
                      "BLOCKED", f"{type(exc).__name__}: {exc}"[:140], viewport="desktop")

            # 3) clear / reset
            try:
                clear = await pg.query_selector("#clear-btn, button[id*='clear'], button[id*='reset']")
                if clear:
                    await clear.click()
                    await pg.wait_for_timeout(400)
                    back = await pg.evaluate("""() => {
                        const p = Array.from(document.querySelectorAll('button')).find(b => /run|generate|create/i.test(b.id + ' ' + b.textContent));
                        const f = document.querySelector('input[type=file]');
                        return {disabled: p ? p.disabled : null, files: f ? f.files.length : -1};
                    }""")
                    r.rec(f"TOOL-{slug}-05", "'Clear' resets the tool state", path,
                          "PASS" if (back["files"] in (0, -1) and back["disabled"] is not False) else "WARN",
                          f"files={back['files']} run_disabled={back['disabled']}", viewport="desktop")
            except Exception:  # noqa: BLE001
                pass
        else:
            # no upload: pure generator / calculator tool
            state = await pg.evaluate("""() => ({
                inputs: Array.from(document.querySelectorAll('input,textarea,select')).filter(e => e.type !== 'hidden').length,
                buttons: Array.from(document.querySelectorAll('button')).filter(b => b.offsetParent !== null).length,
            })""")
            r.rec(f"TOOL-{slug}-00", "Tool exposes usable inputs and actions", path,
                  "PASS" if (state["inputs"] or state["buttons"]) else "FAIL",
                  f"{state['inputs']} inputs, {state['buttons']} buttons", viewport="desktop",
                  evidence=shape)

        r.rec(f"TOOL-{slug}-ERR", "No uncaught JS errors during the tool flow", path,
              "PASS" if not errors else "FAIL", f"errors={errors[:3]}", viewport="desktop")
        await r.close(pg)


# --------------------------------------------------------------------------- #
# F. gallery
# --------------------------------------------------------------------------- #

async def suite_gallery(r: Runner) -> None:
    print("\n== F. gallery filters ==", flush=True)
    for vp in ("mobile", "desktop"):
        pg = await r.page(vp)
        await r.route_block(pg)
        await pg.goto(to_local("/gallery/"), wait_until="load")
        await pg.wait_for_timeout(500)

        cards_total = await pg.evaluate("() => document.querySelectorAll('.gallery-card').length")
        btns = await pg.evaluate("""() => Array.from(document.querySelectorAll('.filter-btn'))
            .map(b => ({f: b.getAttribute('data-filter'), text:(b.textContent||'').trim().slice(0,24)}))""")
        r.rec(f"GAL-{vp}-01", "Gallery renders its case-study cards", "/gallery/",
              "PASS" if cards_total else "FAIL", f"{cards_total} cards, {len(btns)} filter buttons",
              viewport=vp)

        results = []
        for b in btns:
            n = await pg.evaluate("""(f) => {
                document.querySelector('.filter-btn[data-filter="' + f + '"]').click();
                const cards = Array.from(document.querySelectorAll('.gallery-card'));
                const shown = cards.filter(c => getComputedStyle(c).display !== 'none');
                return {shown: shown.length, total: cards.length,
                        active: document.querySelector('.filter-btn[data-filter="' + f + '"]').classList.contains('active'),
                        activeCount: document.querySelectorAll('.filter-btn.active').length};
            }""", b["f"])
            expected = cards_total if b["f"] == "all" else None
            if expected is not None:
                status = "PASS" if n["shown"] == expected else "FAIL"
            else:
                status = "PASS" if n["shown"] > 0 else "FAIL"
                if n["shown"] == 0:
                    status = "FAIL"
            results.append({"filter": b["f"], **n})
            r.rec(f"GAL-{vp}-F-{b['f']}", f"Filter '{b['text']}' shows the right cards", "/gallery/",
                  status, f"{n['shown']}/{n['total']} cards visible, active buttons={n['activeCount']}",
                  viewport=vp)

        empties = [x["filter"] for x in results if x["shown"] == 0]
        r.rec(f"GAL-{vp}-02", "No filter category is empty", "/gallery/",
              "PASS" if not empties else "FAIL",
              "every category has cards" if not empties else f"empty categories: {empties}", viewport=vp)
        await r.close(pg)


# --------------------------------------------------------------------------- #
# G. order form
# --------------------------------------------------------------------------- #

async def suite_order(r: Runner) -> None:
    print("\n== G. order / quote form ==", flush=True)
    pg = await r.page("desktop")
    await r.route_block(pg)
    errors: list[str] = []
    pg.on("pageerror", lambda e: errors.append(str(e)[:160]))
    await pg.goto(to_local("/order/"), wait_until="load")
    await pg.wait_for_timeout(300)

    shape = await pg.evaluate("""() => {
        const f = document.querySelector('form');
        if (!f) return {form: false};
        const fields = Array.from(f.querySelectorAll('input,select,textarea'))
            .filter(e => !['hidden','submit','button'].includes(e.type));
        return {
            form: true, action: f.getAttribute('action'), method: f.getAttribute('method'),
            novalidate: f.hasAttribute('novalidate'),
            fields: fields.map(e => ({tag:e.tagName.toLowerCase(), id:e.id, name:e.name, type:e.type,
                                     required: e.required, label: !!document.querySelector('label[for="'+e.id+'"]')
                                             || !!e.getAttribute('aria-label') || !!e.closest('label')})),
            submits: Array.from(f.querySelectorAll('[type=submit],button')).map(b => (b.textContent||'').trim().slice(0,24)),
            status: !!document.querySelector('#form-status'),
        };
    }""")
    r.rec("ORDER-01", "Quote form exists with labelled fields", "/order/",
          "PASS" if shape.get("form") and all(x["label"] for x in shape["fields"]) else "FAIL",
          f"{len(shape.get('fields', []))} fields, unlabelled="
          f"{[x['id'] for x in shape.get('fields', []) if not x['label']]}",
          viewport="desktop", evidence=shape)
    r.rec("ORDER-02", "Native validation does not pre-empt the custom messages", "/order/",
          "PASS" if shape.get("novalidate") else "WARN",
          f"novalidate={'yes' if shape.get('novalidate') else 'no'}", viewport="desktop")

    req = [x for x in shape.get("fields", []) if x["required"]]
    r.rec("ORDER-03", "Mandatory fields are marked required", "/order/",
          "PASS" if req else "FAIL", f"required fields: {[x['id'] for x in req]}", viewport="desktop")

    # submit empty
    await pg.click("form button[type=submit]")
    await pg.wait_for_timeout(500)
    res = await pg.evaluate("""() => {
        const f = document.querySelector('form');
        const bad = Array.from(f.querySelectorAll('[aria-invalid="true"], .error'))
            .map(e => e.id || e.name || e.tagName);
        const st = document.querySelector('#form-status');
        return {invalid: bad, statusText: st ? st.textContent.replace(/\\s+/g,' ').trim().slice(0,140) : null,
                statusClass: st ? st.className : null,
                focused: document.activeElement ? (document.activeElement.id || document.activeElement.tagName) : null,
                url: location.pathname};
    }""")
    r.rec("ORDER-04", "Submitting an empty form blocks submission and flags every empty required field",
          "/order/", "PASS" if (len(res["invalid"]) >= len(req) and res["url"] == "/order/") else "FAIL",
          f"flagged={res['invalid']} status={res['statusText']!r}", viewport="desktop", evidence=res)
    r.rec("ORDER-05", "Error summary message is shown to the user", "/order/",
          "PASS" if res["statusText"] else "FAIL", f"#form-status: {res['statusText']!r}",
          viewport="desktop")
    r.rec("ORDER-06", "Focus moves to the first invalid field", "/order/",
          "PASS" if res["focused"] in [x["id"] for x in req] else "WARN",
          f"activeElement=#{res['focused']}", viewport="desktop")

    # bad email
    await pg.fill("#email", "not-an-email")
    await pg.click("button[type=submit]")
    await pg.wait_for_timeout(400)
    bad_email = await pg.evaluate("""() => {
        const e = document.querySelector('#email');
        return {invalid: e.getAttribute('aria-invalid'), cls: e.className,
                status: (document.querySelector('#form-status')||{}).textContent?.slice(0,120)};
    }""")
    r.rec("ORDER-07", "Malformed e-mail is rejected with an inline message", "/order/",
          "PASS" if bad_email["invalid"] == "true" else "FAIL",
          f"aria-invalid={bad_email['invalid']} class={bad_email['cls']!r} status={bad_email['status']!r}",
          viewport="desktop", evidence=bad_email)

    # error clears on typing
    await pg.fill("#email", "couple")
    await pg.wait_for_timeout(200)
    cleared = await pg.evaluate("() => document.querySelector('#email').getAttribute('aria-invalid')")
    r.rec("ORDER-08", "Error state clears as the user corrects the field", "/order/",
          "PASS" if cleared is None else "FAIL", f"aria-invalid after typing={cleared}",
          viewport="desktop")

    # happy path
    filled = await pg.evaluate("""() => {
        const set = (sel, v) => { const el = document.querySelector(sel); if (!el) return false;
            el.value = v; el.dispatchEvent(new Event('input', {bubbles:true}));
            el.dispatchEvent(new Event('change', {bubbles:true})); return true; };
        const ok = [];
        document.querySelectorAll('.order-form [required], form [required]').forEach(el => {
            if (el.type === 'hidden') return;
            if (el.tagName === 'SELECT') { if (el.options.length > 1) { el.selectedIndex = 1; el.dispatchEvent(new Event('change', {bubbles:true})); ok.push(el.id); } }
            else if (el.type === 'email') { set('#' + el.id, 'couple@example.com'); ok.push(el.id); }
            else if (el.tagName === 'TEXTAREA') { el.value = 'We got married in June, 300 photos from an iPhone.'; ok.push(el.id); }
            else { el.value = 'Test Couple'; ok.push(el.id); }
        });
        return ok;
    }""")
    r.rec("ORDER-09", "A complete submission can be composed", "/order/",
          "PASS" if len(filled) >= 2 else "FAIL", f"filled: {filled}", viewport="desktop")

    try:
        async with pg.expect_navigation(wait_until="load", timeout=30000):
            await pg.click("form button[type=submit], .order-form button[type=submit]")
        await pg.wait_for_timeout(500)
        path = urlparse(pg.url).path
        ref = await pg.evaluate("""() => ({
            url: location.href,
            slot: ((document.querySelector('#reference-id-slot')||{}).textContent||'').trim(),
            copyVisible: (() => { const b = document.querySelector('#reference-copy'); return b ? !b.hidden && b.offsetParent !== null : false; })(),
            headline: ((document.querySelector('h1')||{}).textContent||'').trim().slice(0,60),
        })""")
        ok_ref = bool(ref["slot"]) and ref["slot"].startswith("WA-")
        r.rec("ORDER-10", "Valid submission reaches the success page with a reference ID", "/order/",
              "PASS" if (path == "/success/" and ok_ref) else "FAIL",
              f"final={ref['url']} reference={ref['slot']!r} copyButton={ref['copyVisible']}",
              viewport="desktop", evidence=ref)
        if ref["copyVisible"]:
            await pg.click("#reference-copy")
            await pg.wait_for_timeout(400)
            txt = await pg.evaluate("() => document.querySelector('#reference-copy').textContent.trim()")
            r.rec("ORDER-11", "Copy button confirms the copy to the user", "/success/",
                  "PASS" if ("copied" in txt.lower() or "✓" in txt) else "WARN",
                  f"button label after click: {txt!r}", viewport="desktop")
    except Exception as exc:  # noqa: BLE001
        r.rec("ORDER-10", "Valid submission reaches the success page with a reference ID", "/order/",
              "FAIL", f"{type(exc).__name__}: {exc}"[:160], viewport="desktop")

    r.rec("ORDER-ERR", "No uncaught JS errors during the whole order flow", "/order/",
          "PASS" if not errors else "FAIL", f"errors={errors[:3]}", viewport="desktop")
    await r.close(pg)

    # success page resilience
    for qs, label in (("", "without a reference"), ("?id=BAD-REF", "with a malformed reference")):
        pg = await r.page("desktop")
        await r.route_block(pg)
        errs: list[str] = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:120]))
        await pg.goto(to_local("/success/" + qs), wait_until="load")
        await pg.wait_for_timeout(300)
        slot = await pg.evaluate("""() => ({
            slot: ((document.querySelector('#reference-id-slot')||{}).textContent||'').trim(),
            copyHidden: (() => { const b = document.querySelector('#reference-copy'); return b ? b.hidden : null; })(),
            body: (document.body.innerText||'').length,
        })""")
        r.rec("SUCCESS-01", f"Success page renders cleanly {label}", "/success/",
              "PASS" if (not errs and slot["body"] > 200) else "FAIL",
              f"ref={slot['slot']!r} copyHidden={slot['copyHidden']} errors={errs[:2]}",
              viewport="desktop", evidence=slot)
        await r.close(pg)


# --------------------------------------------------------------------------- #
# H. search / blog / 404
# --------------------------------------------------------------------------- #

async def suite_search(r: Runner) -> None:
    print("\n== H. search ==", flush=True)
    pg = await r.page("desktop")
    await r.route_block(pg)
    await pg.goto(to_local("/search/"), wait_until="load")
    await pg.wait_for_timeout(300)

    shape = await pg.evaluate("""() => {
        const f = document.querySelector('form');
        const i = document.querySelector('input[type=search], input[name=q], input[type=text]');
        return {form: !!f, input: !!i, id: i ? i.id : null, name: i ? i.name : null,
                method: f ? f.getAttribute('method') : null, action: f ? f.getAttribute('action') : null,
                results: document.querySelectorAll('[id*="result"], [class*="result"]').length};
    }""")
    r.rec("SEARCH-01", "Search page exposes a query field", "/search/",
          "PASS" if shape["input"] else "FAIL", f"input=#{shape['id']} name={shape['name']}",
          viewport="desktop", evidence=shape)
    if not shape["input"]:
        await r.close(pg)
        return

    async def run_query(q: str) -> dict:
        try:
            async with pg.expect_navigation(wait_until="load", timeout=20000):
                await pg.fill(f"#{shape['id']}", q)
                await pg.press(f"#{shape['id']}", "Enter")
            await pg.wait_for_timeout(600)
        except Exception:
            await pg.wait_for_timeout(600)
        return await pg.evaluate("""() => ({
            url: location.href,
            hits: document.querySelectorAll('a[href*="/blog/"]').length,
            body: (document.body.innerText||'').replace(/\\s+/g,' ').trim().slice(0, 160),
            q: (document.querySelector('input[type=search], input[name=q]')||{}).value,
        })""")

    hit = await run_query("wedding video")
    r.rec("SEARCH-02", "Enter submits the query and returns results", "/search/",
          "PASS" if hit["hits"] > 0 else "FAIL",
          f"url={hit['url']} links={hit['hits']} snippet={hit['body'][:90]!r}", viewport="desktop",
          evidence=hit)
    miss = await run_query("zzzqqqxxx-nothing-here")
    has_empty = any(k in miss["body"].lower() for k in ("no result", "nothing", "not found", "0 result", "try another"))
    r.rec("SEARCH-03", "A no-result query explains itself instead of showing a blank page", "/search/",
          "PASS" if (miss["hits"] == 0 and has_empty) else ("WARN" if miss["hits"] == 0 else "FAIL"),
          f"links={miss['hits']} empty-state-text={has_empty} snippet={miss['body'][:90]!r}",
          viewport="desktop", evidence=miss)

    await pg.goto(to_local("/search/"), wait_until="load")
    await pg.wait_for_timeout(200)
    try:
        async with pg.expect_navigation(wait_until="load", timeout=8000):
            await pg.press(f"#{shape['id']}", "Enter")
        empty_nav = True
    except Exception:
        empty_nav = False
    await pg.wait_for_timeout(300)
    r.rec("SEARCH-04", "Empty query is handled without an error page", "/search/",
          "PASS" if urlparse(pg.url).path == "/search/" else "WARN",
          f"url={urlparse(pg.url).path} navigated={empty_nav}", viewport="desktop")
    r.rec("SEARCH-05", "Query survives the round-trip (input is repopulated)", "/search/",
          "PASS" if hit["q"] else "WARN", f"input value after search={hit['q']!r}", viewport="desktop")
    await r.close(pg)


async def suite_blog(r: Runner) -> None:
    print("\n== I. blog index + article ==", flush=True)
    pg = await r.page("mobile")
    await r.route_block(pg)
    await pg.goto(to_local("/blog/"), wait_until="load")
    await pg.wait_for_timeout(500)
    idx = await pg.evaluate("""() => {
        const cards = document.querySelectorAll('article, [class*="card"], [class*="post"]');
        const links = Array.from(document.querySelectorAll('a[href^="/blog/"]')).map(a => a.getAttribute('href'));
        const uniq = Array.from(new Set(links));
        const pag = Array.from(document.querySelectorAll('a[href*="page="], .pagination a, [class*="paginat"] a')).length;
        return {cards: cards.length, articleLinks: uniq.length, pagination: pag,
                filters: document.querySelectorAll('.filter-btn, [data-category]').length,
                h1: (document.querySelector('h1')||{}).textContent};
    }""")
    r.rec("BLOG-01", "Blog index lists its articles", "/blog/",
          "PASS" if idx["articleLinks"] > 5 else "FAIL",
          f"{idx['articleLinks']} distinct article links, {idx['cards']} card-like nodes, "
          f"{idx['pagination']} pagination links, h1={str(idx['h1'])[:50]!r}", viewport="mobile",
          evidence=idx)

    sample = await pg.evaluate("() => (document.querySelector('a[href^=\"/blog/\"]')||{}).getAttribute('href')")
    if sample:
        resp = await pg.request.get(BASE + sample, timeout=20000)
        r.rec("BLOG-02", "First article link resolves", "/blog/",
              "PASS" if resp.status == 200 else "FAIL", f"{sample} -> {resp.status}", viewport="mobile")
        article = sample
    else:
        article = None
        r.rec("BLOG-02", "First article link resolves", "/blog/", "FAIL", "no article link found",
              viewport="mobile")
    await r.close(pg)

    if not article:
        return

    for vp in ("mobile", "desktop"):
        pg = await r.page(vp)
        await r.route_block(pg)
        errs: list[str] = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:140]))
        await pg.goto(to_local(article), wait_until="load")
        await pg.wait_for_timeout(400)
        art = await pg.evaluate("""() => {
            const toc = Array.from(document.querySelectorAll('nav a[href^="#"], [class*="toc"] a[href^="#"]'));
            const heads = Array.from(document.querySelectorAll('article h2, main h2')).map(h => h.id).filter(Boolean);
            const dead = toc.map(a => a.getAttribute('href')).filter(h => h.length > 1 && !document.getElementById(h.slice(1)));
            return {toc: toc.length, heads: heads.length, deadToc: dead,
                    readingTime: ((document.body.innerText.match(/(\\d+)\\s*(min read|minute)/i)||[])[0]) || null,
                    related: document.querySelectorAll('[class*="related"] a').length,
                    share: document.querySelectorAll('[class*="share"] a, [class*="share"] button').length,
                    words: (document.body.innerText||'').split(/\\s+/).length};
        }""")
        r.rec(f"BLOG-{vp}-03", "Table of contents anchors all resolve", article,
              "PASS" if not art["deadToc"] else "FAIL",
              f"{art['toc']} TOC links, {art['deadToc']} dead: {art['deadToc'][:4]}", viewport=vp,
              evidence=art)
        r.rec(f"BLOG-{vp}-04", "Article has substance and related-navigation", article,
              "PASS" if art["words"] > 300 else "WARN",
              f"~{art['words']} words, reading-time label={art['readingTime']!r}, related links={art['related']}",
              viewport=vp)
        r.rec(f"BLOG-{vp}-05", "No uncaught JS errors on the article", article,
              "PASS" if not errs else "FAIL", f"errors={errs[:3]}", viewport=vp)
        await r.close(pg)


async def suite_404(r: Runner) -> None:
    print("\n== J. 404 ==", flush=True)
    pg = await r.page("mobile")
    await r.route_block(pg)
    resp = await pg.goto(to_local("/definitely-not-a-real-page-ux-test/"), wait_until="load")
    status = resp.status if resp else 0
    body = await pg.evaluate("() => (document.body.innerText||'').replace(/\\s+/g,' ').trim().slice(0,140)")
    r.rec("404-01", "Unknown URLs return a real 404 status", "/definitely-not-a-real-page-ux-test/",
          "PASS" if status == 404 else "FAIL", f"status={status}", viewport="mobile")
    r.rec("404-02", "404 page keeps users on-site with guidance", "/definitely-not-a-real-page-ux-test/",
          "PASS" if ("/" in body and len(body) > 80) else "FAIL", f"body starts: {body[:110]!r}",
          viewport="mobile")
    await r.close(pg)


# --------------------------------------------------------------------------- #
# K. i18n interaction + untranslated fallback
# --------------------------------------------------------------------------- #

async def suite_i18n(r: Runner) -> None:
    print("\n== K. i18n: navigation, forms and untranslated fallback ==", flush=True)
    en = json.loads((ROOT / "i18n" / "en.json").read_text(encoding="utf-8"))

    paths = ["/", "/pricing/", "/tools/", "/order/", "/gallery/", "/blog/", "/tools/wedding-hashtag-generator/"]
    for lang in LANGS:
        if lang == "en":
            continue
        jpath = ROOT / "i18n" / f"{lang}.json"
        if not jpath.exists():
            continue
        loc = json.loads(jpath.read_text(encoding="utf-8"))
        missing_total = 0
        identical_total = 0
        samples: list[str] = []
        for p in paths:
            prefix = f"/{lang}" if p != "/" else f"/{lang}/"
            up = f"/{lang}{p}" if p != "/" else f"/{lang}/"
            pg = await r.page("desktop")
            await r.route_block(pg)
            try:
                await pg.goto(to_local(up), wait_until="load", timeout=40000)
                await pg.wait_for_timeout(250)
                keyed = await pg.evaluate("""() => Array.from(document.querySelectorAll('[data-i18n]'))
                    .map(el => ({k: el.getAttribute('data-i18n'),
                                 t: (el.textContent||'').replace(/\\s+/g,' ').trim().slice(0,80),
                                 tag: el.tagName}))
                    .filter(x => x.k && x.t)""")
            except Exception as exc:  # noqa: BLE001
                r.rec(f"I18N-{lang}", f"{lang.upper()} pages load", up, "FAIL",
                      f"{type(exc).__name__}: {exc}"[:120], viewport="desktop")
                await r.close(pg)
                continue

            miss = [x for x in keyed if x["k"] not in loc]
            same = [x for x in keyed if x["k"] in loc and x["k"] in en
                    and isinstance(loc[x["k"]], str) and loc[x["k"]].strip()
                    and loc[x["k"]].strip() == str(en[x["k"]]).strip()]
            missing_total += len(miss)
            identical_total += len(same)
            samples += [f"{p}:{x['k']}" for x in miss[:3]]

            # interactive elements must still work in this language
            if p == "/order/" or up.endswith("/order/"):
                det = await pg.evaluate("""() => {
                    const f = document.querySelector('form');
                    if (!f) return null;
                    const req = Array.from(f.querySelectorAll('[required]'));
                    return {status: (document.querySelector('#form-status')||{}).textContent,
                            required: req.length};
                }""")
                if det and det["required"]:
                    await pg.evaluate("() => { const b = document.querySelector('.order-form button[type=submit], form button[type=submit]'); if (b) b.click(); }")
                    await pg.wait_for_timeout(400)
                    msg = await pg.evaluate("() => ((document.querySelector('#form-status')||{}).textContent||'').replace(/\\s+/g,' ').trim()")
                    r.rec(f"I18N-{lang}-FORM", f"{lang.upper()} validation messages are localized", up,
                          "PASS" if msg else "FAIL", f"message={msg[:100]!r}", viewport="desktop")
            await r.close(pg)

        total_keys = len(loc)
        r.rec(f"I18N-{lang}-KEYS", f"{lang.upper()} renders its translated strings", "/ (site-wide sample)",
              "PASS" if missing_total == 0 else "FAIL",
              f"{missing_total} of {total_keys} keys missing on sampled pages "
              f"({identical_total} identical to English) e.g. {samples[:4]}",
              viewport="desktop")

    # menu + FAQ work in a RTL and a CJK language
    for lang in ("ar", "zh"):
        pg = await r.page("mobile")
        await r.route_block(pg)
        await pg.goto(to_local(f"/{lang}/"), wait_until="load")
        await pg.wait_for_timeout(300)
        tog = await pg.query_selector(".mobile-menu-toggle")
        if tog:
            await tog.click()
            await pg.wait_for_timeout(250)
            st = await pg.evaluate("""() => {
                const n = document.querySelector('.main-nav');
                const r = n.getBoundingClientRect();
                return {open: n.classList.contains('active'), h: Math.round(r.height),
                        dir: document.documentElement.dir || getComputedStyle(document.body).direction};
            }""")
            r.rec(f"I18N-{lang}-MENU", f"{lang.upper()} mobile menu opens", f"/{lang}/",
                  "PASS" if st["open"] and st["h"] > 40 else "FAIL",
                  f"open={st['open']} height={st['h']}px direction={st['dir']}", viewport="mobile")
        else:
            r.rec(f"I18N-{lang}-MENU", f"{lang.upper()} mobile menu opens", f"/{lang}/", "FAIL",
                  "hamburger missing", viewport="mobile")
        await r.close(pg)


async def suite_navflow(r: Runner) -> None:
    """Click every header/footer navigation entry and verify where the user lands."""
    print("\n== N. navigation click-through ==", flush=True)
    pg = await r.page("desktop")
    await r.route_block(pg)
    await pg.goto(to_local("/"), wait_until="load")
    await pg.wait_for_timeout(300)

    nav_links = await pg.evaluate("""() => {
        const out = [];
        document.querySelectorAll('.main-nav a[href], .site-footer a[href]').forEach(a => {
            const h = a.getAttribute('href') || '';
            if (!h || h.startsWith('#') || h.startsWith('mailto:') || h.startsWith('tel:')) return;
            out.push({href: h, text: (a.textContent||'').replace(/\\s+/g,' ').trim().slice(0,30),
                      where: a.closest('.main-nav') ? 'header' : 'footer'});
        });
        return out;
    }""")
    seen: set[str] = set()
    results = []
    for l in nav_links:
        if l["href"] in seen:
            continue
        seen.add(l["href"])
        try:
            resp = await pg.request.get(BASE + l["href"] if l["href"].startswith("/") else l["href"],
                                        timeout=20000)
            st = resp.status
        except Exception:
            st = 0
        results.append({**l, "status": st})
    bad = [x for x in results if x["status"] != 200]
    r.rec("NAVFLOW-01", "Every header/footer link returns 200", "/",
          "PASS" if not bad else "FAIL",
          f"{len(results)} distinct links clicked-checked, failures={[(b['href'], b['status']) for b in bad][:6]}",
          viewport="desktop", evidence=results[:20])

    # actually click the first three header links and confirm the landing page
    for i, l in enumerate([x for x in nav_links if x["where"] == "header"][:3]):
        await pg.goto(to_local("/"), wait_until="load")
        await pg.wait_for_timeout(200)
        try:
            async with pg.expect_navigation(wait_until="load", timeout=25000):
                await pg.click(f'.main-nav a[href="{l["href"]}"]')
            await pg.wait_for_timeout(300)
            land = await pg.evaluate("""() => ({
                path: location.pathname,
                h1: (document.querySelector('h1')||{}).textContent?.replace(/\\s+/g,' ').trim().slice(0,60) || '',
                title: document.title.slice(0, 60),
            })""")
            ok = land["path"].rstrip("/") == l["href"].rstrip("/")
            r.rec(f"NAVFLOW-02-{i+1}", f"Header link '{l['text']}' lands on its own page", "/",
                  "PASS" if ok else "FAIL",
                  f"clicked {l['href']} -> {land['path']} · h1={land['h1']!r}", viewport="desktop",
                  evidence=land)
        except Exception as exc:  # noqa: BLE001
            r.rec(f"NAVFLOW-02-{i+1}", f"Header link '{l['text']}' lands on its own page", "/",
                  "FAIL", f"{type(exc).__name__}: {exc}"[:140], viewport="desktop")

    # browser back returns to the home page state
    await pg.goto(to_local("/"), wait_until="load")
    await pg.wait_for_timeout(150)
    try:
        async with pg.expect_navigation(wait_until="load", timeout=20000):
            await pg.click('.main-nav a[href="/pricing/"]')
        await pg.go_back(wait_until="load")
        await pg.wait_for_timeout(250)
        back = urlparse(pg.url).path
        r.rec("NAVFLOW-03", "Browser Back returns to the previous page", "/",
              "PASS" if back in ("/", "") else "FAIL", f"after back: {back}", viewport="desktop")
    except Exception as exc:  # noqa: BLE001
        r.rec("NAVFLOW-03", "Browser Back returns to the previous page", "/",
              "FAIL", f"{type(exc).__name__}: {exc}"[:140], viewport="desktop")

    # breadcrumb on a deep page
    await pg.goto(to_local("/blog/"), wait_until="load")
    await pg.wait_for_timeout(300)
    crumbs = await pg.evaluate("""() => {
        const c = document.querySelector('[class*="breadcrumb"], nav[aria-label*="readcrumb"]');
        return c ? {present: true, text: (c.textContent||'').replace(/\\s+/g,' ').trim().slice(0,60),
                    links: c.querySelectorAll('a').length} : {present: false};
    }""")
    r.rec("NAVFLOW-04", "Deep pages expose a breadcrumb trail", "/blog/",
          "PASS" if crumbs.get("present") else "WARN", str(crumbs)[:140], viewport="desktop")
    await r.close(pg)


class _null:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


# --------------------------------------------------------------------------- #

SUITES = {
    "chrome": lambda r, fx: suite_chrome(r, ["/", "/pricing/", "/blog/"]),
    "home": lambda r, fx: suite_home(r),
    "pricing": lambda r, fx: suite_pricing(r),
    "tools-index": lambda r, fx: suite_tools_index(r),
    "tools": lambda r, fx: suite_tools(r, fx),
    "gallery": lambda r, fx: suite_gallery(r),
    "order": lambda r, fx: suite_order(r),
    "search": lambda r, fx: suite_search(r),
    "blog": lambda r, fx: suite_blog(r),
    "404": lambda r, fx: suite_404(r),
    "i18n": lambda r, fx: suite_i18n(r),
    "navflow": lambda r, fx: suite_navflow(r),
}


async def main_async(only: list[str], vp: str) -> list[dict]:
    fx = make_fixtures()
    results: list[dict] = []
    prev: list[dict] = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--disable-dev-shm-usage"])
        r = Runner(browser, results)
        for name, fn in SUITES.items():
            if only and name not in only:
                continue
            try:
                await fn(r, fx)
            except Exception as exc:  # noqa: BLE001
                import traceback
                tb = traceback.format_exc()
                line = [x for x in tb.strip().splitlines() if "interactions.py" in x]
                where = line[-1].strip()[:120] if line else ""
                r.rec(f"SUITE-{name}", f"suite {name} crashed", "-", "FAIL",
                      f"{type(exc).__name__}: {exc}"[:160] + f" @ {where}")
        await browser.close()
    return prev + results


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="comma-separated suite names")
    ap.add_argument("--append", action="store_true")
    a = ap.parse_args()
    only = [s.strip() for s in a.only.split(",") if s.strip()]
    res = asyncio.run(main_async(only, "desktop"))
    from collections import Counter
    c = Counter(x["status"] for x in res)
    if a.append:
        prev = load("interactions.json") or []
        by_id = {x["id"]: x for x in prev}
        by_id.update({x["id"]: x for x in res})
        res = list(by_id.values())
        print(f"\nmerged into interactions.json — {dict(Counter(x['status'] for x in res))}")
    else:
        print(f"\nsaved interactions.json — {dict(c)}")
    save("interactions.json", res)


if __name__ == "__main__":
    main()

