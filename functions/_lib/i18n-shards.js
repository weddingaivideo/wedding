// =============================================
//   WeddingAI.video — sharded i18n loading
//
//   WHY THIS EXISTS
//   ---------------
//   The per-language dictionaries are 6-17 MB of JSON (i18n/hi.json alone is
//   17 MB / 64k keys). Parsing one of them costs 50-80 ms of CPU, and the
//   Cloudflare Pages Free plan allows 50 ms of CPU per request. A localized
//   page request therefore blew the limit and Cloudflare answered with
//   error 1102 ("Worker exceeded resource limits").
//
//   Measured on the live site on 2026-10-30 (1539 sitemap URLs, pinned to
//   the real edge IP, correct SNI):
//
//       en  2.2% 503     ru  7.9%     ar 26.4%     de 53.6%     es 77.9%
//       hi 82.9%         ja 86.4%     pt 85.7%     th 93.6%     zh 97.1%
//       -------------------------------------------------------------
//       ALL 63.3% (974 of 1539 URLs)
//
//   English is fine because DEFAULT_LANG never loads a dictionary. The rest
//   degrade in proportion to the size of their dictionary.
//
//   The 5-minute body cache (getCachedProcessedBody) cannot rescue those
//   pages: the very first build exceeds the limit, so the builder throws
//   and the cache never gets an entry to serve. The failure is permanent
//   for that URL.
//
//   THE FIX
//   -------
//   The dictionaries are already split into per-namespace shards by
//   qa/build-i18n-shards.py (407 shards per language, biggest ~370 KB).
//   A page only needs the namespaces its OWN data-i18n keys live in -
//   about 10 of the 407 - which is ~270 KB instead of 10 MB, i.e. ~2 ms of
//   parse instead of ~80 ms.
//
//   If anything is missing (no manifest, a shard 404s, a page needs too
//   many shards) this module returns null and the caller falls back to the
//   full dictionary, so the behaviour degrades to the old path instead of
//   breaking the page.
//
//   The shards have to be deployed for this to take effect. They live in
//   i18n/shards/<lang>/ and are rebuilt by qa/build-i18n-shards.py; the
//   pre-deploy check fails when they are out of sync with the dictionaries.
//   =============================================

export const SHARD_DIR = "/i18n/shards";
export const MANIFEST_PATH = "/i18n";

// A manifest is a tiny file (24 KB) and never changes between deploys, so it
// is worth keeping in module scope for the lifetime of the isolate.
const MANIFEST_TTL_MS = 5 * 60 * 1000;

// Cloudflare Pages Free allows 50 subrequests per request. A page normally
// needs ~10 shards; the blog hub needs 111 and is excluded below.
const MAX_SHARDS = 40;

// How many shard fetches run in parallel.
const FETCH_CONCURRENCY = 12;

let manifestCache = null; // { lang, manifest, at }

// The namespace a key belongs to: its first two dotted segments.
//
// MUST stay in step with ns_of() in qa/build-i18n-shards.py, otherwise the
// middleware asks for shard files that do not exist and every translation
// silently falls back to English.
export function namespaceOf(key) {
    const p = key.split(".");
    if (p.length <= 1) return "_root";
    if (p.length === 2) return p[0];
    return p[0] + "." + p[1];
}

// The namespaces a page needs, read from its own data-i18n attributes.
//
// Handles both spellings:
//   data-i18n="blog.foo.p_text.bar"
//   data-i18n-attr="content:blog.foo.meta|content:blog.foo.other"
// The attribute form carries "attr:key" pairs separated by "|", and the two
// keys can live in DIFFERENT namespaces - so each part is split separately.
//
// MUST stay in step with keys_in_html() in qa/build-i18n-shards.py. An
// earlier version of the builder only understood data-i18n="key" and
// data-i18n-attr="content:key", so a `title:key` binding was filed under
// the "_root" namespace, no shard was ever built for it, and the binding
// silently stayed English. scripts/verify-i18n-shards.py cross-checks the
// two implementations against each other so they cannot drift apart again.
export function namespacesInHtml(html) {
    const ns = new Set();
    const re = /data-i18n(?:-attr)?="([^"]+)"/g;
    let m;
    while ((m = re.exec(html)) !== null) {
        const spec = m[1];
        const parts = spec.indexOf("|") !== -1 ? spec.split("|") : [spec];
        for (const part of parts) {
            const c = part.indexOf(":");
            const key = (c === -1 ? part : part.slice(c + 1)).trim();
            if (key) ns.add(namespaceOf(key));
        }
    }
    return ns;
}

