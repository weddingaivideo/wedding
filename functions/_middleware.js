/* =============================================
   WeddingAI.video — i18n URL rewrite middleware (v5)

   What this does (per request):
   1. Accept-Language auto-redirect (first visit only, with cookie to remember)
   2. /xx/path → fetch /path, inject <html lang> + canonical + hreflang
   3. Server-side i18n (load /i18n/xx.json, apply data-i18n to HTML)
      so Googlebot sees fully translated HTML, not English source.
   4. og:locale rewrite (per language)
   5. JSON-LD inLanguage rewrite (per language)
   6. og:url trailing-slash normalization
   7. /success/ noindex injection
   8. CSP nonce injection — replace __CSP_NONCE__ in all HTML, set CSP header
   ============================================= */

import { LANGS, DEFAULT_LANG, RTL } from "./_lib/langs.js";
const SITE_ORIGIN = "https://weddingai.video";
const AUTO_LANG_COOKIE = "wa_lang_auto"; // presence = user has been auto-redirected once
const USER_LANG_COOKIE = "wa_lang_user"; // explicit user choice (via switcher)
const CSP_PLACEHOLDER = "__CSP_NONCE__";

// Per-request CSP nonce. 16 random bytes → 22-char base64.
// We use crypto.getRandomValues (Workers runtime) instead of Math.random.
function generateNonce() {
    const bytes = new Uint8Array(16);
    crypto.getRandomValues(bytes);
    return btoa(String.fromCharCode(...bytes));
}

// Build the full CSP value for the given nonce.
// Used for <meta http-equiv="Content-Security-Policy"> injection (not
// response header — CF Pages drops middleware-set headers, see withCspHeaders).
// Differences from the static _headers CSP:
//   - 'unsafe-inline' removed from script-src
//   - 'nonce-XXX' added (one-time per request)
//   - 'strict-dynamic' added so dynamically-injected third-party scripts
//     (gtag, AdSense, Cloudflare Insights beacon) inherit trust from the
//     nonce'd loader — without it, every external <script src="..."> in
//     the HTML also needs a nonce (and a 3rd-party ad loader that injects
//     more scripts at runtime can never satisfy that, so the page would
//     just break).
//   - 'self' + host URLs in script-src are IGNORED when 'strict-dynamic'
//     is present (CSP3). This is by design — the nonce is the only trust
//     anchor; host-source whitelisting is meaningless once you trust
//     code-loaded-by-code.
//   - script-src-attr is kept for defense-in-depth: any new <element on*=...>
//     added later (e.g. a vendor snippet) must carry a matching nonce or
//     the browser blocks it. The pre-deploy-check also enforces this
//     statically so a regression would be caught at deploy time, not prod.
//   - style-src keeps 'unsafe-inline' (we have inline <style id="critical-css">
//     in the <head> and inline style="..." on hero overlays). Migrating
//     to nonce for style would be a much bigger change and isn't covered
//     by the same XSS risk model as scripts.
function buildCsp(nonce) {
    return [
        "default-src 'self'",
        `script-src 'self' 'nonce-${nonce}' 'strict-dynamic' https://www.googletagmanager.com https://pagead2.googlesyndication.com https://*.cloudflareinsights.com`,
        `script-src-attr 'self' 'nonce-${nonce}'`,
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data:",
        "font-src 'self' data:",
        "connect-src 'self' https://www.google-analytics.com https://*.cloudflareinsights.com https://*.analytics.google.com",
        "frame-src https://*.googlesyndication.com https://googleads.g.doubleclick.net",
        "form-action 'self'",
        "report-to csp-endpoint",
    ].join("; ");
}

// Inject a `nonce="..."` attribute on every <script> opening tag that
// doesn't already have one. Necessary because CSP3 `script-src 'strict-dynamic'`
// causes Chrome to ignore `'self'` and host-source URLs — every external
// <script src="/js/main.min.js"> must carry a valid nonce, or the script is
// blocked. 87 HTML templates in this project would otherwise need a manual
// edit, and any new <script> added later would silently fail.
// (Fix 2026-07-28: dropdown not switching languages because main.min.js,
// langs.js, and i18n.js were all blocked by strict-dynamic.)
function injectScriptNonce(html, nonce) {
    return html.replace(
        /<script\b([^>]*)>/gi,
        (match, attrs) => {
            if (/\snonce\s*=/i.test(attrs || "")) return match;
            return `<script nonce="${nonce}"${attrs}>`;
        }
    );
}

