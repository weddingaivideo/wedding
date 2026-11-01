// Local integration test for functions/_middleware.js.
//
// Runs the real middleware against the real repo files with a mocked
// origin (no network), and asserts the things the 2026-10-30 audit found:
//
//   1. The served <title> contains NO markup (the local-currency <span> used
//      to be injected into it, so the SERP entry showed raw HTML).
//   2. The hero trust line is TRANSLATED (its key was renamed in index.html
//      only, so every localized homepage rendered it in English).
//   3. The footer badge title attribute is TRANSLATED (it was never bound to
//      the dictionary, so "500+ couples served" stayed English).
//   4. The shard path is actually used (not the 10 MB full dictionary).
//   5. The blog hub is served from a BUNDLE, not from ~111 namespace shards
//      (the hub binds the title and description of ~100 articles, but each
//      article namespace holds the whole article body - the namespace path
//      needed 9-15 MB and blew the CPU limit, i.e. Cloudflare error 1102).
//
// Run:  node tests/middleware-i18n-check.cjs
const fs = require("fs");
const path = require("path");
const os = require("os");
const { pathToFileURL } = require("url");

const REPO = path.resolve(__dirname, "..");
const ORIGIN = "https://weddingai.video";

// The middleware is an ES module ("import ... from"), but the repo has no
// package.json, so node treats .js as CommonJS. Copy functions/ into a
// temp dir with a {"type":"module"} package.json and import from there -
// that keeps the deploy tree untouched.
function stageMiddleware() {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "wa-mw-"));
    fs.cpSync(path.join(REPO, "functions"), path.join(dir, "functions"), { recursive: true });
    fs.writeFileSync(path.join(dir, "package.json"), JSON.stringify({ type: "module" }));
    return path.join(dir, "functions", "_middleware.js");
}