// Stable id for a set of namespaces.
//
// SHA-256 over the sorted, newline-joined names, truncated to 16 hex
// characters. MUST stay in step with namespace_set_id() in
// qa/build-i18n-shards.py - the manifest is keyed by this value.
export async function namespaceSetId(nsList) {
    const joined = [...nsList].sort().join("\n");
    const bytes = new TextEncoder().encode(joined);
    const digest = await crypto.subtle.digest("SHA-256", bytes);
    return [...new Uint8Array(digest)]
        .map((b) => b.toString(16).padStart(2, "0"))
        .join("")
        .slice(0, 16);
}

async function loadManifest(origin, lang, version) {
    const now = Date.now();
    if (manifestCache && manifestCache.lang === lang &&
        now - manifestCache.at < MANIFEST_TTL_MS) {
        return manifestCache.manifest;
    }
    try {
        const resp = await fetch(`${origin}${MANIFEST_PATH}/${lang}.manifest.json?v=${version}`);
        if (!resp.ok) return null;
        const manifest = await resp.json();
        if (!manifest || typeof manifest !== "object") return null;
        manifestCache = { lang, manifest, at: now };
        return manifest;
    } catch (e) {
        return null;
    }
}

async function fetchShard(origin, lang, version, file) {
    try {
        const resp = await fetch(`${origin}${SHARD_DIR}/${lang}/${file}?v=${version}`);
        if (!resp.ok) return null;
        return await resp.json();
    } catch (e) {
        return null;
    }
}

// Returns a dictionary holding ONLY the keys this page needs, or null when
// the shards cannot serve it (caller falls back to the full dictionary).
//
// extraNamespaces (added 2026-11-09): namespaces to load in ADDITION to the
// ones the page's own data-i18n attributes name. The tool pages need
// "tools.copy" because js/tools/common.js creates buttons and raises toasts
// at RUNTIME - after the middleware has already rewritten the static HTML -
// so those strings cannot be resolved by the data-i18n mechanism. The
// middleware injects that namespace as window.__WA_I18N__ instead.
//
// The extra namespaces are added only to the per-namespace path, AFTER the
// bundle lookup, so the blog hub's bundle id is unchanged.
export async function loadI18nShards(origin, lang, version, html, extraNamespaces) {
    const manifest = await loadManifest(origin, lang, version);
    if (!manifest) return null;

    const nsList = [...namespacesInHtml(html)];

    // ---- page bundle -----------------------------------------------------
    // A page that binds more namespaces than the runtime can fetch (the
    // 50-subrequest limit of the CF Pages Free plan) gets a single bundle
    // holding exactly its own keys. blog/index.html is the case that
    // matters: it binds the title and description of ~100 articles, but
    // each article lives in a namespace that holds the ENTIRE article body,
    // so the namespace path needs 111 shards and 9-15 MB of payload - the
    // same payload that caused the 503 storm. The bundle is ~60 KB and one
    // request.
    const bundles = manifest.__bundles__;
    if (bundles && typeof bundles === "object" && nsList.length) {
        const bid = await namespaceSetId(nsList);
        const bfile = bundles[bid];
        if (bfile) {
            const payload = await fetchShard(origin, lang, version, bfile);
            if (payload && Object.keys(payload).length) return payload;
        }
    }

    // ---- per-namespace shards --------------------------------------------
    const files = [];
    const seen = new Set();
    const allNamespaces = extraNamespaces && extraNamespaces.length
        ? [...nsList, ...extraNamespaces]
        : nsList;
    for (const ns of allNamespaces) {
        const list = manifest[ns];
        if (!Array.isArray(list)) continue;
        for (const f of list) {
            if (!seen.has(f)) {
                seen.add(f);
                files.push(f);
            }
        }
    }
    if (!files.length) return null;

    // Too many shards to fetch inside the subrequest budget: let the caller
    // use the full dictionary for this page instead.
    if (files.length > MAX_SHARDS) return null;

    const dict = {};
    for (let i = 0; i < files.length; i += FETCH_CONCURRENCY) {
        const chunk = files.slice(i, i + FETCH_CONCURRENCY);
        const parts = await Promise.all(
            chunk.map((f) => fetchShard(origin, lang, version, f))
        );
        for (const p of parts) {
            if (p) Object.assign(dict, p);
        }
    }
    return dict;
}