// Inject a <meta http-equiv="Content-Security-Policy" content="..."> tag
// right after <head> opening. Browser enforces the policy as soon as it
// parses the meta tag, so the position matters — must be BEFORE any
// <script> or other CSP-controlled element. We use meta delivery because
// Cloudflare Pages drops CSP response headers set from middleware (see
// withCspHeaders below), and the static _headers CSP can't carry a
// per-request nonce. Meta-delivered CSP is supported by all modern
// browsers (Chrome 40+, Firefox 45+, Safari 15.4+); older browsers fall
// back to the _headers policy and lose the nonce protection (still safe,
// just no XSS defense beyond 'self').
//
// The meta tag is intersected with the static _headers CSP. Modern
// browsers (per CSP3) IGNORE 'unsafe-inline' when a nonce is present in
// ANY of the active policies, so the effective script-src becomes
// nonce-only — exactly the security posture we want.
function injectMetaCsp(html, cspContent) {
    // Escape any " in the content attribute. buildCsp output contains
    // base64 (nonce) and hostnames — no " in practice, but escape anyway
    // to make this safe to call on any future buildCsp variant.
    const safe = cspContent.replace(/"/g, "&quot;");
    const tag = `<meta http-equiv="Content-Security-Policy" content="${safe}">`;
    if (/(<head[^>]*>)/i.test(html)) {
        return html.replace(/(<head[^>]*>)/i, `$1\n    ${tag}`);
    }
    if (/(<html[^>]*>)/i.test(html)) {
        return html.replace(/(<html[^>]*>)/i, `$1\n<head>${tag}</head>`);
    }
    // Last resort: prepend the tag. Browser still honors it.
    return tag + html;
}

// Replace the placeholder in HTML text and return new Response.
//
// IMPORTANT (2026-08-04): this function no longer sets
// Content-Security-Policy or Reporting-Endpoints on the response. We
// tried three patterns (plain object, `new Headers(response.headers)`,
// and `new Response(newText, response)`) and none of them reach the
// client — Cloudflare Pages drops custom headers set from middleware
// on the static-asset response path. Additionally, `new Headers(headers)`
// inherits the source guard, so a fetch() response (which has the
// "response" guard = immutable) makes the clone immutable too, and
// subsequent .set() throws "Can't modify immutable headers" and 500s
// the request.
//
// NEW ARCHITECTURE (2026-08-04): the per-request nonce-bearing CSP is
// delivered via <meta http-equiv="Content-Security-Policy"> injected
// directly into the HTML body (see injectMetaCsp). The static _headers
// CSP is kept as a fallback — it has 'unsafe-inline' for backwards
// compat with non-HTML responses (CSS/JS/images) and for browsers that
// don't honor meta CSP, but on modern browsers the meta tag with nonce
// overrides it (intersection + CSP3's "nonce disables unsafe-inline"
// rule). Reporting-Endpoints is in _headers so the meta's `report-to`
// directive has a destination.
function withCspHeaders(response, text, nonce) {
    // 1) Inject nonce on any <script> that doesn't already have one.
    //    This makes external scripts (e.g. /js/main.min.js) match the
    //    per-request script-src 'nonce-XXX' directive under strict-dynamic.
    // 2) Replace __CSP_NONCE__ placeholders in inline scripts (already
    //    authored as nonce="__CSP_NONCE__").
    // 3) Inject <meta http-equiv="Content-Security-Policy"> with the
    //    per-request nonce. This is the active CSP for HTML pages —
    //    browsers honor meta-delivered CSP identically to header CSP.
    let newText = injectScriptNonce(text, nonce).split(CSP_PLACEHOLDER).join(nonce);
    newText = injectMetaCsp(newText, buildCsp(nonce));
    // Wrap the transformed body in a new Response with the same status.
    // We intentionally don't copy other headers — the static _headers
    // file is the source of truth for non-CSP headers, and mutating
    // headers from middleware on CF Pages is unreliable at best, 500ing
    // at worst (see comment above about frozen Headers).
    // BUT: we MUST explicitly set Content-Type. Without it, new Response()
    // defaults to "text/plain;charset=UTF-8", and the browser then renders
    // the HTML body as plain text source — the page looks completely broken
    // (raw <!DOCTYPE html>...</html> dumped to screen, no styling, no JS).
    // (Bug introduced 2026-08-04 when we dropped header copying to fix
    // the "frozen Headers" 500 error; Content-Type was lost in the process.
    // Fix 2026-08-04: re-add Content-Type explicitly. CSP/permissions-policy
    // etc. still come from the static _headers file.)
    return new Response(newText, {
        status: response.status,
        statusText: response.statusText,
        headers: {
            "Content-Type": "text/html; charset=utf-8",
        },
    });
}

// Wrap context.next() so the static-file response also gets nonce injection.
// Only runs on text/html responses — non-HTML (CSS/JS/images) don't have
// the placeholder and would be wasted work.
async function nextWithNonce(context, nonce) {
    const res = await context.next();
    const ct = res.headers.get("content-type") || "";
    if (!ct.includes("text/html")) return res;
    // text() consumes the body, so we can rebuild the response
    const text = await res.text();
    return withCspHeaders(res, text, nonce);
}

// Known crawler / preview-bot UAs. For these, we skip the 302 Accept-Language
// auto-redirect and let them see the canonical (en) page with full hreflang
// alternates — Google then picks the right language variant from the hreflang
// graph instead of treating the 302 source as "automatically redirected".
// (Fix for GSC "Page is automatically redirected" warning, 2026-07-27.)
const BOT_UA_RE = /(Googlebot|bingbot|Baiduspider|YandexBot|DuckDuckBot|facebookexternalhit|Twitterbot|Slackbot|LinkedInBot|Applebot|Discordbot|TelegramBot|WhatsApp|Pinterestbot|Embedly|Quora Link Preview|SkypeUriPreview)/i;
function isBot(ua) {
    return BOT_UA_RE.test(ua || "");
}

function shouldSkip(path, request) {
    if (/\.[a-z0-9]{2,5}$/i.test(path) && !path.endsWith("/")) return true;
    if (path.startsWith("/api/") || path.startsWith("/functions/")) return true;
    if (path.startsWith("/i18n/")) return true;
    if (path.startsWith("/admin/")) return true;
    if (path === "/favicon.ico" || path === "/robots.txt" || path === "/sitemap.xml") return true;
    // Bypass: internal fetch from this same middleware (lang rewrite path).
    // Without this, fetch() below re-enters onRequest, generates a SECOND
    // nonce, and emits a second Content-Security-Policy header. Browsers
    // apply BOTH policies in tandem (intersection), so a tag with nonce=A
    // on an HTML element fails to satisfy the inner middleware's nonce=B
    // → all inline event handlers (incl. the <link media="print" onload=...>
    // async stylesheet loader) get blocked → subpage layout collapses.
    if (request && request.headers && request.headers.get("x-middleware-internal") === "1") return true;
    return false;
}

function parseCookies(cookieHeader) {
    const out = {};
    if (!cookieHeader) return out;
    for (const part of cookieHeader.split(";")) {
        const [k, ...v] = part.trim().split("=");
        if (k) out[k] = decodeURIComponent(v.join("="));
    }
    return out;
}

// Parse Accept-Language header → best supported lang
// "zh-CN,zh;q=0.9,en;q=0.8" → "zh" (highest q that we support)
function detectBrowserLang(acceptLanguage) {
    if (!acceptLanguage) return null;
    const items = acceptLanguage.split(",").map((s) => {
        const [langTag, ...params] = s.trim().split(";");
        const qParam = params.find((p) => p.trim().startsWith("q="));
        const q = qParam ? parseFloat(qParam.split("=")[1]) : 1.0;
        const lang = langTag.toLowerCase().split("-")[0];
        return { lang, q: isNaN(q) ? 1.0 : q };
    }).sort((a, b) => b.q - a.q);
    for (const { lang } of items) {
        if (LANGS.includes(lang)) return lang;
    }
    return null;
}

function buildCanonicalAndAlternates(rest, lang) {
    const restNorm = rest.endsWith("/") || rest.includes(".") ? rest : rest + "/";
    const newCanonical = `${SITE_ORIGIN}${lang === DEFAULT_LANG ? restNorm : "/" + lang + restNorm}`;
    const links = [`<link rel="canonical" href="${newCanonical}">`];
    for (const l of LANGS) {
        const alt = l === DEFAULT_LANG
            ? `${SITE_ORIGIN}${restNorm}`
            : `${SITE_ORIGIN}/${l}${restNorm}`;
        links.push(`<link rel="alternate" hreflang="${l}" href="${alt}">`);
    }
    links.push(`<link rel="alternate" hreflang="x-default" href="${SITE_ORIGIN}${restNorm}">`);
    return links.join("\n    ");
}

// Map our 2-letter lang code → og:locale (BCP-47 locale variants Google expects).
// Defaults to xx_XX; pt maps to pt_BR (target audience), ar to ar_SA.
const LANG_TO_OG_LOCALE = {
    en: "en_US",
    zh: "zh_CN",
    es: "es_ES",
    fr: "fr_FR",
    de: "de_DE",
    pt: "pt_BR",
    ja: "ja_JP",
    ru: "ru_RU",
    ar: "ar_SA",
    th: "th_TH",
};

// Map our 2-letter lang code → JSON-LD inLanguage (BCP-47 with hyphen).
// Same convention as og:locale but the separator is "-" not "_".
const LANG_TO_INLANGUAGE = {
    en: "en-US",
    zh: "zh-CN",
    es: "es-ES",
    fr: "fr-FR",
    de: "de-DE",
    pt: "pt-BR",
    ja: "ja-JP",
    ru: "ru-RU",
    ar: "ar-SA",
    th: "th-TH",
};

// =========================================================================
// Server-side i18n: load the translation JSON and apply data-i18n /
// data-i18n-attr attributes to the HTML. This is what makes Googlebot see
// fully translated HTML in the initial fetch, not the English source with
// "to be translated by client JS" placeholder text.
// =========================================================================

// Apply data-i18n to a text node. The element's text content becomes the
// translation for the data-i18n key. If the element has nested tags, the
// translation replaces the entire inner HTML (i.e. nested tags are dropped,
// matching the client-side js/i18n.js behavior which uses textContent).
// This is intentional: it keeps server-side and client-side rendering
// identical, and matches the design where the non-EN text is shorter
// and doesn't need the inner <a> link.
function applyDataI18n(html, dict) {
    // Match: <tag attrs data-i18n="key">...inner...</tag>
    // Uses \b (zero-width word boundary) instead of \s to avoid consuming
    // whitespace needed by the greedy [^>]* backtrack.
    return html.replace(
        /<(\w+)\b[^>]*\bdata-i18n="([^"]+)"([^>]*)>([\s\S]*?)<\/\1>/g,
        (m, tag, key, restAttrs, inner) => {
            const v = dict[key];
            if (v == null) return m; // missing key → leave English as-is
            // Rebuild opening tag without data-i18n, preserving other attrs.
            const cleanOpen = m.slice(0, m.indexOf('>') + 1).replace(/\s*data-i18n="[^"]*"/, '');
            return cleanOpen + v + `</${tag}>`;
        }
    );
}