// ---------------------------------------------------------------- file server
function localFile(urlPath) {
    const clean = urlPath.split("?")[0];
    if (clean.endsWith("/")) return path.join(REPO, clean.replace(/^\//, ""), "index.html");
    return path.join(REPO, clean.replace(/^\//, ""));
}

const fetchLog = [];
globalThis.fetch = async (input) => {
    const url = typeof input === "string" ? input : input.url;
    const u = new URL(url);
    const file = localFile(u.pathname);
    fetchLog.push({ path: u.pathname + (u.search || ""), bytes: 0 });
    if (!fs.existsSync(file)) {
        fetchLog[fetchLog.length - 1].bytes = -1;
        return new Response("not found", { status: 404 });
    }
    const body = fs.readFileSync(file);
    fetchLog[fetchLog.length - 1].bytes = body.length;
    return new Response(body, {
        status: 200,
        headers: { "content-type": file.endsWith(".json") ? "application/json" : "text/html; charset=utf-8" },
    });
};

// ------------------------------------------------------------------ CF mocks
const cacheStore = new Map();
globalThis.caches = {
    default: {
        async match(req) {
            const key = typeof req === "string" ? req : req.url;
            return cacheStore.get(key);
        },
        async put(req, resp) {
            const key = typeof req === "string" ? req : req.url;
            cacheStore.set(key, resp.clone());
        },
    },
};

// Which html file the middleware is asked to render for a given url.
function sourceFileFor(urlPath) {
    // A localized url without a localized twin is served from the ENGLISH
    // source file - that is exactly the fallback the middleware does.
    const clean = urlPath.replace(/\/+$/, "") || "/";
    const parts = clean.split("/").filter(Boolean);
    const langs = ["zh", "ja", "ar", "es", "fr", "de", "pt", "ru", "th", "hi"];
    let rest = parts;
    if (parts.length && langs.includes(parts[0])) rest = parts.slice(1);
    const rel = (rest.length ? "/" + rest.join("/") : "/") + "/";
    const localized = path.join(REPO, parts.length && langs.includes(parts[0])
        ? parts.join("/") : "", "index.html");
    if (fs.existsSync(localized)) return localized;
    return path.join(REPO, rel.replace(/^\//, ""), "index.html");
}

async function run() {
    const mod = await import(pathToFileURL(stageMiddleware()).href);
    const onRequest = mod.onRequest;
    if (typeof onRequest !== "function") throw new Error("onRequest is not exported");

    let failures = 0;

    function report(lang, path, checks) {
        console.log(`\n=== ${lang}${path} ===`);
        for (const [name, ok, detail] of checks) {
            if (!ok) failures++;
            console.log(`  ${ok ? "PASS" : "FAIL"}  ${name}`);
            console.log(`        ${detail}`);
        }
    }

    // ---------------------------------------------------- homepages (shards)
    for (const lang of ["zh", "pt", "es", "de"]) {
        fetchLog.length = 0;
        const url = `${ORIGIN}/${lang}/`;
        const request = new Request(url, { method: "GET", headers: { "user-agent": "Mavis-Test/1.0" } });
        const context = {
            request,
            env: {},
            next: async () => new Response(fs.readFileSync(path.join(REPO, "index.html")), {
                status: 200,
                headers: { "content-type": "text/html; charset=utf-8" },
            }),
        };

        const res = await onRequest(context);
        const html = await res.text();

        const title = (html.match(/<title[^>]*>([\s\S]*?)<\/title>/) || [])[1] || "";
        const hero = (html.match(/<p class="hero-trust"[^>]*>([\s\S]*?)<\/p>/) || [])[1] || "";
        const badge = (html.match(/<a[^>]*class="footer-badge[^"]*"[^>]*title="([^"]*)"/) || [])[1] || "";
        const shardFetches = fetchLog.filter((f) => f.path.includes("/i18n/shards/")).length;
        const dictFetch = fetchLog.filter((f) => /\/i18n\/[a-z]+\.json/.test(f.path)).length;

        // The English source of this line. A localized page must NOT still
        // show it - checking against the source works for every script,
        // unlike a "does it contain non-Latin characters" heuristic.
        const EN_TRUST_LINE = "Trusted by 500+ couples · Top-rated 4.9/5 · 48h turnaround";
        const EN_BADGE_TITLE = "500+ couples served, 4.9/5 rating";

        report(`/${lang}/`, "", [
            ["title has no markup", !/<[a-z]/i.test(title), title.slice(0, 70)],
            ["hero trust line is translated", hero.trim() !== "" && hero.trim() !== EN_TRUST_LINE, hero.slice(0, 70)],
            ["footer badge title is translated", badge.trim() !== "" && badge.trim() !== EN_BADGE_TITLE, badge.slice(0, 70)],
            ["shard path used, full dict not fetched", shardFetches > 0 && dictFetch === 0, `shards=${shardFetches} fullDict=${dictFetch}`],
        ]);
    }

    // ------------------------------------------- blog hub (page bundle path)
    for (const lang of ["zh", "hi"]) {
        fetchLog.length = 0;
        const url = `${ORIGIN}/${lang}/blog/`;
        const src = sourceFileFor(`/${lang}/blog/`);
        const request = new Request(url, { method: "GET", headers: { "user-agent": "Mavis-Test/1.0" } });
        const context = {
            request,
            env: {},
            next: async () => new Response(fs.readFileSync(src), {
                status: 200,
                headers: { "content-type": "text/html; charset=utf-8" },
            }),
        };

        const res = await onRequest(context);
        const html = await res.text();

        const bundleFetches = fetchLog.filter((f) => f.path.includes("/i18n/shards/") && f.path.includes("bundle.")).length;
        const shardFetches = fetchLog.filter((f) => f.path.includes("/i18n/shards/")).length;
        const dictFetch = fetchLog.filter((f) => /\/i18n\/[a-z]+\.json/.test(f.path)).length;
        const bytes = fetchLog
            .filter((f) => f.path.includes("/i18n/shards/"))
            .reduce((a, f) => a + (f.bytes > 0 ? f.bytes : 0), 0);

        // The first card title of the hub: <h3><a href="/blog/...">Title</a></h3>
        // Matched by STRUCTURE, not by data-i18n: applyDataI18n() strips the
        // data-i18n attribute when it rewrites the text, so the served html
        // no longer carries it.
        const CARD_RE = /<h3[^>]*>\s*<a href="\/blog\/[^"]*"[^>]*>([\s\S]*?)<\/a>/;
        const DESC_RE = /<h3[^>]*>\s*<a href="\/blog\/[^"]*"[^>]*>[\s\S]*?<\/a>\s*<\/h3>\s*<p[^>]*>([\s\S]*?)<\/p>/;
        const srcHtml = fs.readFileSync(src, "utf8");
        const enTitle = (srcHtml.match(CARD_RE) || [])[1] || "";
        const cardTitle = (html.match(CARD_RE) || [])[1] || "";
        const enDesc = (srcHtml.match(DESC_RE) || [])[1] || "";
        const desc = (html.match(DESC_RE) || [])[1] || "";

        report(`/${lang}/blog/`, "", [
            ["bundle fetched", bundleFetches === 1, `bundles=${bundleFetches} shards=${shardFetches} fullDict=${dictFetch}`],
            ["full dictionary NOT fetched", dictFetch === 0, `fullDict=${dictFetch}`],
            ["shard payload is small (< 500 KB)", bytes > 0 && bytes < 500 * 1024, `${(bytes / 1024).toFixed(0)} KB`],
            ["a card title is translated", cardTitle.trim() !== "" && cardTitle.trim() !== enTitle.trim(), `EN: ${enTitle.trim().slice(0, 46)} | ${cardTitle.trim().slice(0, 46)}`],
            ["a card description is translated", desc.trim() !== "" && desc.trim() !== enDesc.trim(), `EN: ${enDesc.trim().slice(0, 40)} | ${desc.trim().slice(0, 40)}`],
        ]);
    }

    // ------------------------------------------------- hreflang of the output
    // The middleware injects a complete 11-language + x-default block and
    // strips the author's own block first. The strip used to match only ONE
    // attribute order, so a page written as
    //     <link href="..." hreflang="xx" rel="alternate"/>
    // kept its own block and was served with every hreflang DUPLICATED
    // ("Hreflang: Multiple Entries"). hi/blog/* is written in that form.
    {
        const LINK_RE = /<link\b([^>]*)>/gi;
        const ATTR_RE = /([a-zA-Z-]+)\s*=\s*"([^"]*)"/g;
        const alternatesOf = (html) => {
            const out = [];
            let m;
            LINK_RE.lastIndex = 0;
            while ((m = LINK_RE.exec(html)) !== null) {
                const attrs = {};
                let a;
                ATTR_RE.lastIndex = 0;
                while ((a = ATTR_RE.exec(m[1])) !== null) attrs[a[1].toLowerCase()] = a[2];
                if ((attrs.rel || "").toLowerCase() !== "alternate") continue;
                out.push([attrs.hreflang, attrs.href]);
            }
            return out;
        };

        for (const url of ["/hi/blog/affordable-wedding-video-ai/", "/ar/blog/affordable-wedding-video-ai/", "/es/tools/save-the-date-maker/", "/about/"]) {
            fetchLog.length = 0;
            const src = sourceFileFor(url);
            const request = new Request(ORIGIN + url, { method: "GET", headers: { "user-agent": "Mavis-Test/1.0" } });
            const context = {
                request,
                env: {},
                next: async () => new Response(fs.readFileSync(src), {
                    status: 200,
                    headers: { "content-type": "text/html; charset=utf-8" },
                }),
            };
            const res = await onRequest(context);
            const html = await res.text();
            const pairs = alternatesOf(html);
            const counts = {};
            for (const [hl] of pairs) counts[hl] = (counts[hl] || 0) + 1;
            const dups = Object.keys(counts).filter((k) => counts[k] > 1);
            const want = ["ar", "de", "en", "es", "fr", "hi", "ja", "pt", "ru", "th", "zh", "x-default"];
            const missing = want.filter((l) => !counts[l]);
            // every alternate must point at its own language
            const wrong = [];
            for (const [hl, href] of pairs) {
                if (hl === "en" || hl === "x-default") continue;
                if (!href.startsWith(`https://weddingai.video/${hl}/`)) wrong.push(`${hl}->${href}`);
            }
            report(url, "", [
                ["exactly 12 alternates", pairs.length === 12, `got ${pairs.length}`],
                ["no duplicated hreflang", dups.length === 0, dups.join(", ") || "none"],
                ["every language present", missing.length === 0, missing.join(", ") || "11 + x-default"],
                ["every href matches its hreflang", wrong.length === 0, wrong.slice(0, 3).join(" | ") || "ok"],
            ]);
        }
    }

    console.log(`\n${failures === 0 ? "ALL CHECKS PASSED" : failures + " CHECK(S) FAILED"}`);
    process.exit(failures === 0 ? 0 : 1);
}

run().catch((e) => {
    console.error("TEST ERROR:", e && e.stack ? e.stack : e);
    process.exit(2);
});
