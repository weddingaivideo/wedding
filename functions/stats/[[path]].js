/**
 * Cloudflare Pages Function — /stats/*
 * Reverse proxy for the self-hosted Umami analytics instance.
 *
 * WHY A PROXY INSTEAD OF LOADING THE UMAMI ORIGIN DIRECTLY
 * -------------------------------------------------------
 * 1. Ad blockers. Umami self-hosted lives on a *.vercel.app host, and
 *    vercel.app is on several blocker lists. A first-party path
 *    (/stats/script.js on weddingai.video) is not, so the traffic
 *    actually arrives.
 * 2. CSP. Because the tracker is served same-origin, the site's
 *    script-src / connect-src need no change ('self' already covers
 *    it). The Umami tracker derives its beacon endpoint from the
 *    script's own URL (src/tracker/index.ts:
 *    `host = currentScript.src.split('/').slice(0, -1)`), so a script
 *    at /stats/script.js automatically posts to /stats/api/send —
 *    which this proxy also forwards.
 *
 * ROUTING
 * -------
 *   GET  /stats/script.js   ->  <UMAMI_ORIGIN>/script.js
 *   POST /stats/api/send     ->  <UMAMI_ORIGIN>/api/send
 *
 * The tracker only needs those two, but the proxy is generic so a
 * future dashboard embed or a /stats/recorder.js can be added without
 * touching this file.
 *
 * GEOGRAPHY
 * ---------
 * Umami resolves country/region/city from the edge provider's headers
 * (see src/lib/detect.ts PROVIDER_HEADERS) and falls back to a MaxMind
 * database. When we proxy, the request that reaches Umami originates
 * from Cloudflare's network, NOT the visitor's — so the visitor's geo
 * headers must be copied across, or every visitor would be geo-located
 * to Cloudflare's PoP.
 *
 * The header names below are the ones Umami actually reads. For
 * Cloudflare that is cf-ipcountry / cf-region-code / cf-ipcity —
 * NOT cf-region / cf-city. (Verified against src/lib/detect.ts
 * PROVIDER_HEADERS, 2026-11-12. The first version of this proxy
 * forwarded the wrong names, so country was read but region and city
 * always came back empty.)
 *
 * We also pass through CF-Connecting-IP so Umami sees the real client
 * IP for session uniqueness and IP blocking.
 *
 * SETUP
 * -----
 * UMAMI_ORIGIN defaults to the deployed Umami instance. Override it with a
 * Cloudflare Pages environment variable only if the Umami deployment moves
 * to a different host — then set:
 *   UMAMI_ORIGIN = https://<new-host>
 * Do NOT include a trailing slash.
 */

const DEFAULT_ORIGIN = "https://umami-weddingai.vercel.app";

// Headers we copy from the visitor's request onto the proxied request.
// Only headers that affect the DATA Umami stores are forwarded —
// forwarding every header would leak the visitor's cookies and
// auth state to a third-party origin.
const FORWARD_REQUEST_HEADERS = [
    // Identity of the visitor (Umami derives the session from IP+UA).
    "cf-connecting-ip",
    "x-forwarded-for",
    "user-agent",
    "accept-language",
    // Geography. These are the EXACT header names umami reads
    // (src/lib/detect.ts -> PROVIDER_HEADERS). Cloudflare's are
    // cf-ipcountry / cf-region-code / cf-ipcity.
    //
    // We forward BOTH naming variants for region and city. Cloudflare
    // exposes the location of the visitor as cf-region / cf-city in
    // some edge configurations and cf-region-code / cf-ipcity in
    // others, and umami only reads one spelling. Forwarding both costs
    // nothing and guarantees the lookup hits whichever pair the edge
    // actually sent.
    "cf-ipcountry",
    "cf-region",
    "cf-region-code",
    "cf-city",
    "cf-ipcity",
    "cf-vercel-ip-country",
    "cf-vercel-ip-country-region",
    "cf-vercel-ip-city",
    // Umami's own collection protocol headers.
    "x-umami-website-id",
    "x-umami-hostname",
    "x-umami-cache",
];

// Response headers worth keeping. Everything else (cookies, CSP of the
// Umami app, cache-control of the Vercel host) is dropped — we want
// the browser to treat this as our own first-party asset.
const FORWARD_RESPONSE_HEADERS = ["content-type", "content-length", "cache-control", "etag"];

function resolveOrigin(env) {
    const raw = (env.UMAMI_ORIGIN || DEFAULT_ORIGIN).replace(/^\ufeff+/, "").trim();
    if (!raw) return null;
    // Normalize: strip trailing slash, force https://
    let origin = raw.replace(/\/+$/, "");
    if (!/^https?:\/\//i.test(origin)) {
        origin = `https://${origin}`;
    }
    return origin;
}

export async function onRequest(context) {
    const { request, env } = context;

    const origin = resolveOrigin(env);
    if (!origin) {
        return new Response("Analytics proxy is not configured (UMAMI_ORIGIN missing).", {
            status: 503,
            headers: { "Content-Type": "text/plain; charset=utf-8" },
        });
    }

    const requestUrl = new URL(request.url);

    // Strip the /stats prefix: /stats/script.js -> /script.js,
    // /stats/api/send -> /api/send.
    const path = requestUrl.pathname.replace(/^\/stats/, "") || "/";
    const target = new URL(path + requestUrl.search, origin);

    // Only GET and POST are forwarded. GET serves the tracker script;
    // POST carries the collection beacon. Anything else is a probe.
    if (request.method !== "GET" && request.method !== "POST") {
        return new Response("Method Not Allowed", {
            status: 405,
            headers: { Allow: "GET, POST" },
        });
    }

    const headers = new Headers();
    for (const name of FORWARD_REQUEST_HEADERS) {
        const value = request.headers.get(name);
        if (value) headers.set(name, value);
    }
    headers.set("accept", request.method === "GET" ? "text/javascript,*/*" : "application/json");

    let body;
    if (request.method === "POST") {
        body = await request.arrayBuffer();
        headers.set("content-type", request.headers.get("content-type") || "application/json");
    }

    let upstream;
    try {
        upstream = await fetch(target.toString(), {
            method: request.method,
            headers,
            body,
            redirect: "follow",
        });
    } catch (e) {
        console.error(`[UMAMI PROXY FAIL] ${request.method} ${target.toString()} err=${e && e.message ? e.message : e}`);
        return new Response("Upstream analytics unavailable.", {
            status: 502,
            headers: { "Content-Type": "text/plain; charset=utf-8" },
        });
    }

    const outHeaders = new Headers();
    for (const name of FORWARD_RESPONSE_HEADERS) {
        const value = upstream.headers.get(name);
        if (value) outHeaders.set(name, value);
    }
    // The tracker script must never be cached stale across deploys of
    // the Umami app, and the collection beacon must never be cached.
    if (request.method === "POST") {
        outHeaders.set("cache-control", "no-store");
    } else if (!outHeaders.get("cache-control")) {
        outHeaders.set("cache-control", "public, max-age=300");
    }

    return new Response(upstream.body, {
        status: upstream.status,
        headers: outHeaders,
    });
}