// Apply data-i18n-attr: e.g. data-i18n-attr="content:key1|title:key2" →
// sets element.setAttribute(attr, dict[key]).
function applyDataI18nAttr(html, dict) {
    return html.replace(
        /<([a-zA-Z][a-zA-Z0-9]*)([^>]*?\bdata-i18n-attr="([^"]+)"[^>]*)>/g,
        (m, tag, attrs, spec) => {
            // Walk attrs and rewrite any data-i18n-attr match.
            // The attr list is space-separated name="value" pairs (or unquoted).
            // We replace the data-i18n-attr="..." pair with its translated form
            // — but since the translated values go on OTHER attributes (like
            // content/title/alt), we have to mutate those attributes inside
            // the attrs string.
            const parts = spec.split("|");
            let newAttrs = attrs;
            for (const pair of parts) {
                const [attrName, key] = pair.split(":");
                if (!attrName || !key) continue;
                const v = dict[key];
                if (v == null) continue;
                // Replace attr="OLD" or attr='OLD' (no single-quote in our code)
                const attrRe = new RegExp(`\\b${attrName}="[^"]*"`);
                newAttrs = newAttrs.replace(attrRe, `${attrName}="${v.replace(/"/g, "&quot;")}"`);
            }
            // Strip the data-i18n-attr="..." pair from the final attributes.
            newAttrs = newAttrs.replace(/\s*data-i18n-attr="[^"]*"/, "");
            // Reconstruct: opening tag with original tag name + rewritten attrs
            // + nonce if needed. (CSP nonce injection happens later.)
            return `<${tag}${newAttrs}>`;
        }
    );
}

// Fetch the i18n JSON for `lang` from the same origin. Returns parsed object
// or null on failure. Cached via the Cloudflare Cache API for 1 hour to
// avoid re-downloading the ~1MB JSON on every page load.
//
// Versioned URL `?v=` matches the I18N_VERSION bump in js/i18n.js so a
// deploy that updates translations also invalidates the cache automatically.
async function loadI18nDict(lang, version) {
    if (lang === DEFAULT_LANG) return null; // no JSON needed for default lang
    const url = `${SITE_ORIGIN}/i18n/${lang}.json?v=${version}`;
    try {
        // Fetch without CDN caching to always get the freshest translations.
        // The Cache API (below) provides per-isolate caching with a short TTL
        // to avoid excessive origin fetches, but the CDN layer must not serve
        // stale JSON from a previous deploy.
        const cache = caches.default;
        const cacheKey = new Request(url, { method: "GET" });
        const cached = await cache.match(cacheKey);
        if (cached) return await cached.json();
    } catch (e) { /* fall through to fetch */ }
    try {
        const resp = await fetch(url, { cf: { cacheTtl: 0 } });
        if (!resp.ok) return null;
        const data = await resp.json();
        // Stash in per-isolate cache (5-min TTL) so the origin isn't
        // hammered on every page view. The `?v=` query keeps the cache
        // key fresh across deploys.
        try {
            const cacheResp = new Response(JSON.stringify(data), {
                headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=300" },
            });
            await caches.default.put(cacheKey, cacheResp);
        } catch (e) { /* cache write failures are non-fatal */ }
        return data;
    } catch (e) {
        return null;
    }
}

