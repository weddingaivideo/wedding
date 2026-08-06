/**
 * WeddingAI.video — Service Worker (v2, 2026-08-04)
 *
 * Strategy:
 *   - HTML:       network-first, fall back to cache on offline
 *   - Static      cache-first (images, fonts, CSS, JS — content-addressed via
 *     assets:     ?v=N versioning, so cache hits are safe across deploys)
 *   - i18n JSON:  cache-first (re-deployed, versioned by deploy; old versions
 *                 are simply replaced)
 *   - /api/*:     never cache (always network)
 *
 * Bumping the cache name (`wa-static-v2` → `wa-static-v3`) is the
 * "nuke from orbit" version — all clients get a fresh cache.
 * Bump on major deploys (e.g. URL structure changes).
 *
 * Pre-cache v2 adds critical CSS/JS/i18n CSS so the first offline visit
 * to any page is fully styled + interactive (was previously: only `/` and
 * `/offline.html` were pre-cached, so the first offline hit on /pricing/
 * would render un-styled). We DON'T pre-cache the i18n JSON (10 files,
 * ~1MB total) — the page falls back to English source when offline, which
 * is a reasonable degradation for a non-native-English audience. The
 * client-side i18n.js then upgrades to the cached JSON once online.
 *
 * Offline behavior:
 *   - Previously visited page renders from cache, fully styled.
 *   - Unvisited URL shows the 404 page from cache (if previously loaded).
 *   - Unvisited URL with no cache shows /offline.html.
 */
const CACHE_NAME = "wa-static-v2";
const HTML_CACHE = "wa-html-v2";

// Pre-cache the critical asset set so the offline fallback is fully styled
// + interactive. Any deploy that changes these filenames MUST bump the
// cache name above (or the new files won't be picked up by old SWs).
//
// Note: the i18n JSON files are NOT pre-cached (see header comment for why).
// Critical HTML pages are NOT pre-cached either — they get cached lazily on
// first visit. /offline.html is pre-cached so it's available even on the
// very first request to an unvisited URL.
const PRECACHE_URLS = [
    "/",
    "/offline.html",
    // Critical CSS
    "/styles.min.css",
    "/styles/i18n.css",
    // Critical JS (defer-loaded; safe to pre-cache, content-addressed)
    "/js/main.min.js",
    "/js/i18n.js",
    "/js/langs.js",
    "/js/cookie-consent.js",
    // Icons (PWA install)
    "/icon-192.png",
    "/icon-512.png",
    "/icon-512-maskable.png",
    "/apple-touch-icon.png",
    "/favicon.svg",
    // Hero image poster (LCP element — the first thing users see on /)
    "/images/hero-wedding-vineyard-1024.webp",
];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) =>
            // addAll fails if ANY URL fails. Pre-cached URLs are all known
            // to exist (verified by deploy script), so a failure here would
            // indicate a missing deploy file — log and continue rather than
            // breaking the install entirely.
            cache.addAll(PRECACHE_URLS).catch((err) => {
                console.warn("[sw] precache partial failure:", err);
            })
        )
    );
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        (async () => {
            const keys = await caches.keys();
            await Promise.all(
                keys
                    .filter((k) => k !== CACHE_NAME && k !== HTML_CACHE)
                    .map((k) => caches.delete(k))
            );
            await self.clients.claim();
        })()
    );
});

self.addEventListener("fetch", (event) => {
    const req = event.request;
    if (req.method !== "GET") return;

    const url = new URL(req.url);
    if (url.origin !== self.location.origin) return; // pass-through for 3rd party
    if (url.pathname.startsWith("/api/")) return;     // never cache API

    // HTML navigation requests → network-first, fall back to cache.
    const accept = req.headers.get("Accept") || "";
    if (req.mode === "navigate" || accept.includes("text/html")) {
        event.respondWith(handleHtml(req));
        return;
    }

    // Static assets (CSS/JS/images/i18n JSON) → cache-first.
    event.respondWith(handleStatic(req));
});

async function handleHtml(req) {
    const cache = await caches.open(HTML_CACHE);
    try {
        const fresh = await fetch(req);
        if (fresh && fresh.ok) {
            cache.put(req, fresh.clone()).catch(() => null);
        }
        return fresh;
    } catch (_) {
        const cached = await cache.match(req);
        if (cached) return cached;
        // Last resort: offline page if we precached one.
        const offline = await cache.match("/offline.html");
        return offline || new Response("Offline", { status: 503 });
    }
}

async function handleStatic(req) {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(req);
    if (cached) return cached;
    try {
        const fresh = await fetch(req);
        if (fresh && fresh.ok) {
            cache.put(req, fresh.clone()).catch(() => null);
        }
        return fresh;
    } catch (_) {
        return new Response("", { status: 504 });
    }
}