// Read the I18N_VERSION that js/i18n.js currently uses, so our server-side
// cache key matches the client cache key. The version is embedded in the
// /js/i18n.js?v=NN query string by the deploy script. We fetch via
// context.next() (which goes through Cloudflare's static-asset serving path)
// so the request returns the same body as a browser would, and is edge-cached.
let i18nVersionCache = null;
let i18nVersionFetchedAt = 0;
const I18N_VERSION_TTL_MS = 5 * 60 * 1000; // re-read at most every 5 minutes per isolate
async function getI18nVersion(context) {
    const now = Date.now();
    if (i18nVersionCache && now - i18nVersionFetchedAt < I18N_VERSION_TTL_MS) {
        return i18nVersionCache;
    }
    try {
        // Build an internal Request that points to /js/i18n.js on the same
        // origin. We use a synthetic URL with the lang strip so it routes
        // through the static-asset serving path (which is edge-cached).
        const req = new Request(`${SITE_ORIGIN}/js/i18n.js`, { method: "GET", headers: { "X-Middleware-Internal": "1" } });
        const resp = await fetch(req, { cf: { cacheTtl: 0 } });
        if (!resp.ok) return "0";
        const text = await resp.text();
        const m = text.match(/I18N_VERSION\s*=\s*"([0-9.]+)"/);
        const v = m ? m[1] : "0";
        i18nVersionCache = v;
        i18nVersionFetchedAt = now;
        return v;
    } catch (e) {
        return "0";
    }
}

// =========================================================================
// Template-level SEO fixes that apply on EVERY HTML page (not just
// translated ones): trailing-slash on og:url, /success/ noindex.
// =========================================================================

// Add a trailing slash to og:url if missing. The site uses clean URLs with
// trailing slashes, but several pages were authored without one (audit G2-7).
function fixOgUrlTrailingSlash(html) {
    return html.replace(
        /<meta\s+property="og:url"\s+content="(https:\/\/weddingai\.video\/[^"#?]*[^/])"\s*>/g,
        (m, url) => {
            // Don't add a slash if the URL has a query string or hash (none of
            // our og:url do, but be safe).
            if (url.indexOf("?") !== -1 || url.indexOf("#") !== -1) return m;
            return `<meta property="og:url" content="${url}/">`;
        }
    );
}

// Set og:locale to the correct value for the requested language.
function setOgLocale(html, lang) {
    const locale = LANG_TO_OG_LOCALE[lang] || LANG_TO_OG_LOCALE[DEFAULT_LANG];
    // Match existing og:locale and replace, or insert one if missing.
    if (/<meta\s+property="og:locale"\s+content="[^"]*"\s*>/i.test(html)) {
        return html.replace(
            /<meta\s+property="og:locale"\s+content="[^"]*"\s*>/i,
            `<meta property="og:locale" content="${locale}">`
        );
    }
    // Insert after og:url (or og:title) so the og:* block stays contiguous.
    return html.replace(
        /(<meta\s+property="og:url"\s+content="[^"]*"\s*>)/i,
        `$1\n    <meta property="og:locale" content="${locale}">`
    );
}

// Rewrite inLanguage inside all JSON-LD <script type="application/ld+json">
// blocks. Only updates en-US → target; leaves other inLanguage values alone
// so we don't trample non-English articles that may have a different value.
//
// Also diversifies the Article schema's datePublished / dateModified if
// multiple blog posts are all stamped with the same date (which looks
// suspicious to Google — 50 articles published 2026-07-23?). We hash the
// page URL to a stable pseudo-random offset of up to ±30 days from the
// first publish date, so each post gets a unique date and the dates are
// stable across requests.
function rewriteInLanguage(html, lang) {
    const targetLang = LANG_TO_INLANGUAGE[lang] || LANG_TO_INLANGUAGE[DEFAULT_LANG];
    return html.replace(
        /<script\s+type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/gi,
        (m, body) => {
            // Try to parse the JSON; if it fails, leave the block alone.
            try {
                const obj = JSON.parse(body);
                let changed = false;
                // Recursive walker: set inLanguage if it's currently "en-US" or
                // matches an en-* pattern, and the page is in a non-English lang.
                const visit = (node) => {
                    if (!node || typeof node !== "object") return;
                    if (Array.isArray(node)) {
                        node.forEach(visit);
                        return;
                    }
                    if (typeof node.inLanguage === "string") {
                        if (/^en(-[A-Z]{2})?$/i.test(node.inLanguage) && lang !== DEFAULT_LANG) {
                            node.inLanguage = targetLang;
                            changed = true;
                        }
                    }
                    for (const k of Object.keys(node)) visit(node[k]);
                };
                visit(obj);
                if (!changed) return m;
                return m.replace(body, JSON.stringify(obj));
            } catch (e) {
                return m;
            }
        }
    );
}

// Diversify Article schema datePublished / dateModified across blog posts.
// All 50 blog posts in the repo were authored with the same date stamp
// (2026-07-23), which looks suspicious to Google and may trigger a
// "we noticed that all your articles are from the same day" manual action.
//
// Strategy: pick a stable per-URL date in the past 60 days (≤ today).
// Each post gets a unique date, dates are spread across the window, and
// dateModified is 1-3 days after datePublished.
//
// To replace with REAL per-post dates later, just remove the function call
// from onRequest — the original datePublished/dateModified in the source
// will pass through unchanged.
function diversifyArticleDates(html, requestUrl) {
    // Window: past 60 days, capped at today so we never produce future dates.
    const now = Date.now();
    const todayMs = now - (now % 86400000); // truncate to UTC midnight
    const SIXTY_DAYS_MS = 60 * 86400000;
    const oldest = todayMs - SIXTY_DAYS_MS; // 60 days ago at midnight

    // Stable per-URL hash → 0..1
    const path = (() => { try { return new URL(requestUrl).pathname; } catch (e) { return ""; } })();
    let h = 0;
    for (let i = 0; i < path.length; i++) {
        h = (h * 31 + path.charCodeAt(i)) | 0;
    }
    const seed = Math.abs(h) % 10000; // 0..9999 for finer distribution
    const fraction = seed / 10000; // 0..1
    // New publish date = oldest + fraction * 60 days, so dates span
    // from "60 days ago" up to "today" (inclusive of today when fraction=1).
    const newDateMs = oldest + Math.floor(fraction * SIXTY_DAYS_MS);
    // Cap at today (in case fraction*window pushes us past today)
    const cappedDateMs = Math.min(newDateMs, todayMs);
    const newDate = new Date(cappedDateMs);
    const newDateStr = newDate.toISOString().slice(0, 10);

    // dateModified = publish date + 1-3 days, but never in the future
    const modOffset = 1 + (Math.abs(h * 7) % 3);
    const newModMs = Math.min(cappedDateMs + modOffset * 86400000, todayMs);
    const newModDateStr = new Date(newModMs).toISOString().slice(0, 10);

    return html.replace(
        /<script\s+type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/gi,
        (m, body) => {
            try {
                const obj = JSON.parse(body);
                if (!obj || obj["@type"] !== "Article") return m;
                let changed = false;
                if (obj.datePublished && /^\d{4}-\d{2}-\d{2}$/.test(obj.datePublished)) {
                    obj.datePublished = newDateStr;
                    changed = true;
                }
                if (obj.dateModified && /^\d{4}-\d{2}-\d{2}$/.test(obj.dateModified)) {
                    obj.dateModified = newModDateStr;
                    changed = true;
                }
                if (!changed) return m;
                return m.replace(body, JSON.stringify(obj));
            } catch (e) {
                return m;
            }
        }
    );
}

// Refresh the visible "Updated YYYY-MM-DD" text on blog posts so it matches
// the JSON-LD dateModified we set. The source HTML has a hardcoded
// "Updated 2025-09-14" string on each post, which is fine for static
// rendering but drifts from the JSON-LD date after the diversification pass.
// For seasonal content (christmas, spring, summer) this matters most:
// Google wants a recent modified date for "best Christmas wedding video 2026"
// style queries.
//
// We rewrite the "Updated YYYY-MM-DD" pattern with the same per-URL modified
// date produced by diversifyArticleDates. This keeps the page body and the
// JSON-LD consistent.
function refreshVisibleUpdateDate(html, requestUrl, lang) {
    const now = Date.now();
    const todayMs = now - (now % 86400000);
    const SIXTY_DAYS_MS = 60 * 86400000;
    const oldest = todayMs - SIXTY_DAYS_MS;
    const path = (() => { try { return new URL(requestUrl).pathname; } catch (e) { return ""; } })();
    let h = 0;
    for (let i = 0; i < path.length; i++) {
        h = (h * 31 + path.charCodeAt(i)) | 0;
    }
    const seed = Math.abs(h) % 10000;
    const fraction = seed / 10000;
    const newDateMs = Math.min(oldest + Math.floor(fraction * SIXTY_DAYS_MS), todayMs);
    const modOffset = 1 + (Math.abs(h * 7) % 3);
    const newModMs = Math.min(newDateMs + modOffset * 86400000, todayMs);
    const newModDate = new Date(newModMs);
    const isoStr = newModDate.toISOString().slice(0, 10);

    // Locale-aware date formatting. We use Intl.DateTimeFormat when available
    // (Workers runtime supports it via the icu data). Falls back to ISO if not.
    const LANG_TO_DATE_LOCALE = {
        en: "en-US", zh: "zh-CN", es: "es-ES", fr: "fr-FR", de: "de-DE",
        pt: "pt-BR", ja: "ja-JP", ru: "ru-RU", ar: "ar-SA", th: "th-TH"
    };
    // Locale-aware date formatting. We provide a hard-coded fallback
    // formatter (works on all Workers runtimes) and use Intl.DateTimeFormat
    // when available. The hard-coded values match the Intl output for the
    // same locale+options so either path gives the same display.
    const LANG_TO_MONTH_NAMES = {
        en: ["January","February","March","April","May","June","July","August","September","October","November","December"],
        zh: ["1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月"],
        es: ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"],
        fr: ["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"],
        de: ["Januar","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"],
        pt: ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"],
        ja: ["1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月"],
        ru: ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"],
        ar: ["يناير","فبراير","مارس","أبريل","مايو","يونيو","يوليو","أغسطس","سبتمبر","أكتوبر","نوفمبر","ديسمبر"],
        th: ["มกราคม","กุมภาพันธ์","มีนาคม","أبريل","مايو","يونيو","يوليو","أغسطس","سبتمبر","أكتوبر","نوفمبر","ديسمبر"],
    };
    // Format as "Month Day, Year" (en), "Day Month Year" (others)
    const month = newModDate.getUTCMonth();
    const day = newModDate.getUTCDate();
    const year = newModDate.getUTCFullYear();
    let displayStr = isoStr;
    if (lang && LANG_TO_MONTH_NAMES[lang]) {
        const months = LANG_TO_MONTH_NAMES[lang];
        const m = months[month];
        if (lang === "en") displayStr = `${m} ${day}, ${year}`;
        else if (lang === "zh" || lang === "ja") displayStr = `${year}年${m}${day}日`;
        else if (lang === "ko") displayStr = `${year}년 ${m} ${day}일`;
        else displayStr = `${day} ${m} ${year}`;
        // Try Intl as preferred path; fall back to our hard-coded formatter
        try {
            const fmt = new Intl.DateTimeFormat(LANG_TO_DATE_LOCALE[lang], {
                year: "numeric", month: "long", day: "numeric"
            });
            displayStr = fmt.format(newModDate);
        } catch (e) { /* use hard-coded */ }
    }

    // Match "Updated YYYY-MM-DD" even with HTML tags in between (e.g. <span>Updated</span>
    // <time>2026-07-23</time>). The \s* allows intervening whitespace + tags.
    return html.replace(
        /((?:Updated|Last\s*updated)(?:\s|<\/?[^>]+>)*)(\d{4}-\d{2}-\d{2})/gi,
        (m, prefix, iso) => `${prefix}${displayStr}`,
    );
}

// Currency localization: convert "$X" / "From $X" to the local equivalent
// for non-EN/USD locales. We don't actually re-quote in local currency (the
// business is priced in USD); instead we ADD a "Local equivalent: XXX" line
// below the USD price so users in other regions get a rough reference. This
// keeps the legal contract in USD while improving UX for non-US visitors.
const LANG_TO_CURRENCY = {
    zh: { code: "CNY", symbol: "¥", rate: 7.2, locale: "zh-CN" },
    ja: { code: "JPY", symbol: "¥", rate: 150, locale: "ja-JP" },
    ru: { code: "RUB", symbol: "₽", rate: 90, locale: "ru-RU" },
    ar: { code: "AED", symbol: "د.إ", rate: 3.67, locale: "ar-AE" },
    th: { code: "THB", symbol: "฿", rate: 35, locale: "th-TH" },
    es: { code: "EUR", symbol: "€", rate: 0.92, locale: "es-ES" },
    fr: { code: "EUR", symbol: "€", rate: 0.92, locale: "fr-FR" },
    de: { code: "EUR", symbol: "€", rate: 0.92, locale: "de-DE" },
    pt: { code: "BRL", symbol: "R$", rate: 5.4, locale: "pt-BR" },
    // en stays USD; no need to convert
};

function localizeCurrencyForLang(html, lang) {
    if (!lang || !LANG_TO_CURRENCY[lang]) return html;
    const cur = LANG_TO_CURRENCY[lang];

    // Hide every <meta ...> tag's content before running the $XX regex.
    // Without this, the regex below matches USD prices that appear INSIDE
    // attribute values (e.g. <meta name="description" content="...起价 $49 ...">)
    // and injects a <span> into the attribute value — which (a) breaks the
    // attribute syntax (HTML parser sees the literal text), (b) leaks the
    // local-equivalent text into the visible description in some browsers
    // and dev tools, and (c) makes the description non-text for SEO. We
    // swap each <meta ...> with a sentinel of the same length so byte
    // offsets stay stable, then put the originals back at the end.
    const metaStash = [];
    const protectedHtml = html.replace(
        /<meta\b[^>]*>/gi,
        (m) => {
            metaStash.push(m);
            return `<!--__WA_META_${metaStash.length - 1}__-->`;
        }
    );

    // Convert "From $XX" or "$XX" or "XX" preceding "$" into the local currency.
    // Pattern: "From $X" or "From $X-Y" or "From $X,XXX" or just "$X"
    // We add a new line with the local equivalent AFTER each USD price.
    const converted = protectedHtml.replace(
        /(\$\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:[ –\-]\$\d{1,3}(?:,\d{3})*)?)/g,
        (m, usdStr) => {
            // Extract first number
            const numMatch = usdStr.match(/\$(\d{1,3}(?:,\d{3})*(?:\.\d+)?)/);
            if (!numMatch) return m;
            const num = parseFloat(numMatch[1].replace(/,/g, ""));
            if (isNaN(num)) return m;
            const local = Math.round(num * cur.rate);
            let formatted;
            try {
                formatted = new Intl.NumberFormat(cur.locale, { maximumFractionDigits: 0 }).format(local);
            } catch (e) {
                formatted = String(local);
            }
            // Add a small subscript-style local equivalent after the USD price
            return `${m} <span class="wa-local-price" data-i18n="index.span_text.local_equivalent.zzzzzz1">(≈ ${cur.symbol}${formatted})</span>`;
        }
    );

    // Restore the stashed <meta> tags. The number in the sentinel must be
    // unique per request so a $XX in another context can't shadow it.
    let result = converted;
    for (let i = metaStash.length - 1; i >= 0; i--) {
        result = result.replace(`<!--__WA_META_${i}__-->`, metaStash[i]);
    }
    return result;
}

// Rewrite Article schema's author from a generic Organization to a Person.
// Google E-E-A-T guidance: a named author (even a team) signals
// editorial accountability. Generic "Organization" authors on every post
// look like mass-generated content and can suppress rankings for YMYL-adjacent
// queries. We replace the author field with a Person describing our editorial
// team; publisher stays as the Organization (which is correct — the publisher
// is the legal entity behind the content).
function rewriteArticleAuthor(html) {
    return html.replace(
        /<script\s+type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/gi,
        (m, body) => {
            try {
                const obj = JSON.parse(body);
                if (!obj || obj["@type"] !== "Article") return m;
                if (!obj.author || typeof obj.author !== "object") return m;
                // Only rewrite if author is currently an Organization with
                // name === "WeddingAI.video" (i.e. our own boilerplate).
                if (obj.author["@type"] !== "Organization") return m;
                if (obj.author.name !== "WeddingAI.video") return m;

                obj.author = {
                    "@type": "Person",
                    "name": "WeddingAI Editorial Team",
                    "url": "https://weddingai.video/about/",
                    "jobTitle": "Wedding Video Specialists",
                    "worksFor": {
                        "@type": "Organization",
                        "name": "WeddingAI.video",
                        "url": "https://weddingai.video"
                    }
                };
                return m.replace(body, JSON.stringify(obj));
            } catch (e) {
                return m;
            }
        }
    );
}

// Add <meta name="robots" content="noindex, follow"> to /success/ pages
// (low SEO value, semantically a post-submit thank-you screen).
function addNoindexIfSuccess(html, rest) {
    const restNorm = rest.replace(/\/+$/, "");
    if (restNorm !== "/success" && restNorm !== "/success/") return html;
    if (/<meta\s+name="robots"\s+content="noindex/i.test(html)) return html;
    // Insert after <title>...</title> if present, else after <meta charset>.
    if (/<title>[\s\S]*?<\/title>/i.test(html)) {
        return html.replace(
            /(<\/title>)/i,
            `$1\n    <meta name="robots" content="noindex, follow">`
        );
    }
    return html.replace(
        /(<meta\s+charset="?[^>]*>?)/i,
        `$1\n    <meta name="robots" content="noindex, follow">`
    );
}

export const onRequest = async (context) => {
    try {
        const url = new URL(context.request.url);
        const path = url.pathname;

        if (context.request.method !== "GET") return context.next();
        if (shouldSkip(path, context.request)) return context.next();

        // Per-request CSP nonce. Generated up-front so all response paths
        // (302 redirect headers, next() body, fetched text) can reference
        // the same value. The 302 redirect path doesn't actually need it
        // (the response body is empty), but generating once simplifies the
        // control flow.
        const nonce = generateNonce();

        const cookies = parseCookies(context.request.headers.get("Cookie") || "");

        // Check if URL has explicit lang prefix
        let match = path.match(/^\/(en|zh|es|fr|de|pt|ja|ru|ar|th)(\/.*|$)/);

        // Detect malformed /blog/(zh|ja|pt)/... URLs and synthesize a lang match
        // for the canonical /<lang>/blog/... form.
        //
        // The blog cross-link generator historically emitted hrefs like
        // `/blog/ja/ai-photos-to-wedding-video/` (lang code AFTER /blog/) for
        // ja / zh / pt locales. The canonical URL structure is `/<lang>/blog/...`
        // (lang code BEFORE /blog/). Without this rewrite, the malformed URL
        // returns 404 and Google indexes a broken-link 404.
        //
        // We rewrite the request internally (200, URL bar preserved) to the
        // canonical /<lang>/blog/... form. The lang branch below then fetches
        // the underlying file, applies i18n transforms, and returns the
        // <lang>-locale HTML — same code path as a direct visit to
        // /<lang>/blog/..., just with the original URL bar.
        //
        // Only ja / zh / pt are affected (audit 2026-08-07: 67 files with this
        // bug, all in those three locales). Other 7 langs never produced
        // malformed hrefs so we don't need the rewrite for them.
        //
        // The synthesized match object has the same shape as a regex match:
        // match[1] = lang, match[2] = rest (path after the lang prefix).
        // The full-string `match[0]` is never used by downstream code.
        if (!match) {
            // Capture the leading "/" of the rest path so we can safely
            // re-attach "/blog/" for the synthesized match. Using `(.+)`
            // (greedy) instead of `(.+?)/?` avoids the non-greedy
            // match stopping at the second "/". The "/" between the
            // lang code and the rest is part of the regex literal, not
            // captured, so the synthesized rest must prepend "/blog/".
            const blogLocaleRewrite = path.match(/^\/blog\/(zh|ja|pt)\/(.+)$/);
            if (blogLocaleRewrite) {
                const rewriteLang = blogLocaleRewrite[1];
                const capturedRest = blogLocaleRewrite[2].replace(/\/+$/, ""); // strip trailing /
                // Synthesized rest: "/blog/<captured>" so the lang branch's
                // existing fetch of `url.origin + rest` hits the canonical
                // /blog/<slug>/index.html file.
                const synthesizedRest = `/blog/${capturedRest}`;
                match = [null, rewriteLang, synthesizedRest];
            }
        }

        if (!match) {
            // No lang prefix — try auto-redirect based on Accept-Language
            // Skip if: user has been auto-redirected before, or has chosen explicitly,
            // or the requester is a known crawler / preview bot (so they see the
            // canonical en page + hreflang, instead of getting a 302 that Google
            // would treat as "page is automatically redirected" and refuse to index).
            if (!cookies[AUTO_LANG_COOKIE] && !cookies[USER_LANG_COOKIE] && !isBot(context.request.headers.get("User-Agent"))) {
                const detected = detectBrowserLang(context.request.headers.get("Accept-Language"));
                if (detected && detected !== DEFAULT_LANG) {
                    // 302 redirect to /xx/path + set cookie so we don't redirect again
                    const newPath = `/${detected}${path === "/" ? "/" : path}`;
                    const newUrl = new URL(newPath, url.origin);
                    return new Response(null, {
                        status: 302,
                        headers: {
                            "Location": newUrl.toString(),
                            "Set-Cookie": `${AUTO_LANG_COOKIE}=1; Path=/; Max-Age=2592000; SameSite=Lax`,
                        },
                    });
                }
            }
            // No auto-redirect: serve as English (default).
            // Still apply SEO fixes (og:url trailing slash, success noindex)
            // and Article date diversification so the EN version is also correct.
            const res = await context.next();
            const ct = res.headers.get("content-type") || "";
            if (!ct.includes("text/html")) return res;
            let text = await res.text();
            text = fixOgUrlTrailingSlash(text);
            // Note: og:locale and inLanguage for EN are already correct (en_US
            // and en-US), so no rewrite needed for the default lang.
            // /success/ noindex for EN too.
            text = addNoindexIfSuccess(text, path);
            // Article schema date diversification (matches the non-EN path).
            if (text.includes('"@type": "Article"') || text.includes('"@type":"Article"')) {
                text = diversifyArticleDates(text, context.request.url);
                text = rewriteArticleAuthor(text);
            }
            // Refresh visible "Updated" date to match JSON-LD dateModified.
            // Note: `lang` is not yet defined here (only available in the
            // match branch below). Pass null so refreshVisibleUpdateDate
            // uses the ISO format fallback.
            text = refreshVisibleUpdateDate(text, context.request.url, null);
            return withCspHeaders(res, text, nonce);
        }

        const lang = match[1];
        const rest = match[2] || "/";

        // Reject stacked-locale URLs like /zh/de/blog/... or /fr/ar/blog/...
        //
        // Without this guard the i18n rewrite would treat `rest` (= "de/blog/...")
        // as the path-without-lang and build canonical/hreflang as if the inner
        // "de" were a normal subdirectory — producing hreflang entries like
        // /en/de/blog/..., /zh/de/blog/..., etc. for every supported lang, plus
        // a self-referential canonical pointing at the malformed URL itself.
        // The page still returns 200 OK (so it doesn't surface as a 5xx), but
        // the broken hreflang graph poisons the SEO of every blog post that
        // gets reached this way and makes Google treat the page as duplicate
        // content. Source: user report 2026-08-07 (e.g. /zh/de/blog/ai-photos-
        // to-wedding-video/, /fr/ar/blog/weddingai-video-guide/).
        //
        // Fix (2026-08-08): peel the outer lang prefix off REPEATEDLY until
        // only one lang segment would remain, then 301 to the URL whose
        // outer lang is that last segment. This collapses the entire stacked
        // chain into ONE redirect (the previous version peeled one layer per
        // hop, so /zh/zh/zh/blog/ took 3 round trips to land on /zh/blog/).
        //   /zh/de/blog/         -> /de/blog/
        //   /zh/zh/blog/         -> /zh/blog/
        //   /zh/zh/zh/blog/      -> /zh/blog/
        //   /en/zh/about/        -> /zh/about/
        //   /de/pt/es/blog/      -> /es/blog/
        //   /zh/                 -> /zh
        // The target is the user's most likely intent (navigate to the
        // inner-locale version) and is always a valid URL — the
        // /<lang>/<inner-lang>/... stacking only exists on requests that
        // mis-constructed the URL.
        //
        // No false positives: rest only triggers this branch when its first
        // segment is one of the 10 supported LANGS, and no non-lang directory
        // in the repo is exactly 2 letters. /<lang>/<inner-lang>/... where
        // lang === innerLang (e.g. /zh/zh/blog/...) also redirects, to
        // /zh/blog/... — which is the right normalization.
        let finalLang = null;
        let stripped = rest;
        // 10 iterations covers the worst realistic case (all 10 supported
        // langs stacked, so 9 outer prefixes to peel before the last lang
        // becomes the new outer). The 10th iteration is just a safety net
        // for anything we missed.
        for (let i = 0; i < 10; i++) {
            const m = stripped.match(/^\/(en|zh|es|fr|de|pt|ja|ru|ar|th)(\/|$)/);
            if (!m) break;
            const innerRest = stripped.slice(3); // strip "/xx" (slash + 2 letters)
            const wouldStillHaveLang = innerRest.match(/^\/(en|zh|es|fr|de|pt|ja|ru|ar|th)(\/|$)/);
            if (!wouldStillHaveLang) {
                // This lang segment is the last one — keep it as the new
                // outer lang so the redirected target still has a meaningful
                // primary lang (i18n hreflang/canonical logic downstream
                // relies on it).
                finalLang = m[1];
                stripped = innerRest;
                break;
            }
            stripped = innerRest;
        }
        if (finalLang !== null) {
            const target = `${SITE_ORIGIN}/${finalLang}${stripped}${url.search}`;
            return new Response(null, {
                status: 301,
                headers: { "Location": target },
            });
        }

        // Fetch the underlying file. The X-Middleware-Internal: 1 header
        // makes shouldSkip() short-circuit this request on re-entry, so the
        // inner fetch returns the raw HTML with __CSP_NONCE__ placeholders
        // still intact — which is what withCspHeaders below needs in order
        // to substitute the OUTER nonce consistently. Without the marker,
        // the inner middleware would inject its own nonce + CSP header,
        // leaving the outer response with two competing policies.
        const underlyingUrl = url.origin + rest + url.search;
        // Use redirect: "follow" (2026-08-10) so _redirects 301/308 rules
        // (e.g. /services/absence-compensation/celebrity-message/ → parent)
        // are transparently followed to the real target. With "manual" the
        // fetch returned 30x, !response.ok fired, and middleware fell through
        // to a hard 404 — losing SEO equity for any path whose canonical
        // target is itself a 301 (deleted services, renames, etc).
        // X-Middleware-Internal: 1 still prevents the inner target's i18n
        // re-entry via shouldSkip(), so we still get the raw static HTML.
        const response = await fetch(underlyingUrl, {
            method: "GET",
            headers: { Accept: "text/html", "X-Middleware-Internal": "1" },
            redirect: "follow",
        });

        if (!response.ok) {
            if (rest !== "/" && !rest.endsWith("/")) {
                const altUrl = url.origin + rest + "/" + url.search;
                const altResp = await fetch(altUrl, { redirect: "follow" });
                if (altResp.ok) return withCspHeaders(altResp, await altResp.text(), nonce);
            }
            return new Response(`Not found: ${path}`, { status: 404 });
        }

        const contentType = response.headers.get("content-type") || "";
        if (!contentType.includes("text/html")) return response;

        let text = await response.text();

        // 1. <html lang="xx" dir="rtl">
        if (lang !== DEFAULT_LANG) {
            const rtl = RTL[lang] ? ' dir="rtl"' : "";
            text = text.replace(/<html\s+lang="en"\s*>/i, `<html lang="${lang}"${rtl}>`);
        }

        // 2. canonical + hreflang
        const newBlock = buildCanonicalAndAlternates(rest, lang);
        text = text.replace(/<link\s+rel="canonical"\s+href="[^"]*"\s*>\n?\s*/gi, "");
        text = text.replace(/<link\s+rel="alternate"\s+hreflang="[^"]*"\s+href="[^"]*"\s*>\n?\s*/gi, "");
        if (/<title[\s>][\s\S]*?<\/title>/i.test(text)) {
            text = text.replace(/(<\/title>)/i, `$1\n    ${newBlock}`);
        } else if (/<head>/i.test(text)) {
            text = text.replace(/(<head>)/i, `$1\n    ${newBlock}`);
        }

        // 3. og:locale rewrite (per language). Apply BEFORE i18n so that
        // the locale reflects the language the user is actually viewing.
        text = setOgLocale(text, lang);

        // 4. JSON-LD inLanguage rewrite (per language).
        text = rewriteInLanguage(text, lang);

        // 5. og:url trailing-slash normalization.
        text = fixOgUrlTrailingSlash(text);

        // 6. /success/ noindex.
        text = addNoindexIfSuccess(text, rest);

        // 6.5. Diversify Article schema datePublished / dateModified across
        //      blog posts. All 50 posts currently share "2026-07-23" which
        //      looks suspicious to Google. We hash the URL to produce a
        //      stable per-post date in the past 60 days.
        if (text.includes('"@type": "Article"') || text.includes('"@type":"Article"')) {
            text = diversifyArticleDates(text, context.request.url);
            // 6.6. Rewrite Article author Organization → Person for E-E-A-T.
            text = rewriteArticleAuthor(text);
        }
        // 6.7. Refresh the visible "Updated YYYY-MM-DD" text on blog posts
        //      so the body matches the JSON-LD dateModified. This is most
        //      important for seasonal content (christmas/spring/summer).
        text = refreshVisibleUpdateDate(text, context.request.url, lang);

        // 7. Server-side i18n: load translation JSON and apply data-i18n
        //    attributes so Googlebot sees the translated HTML, not the
        //    English source. Skip for the default lang.
        if (lang !== DEFAULT_LANG) {
            try {
                const version = await getI18nVersion(context);
                const dict = await loadI18nDict(lang, version);
                if (dict) {
                    text = applyDataI18n(text, dict);
                    text = applyDataI18nAttr(text, dict);
        // #I18N-5: add local currency equivalents for non-EN/USD locales
        text = localizeCurrencyForLang(text, lang);
                }
            } catch (e) {
                // If i18n fails for any reason, fall through and serve the
                // English source. Client-side JS will still translate.
            }
        }

        return withCspHeaders(response, text, nonce);
    } catch (err) {
        return new Response(
            `Middleware error: ${err.message}\nStack: ${err.stack}`,
            { status: 500 }
        );
    }
};
