#!/usr/bin/env node
/**
 * Guards the last two runtime-copy gaps from the 2026-11 audit.
 *
 *  1. js/tools/common.js built the "Original: ... / Output: ..." file-row
 *     label, the drop-zone aria-label and the decode errors as literal
 *     English. Everything else in that file already resolves through t()
 *     against window.__WA_I18N__, which the middleware injects for tool pages
 *     from the "tools.copy" shard.
 *
 *  2. search/index.html had 15 hard-coded English result titles and
 *     descriptions. They now live in a hidden, server-translated
 *     [data-copy-set] and are read back at runtime into LOCAL_INDEX.
 *
 * Both fail silently: a missing key just falls back to the English source, so
 * a static "does the file contain translated text" check is not enough. This
 * test checks the dictionaries, the shards, the wiring AND a real middleware
 * render.
 *
 * Run:  node tests/runtime-copy-check.cjs
 */
const fs = require("fs");
const path = require("path");
const os = require("os");
const { pathToFileURL } = require("url");

const REPO = path.resolve(__dirname, "..");
const ORIGIN = "https://weddingai.video";
const LANGS = ["en", "de", "es", "fr", "pt", "ja", "zh", "ar", "th", "hi", "ru"];
const KEYS = JSON.parse(fs.readFileSync(path.join(__dirname, "runtime-copy-keys.json"), "utf8"));

let failures = 0;
function check(label, ok, detail) {
    console.log(`  ${ok ? "PASS" : "FAIL"}  ${label}${detail ? " - " + detail : ""}`);
    if (!ok) failures++;
}

function dict(lang) {
    return JSON.parse(fs.readFileSync(path.join(REPO, "i18n", lang + ".json"), "utf8"));
}
function shard(lang, ns) {
    const p = path.join(REPO, "i18n", "shards", lang, ns + ".json");
    return fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, "utf8")) : {};
}

// ---------------------------------------------------------------------------
console.log("=== dictionaries and shards carry every runtime key ===");
const dicts = {};
for (const l of LANGS) dicts[l] = dict(l);
const allKeys = Object.values(KEYS.tools).concat(
    KEYS.search.flatMap(x => [x.tk, x.dk]));

for (const l of LANGS) {
    const missingDict = allKeys.filter(k => !dicts[l][k]);
    const sh = Object.assign({}, shard(l, "tools.copy"), shard(l, "search.index"));
    const missingShard = allKeys.filter(k => !sh[k]);
    check(`${l}: ${allKeys.length} keys in dict + shards`,
        missingDict.length === 0 && missingShard.length === 0,
        missingDict.length ? `dict missing ${missingDict.length}: ${missingDict[0]}`
            : missingShard.length ? `shard missing ${missingShard.length}: ${missingShard[0]}`
                : "all present");
}

console.log("\n=== non-English values really are translations ===");
for (const l of LANGS.filter(x => x !== "en")) {
    // "Original: {orig}" is genuinely the same word in de/es/pt, so that one
    // key is excluded. Every other value must differ from English: a missing
    // or failed translation silently falls back to the English source.
    const same = allKeys.filter(k => k !== KEYS.tools.original && dicts[l][k] === dicts.en[k]);
    check(`${l}: every runtime key is translated`, same.length === 0,
        same.length ? `${same.length} unchanged (${same.slice(0, 2).join(", ")})` : "0 unchanged");
}

// ---------------------------------------------------------------------------
// Three tool cards + a section were added to tools/index.html with keys that
// existed in NO dictionary. applyDataI18n() leaves an unbound element's
// English source text alone, so all 10 non-English locales showed English.
// ---------------------------------------------------------------------------
console.log("\n=== tool-card keys exist in every language (not just ru) ===");
const CARD_KEYS = [
    "tools.card.badge.docs.18", "tools.card.badge.gen.16", "tools.card.badge.gen.17",
    "tools.card.name.docs.18", "tools.card.name.gen.16", "tools.card.name.gen.17",
    "tools.card.tag.docs.18", "tools.card.tag.gen.16", "tools.card.tag.gen.17",
    "tools.section.desc.docs", "tools.section.title.docs",
    "tools.card.cta.try_free.16", "tools.card.cta.try_free.17", "tools.card.cta.try_free.18",
];
for (const l of LANGS) {
    const absent = CARD_KEYS.filter(k => !dicts[l][k]);
    check(`${l}: 14 card keys present`, absent.length === 0,
        absent.length ? `missing ${absent[0]}` : "all present");
}
for (const l of LANGS.filter(x => x !== "en")) {
    const enLeft = CARD_KEYS.filter(k => dicts[l][k] === dicts.en[k]);
    check(`${l}: card copy translated`, enLeft.length === 0,
        enLeft.length ? `${enLeft.length} still English` : "0 English leftovers");
}

// ---------------------------------------------------------------------------
console.log("\n=== common.js wiring ===");
const common = fs.readFileSync(path.join(REPO, "js", "tools", "common.js"), "utf8");
for (const [alias, key] of Object.entries(KEYS.tools)) {
    check(`COPY.${alias} -> ${key.split(".").slice(2, 3).join("")}`,
        common.includes(`${alias}: '${key}'`), `key ${key}`);
}
for (const call of ["t('sizes'", "t('original'", "t('dropFiles'",
    "t('decodeFailed'", "t('heicUnsupported'", "t('download'", "t('remove'"]) {
    check(`common.js calls ${call}`, common.includes(call), "");
}
check("no literal 'Original: ' concatenation left",
    !/sub\.textContent\s*=\s*'Original: '/.test(common), "");

// ---------------------------------------------------------------------------
console.log("\n=== search page wiring ===");
const search = fs.readFileSync(path.join(REPO, "search", "index.html"), "utf8");
const spans = [...search.matchAll(/<span data-copy="(i\d+[td])" data-i18n="([^"]+)"/g)];
check("30 hidden translated spans", spans.length === 30, `${spans.length} found`);
const bound = new Set(spans.map(m => m[2]));
check("every span key is in the dictionary",
    allKeys.length > 0 && [...bound].every(k => dicts.en[k] !== undefined),
    `${bound.size} distinct keys`);
check("every span has an INDEX alias",
    spans.every(m => search.includes(`"${m[1]}"`) || search.includes(`${m[1]}"`)), "");
check("scoring uses LOCAL_INDEX", search.includes("const scored = LOCAL_INDEX.map"), "");
check("no whole-dictionary client download", !/\/i18n\/\$\{lang\}\.json|\/i18n\/' \+ lang \+ '\.json/.test(search), "");

// ---------------------------------------------------------------------------
// Real middleware render (mocked origin, same harness as middleware-i18n-check)
// ---------------------------------------------------------------------------
function stageMiddleware() {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "wa-rc-"));
    fs.cpSync(path.join(REPO, "functions"), path.join(dir, "functions"), { recursive: true });
    fs.writeFileSync(path.join(dir, "package.json"), JSON.stringify({ type: "module" }));
    return path.join(dir, "functions", "_middleware.js");
}
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
globalThis.caches = {
    default: {
        async match() { return undefined; },
        async put() { },
    },
};
function sourceFileFor(urlPath) {
    const clean = urlPath.replace(/\/+$/, "") || "/";
    const parts = clean.split("/").filter(Boolean);
    const langs = LANGS.filter(x => x !== "en");
    let rest = parts;
    if (parts.length && langs.includes(parts[0])) rest = parts.slice(1);
    const rel = (rest.length ? "/" + rest.join("/") : "/") + "/";
    const localized = path.join(REPO, parts.join("/"), "index.html");
    if (fs.existsSync(localized)) return localized;
    return path.join(REPO, rel.replace(/^\//, ""), "index.html");
}
async function render(lang, page) {
    const src = sourceFileFor(`/${lang}/${page}/`);
    const request = new Request(`${ORIGIN}/${lang}/${page}/`, {
        method: "GET", headers: { "user-agent": "Mavis-Test/1.0" },
    });
    const context = {
        request, env: {},
        next: async () => new Response(fs.readFileSync(src), {
            status: 200, headers: { "content-type": "text/html; charset=utf-8" },
        }),
    };
    const mod = await import(pathToFileURL(MIDDLEWARE).href);
    const res = await mod.onRequest(context);
    return await res.text();
}

let MIDDLEWARE = null;
async function main() {
    MIDDLEWARE = stageMiddleware();

    console.log("\n=== real middleware render: /<lang>/search/ ===");
    for (const lang of ["de", "ja", "ru"]) {
        fetchLog.length = 0;
        const html = await render(lang, "search");
        const served = [...html.matchAll(/<span data-copy="(i\d+[td])"[^>]*>([\s\S]*?)<\/span>/g)];
        const mapped = new Map(served.map(m => [m[1], m[2].trim()]));
        const english = KEYS.search.filter((x, i) =>
            mapped.get(`i${i}t`) === dicts.en[x.tk] || mapped.get(`i${i}d`) === dicts.en[x.dk]);
        const shardsHit = fetchLog.filter(f => f.path.includes("/i18n/shards/")).length;
        const dictHit = fetchLog.filter(f => /\/i18n\/[a-z]+\.json/.test(f.path)).length;
        check(`/${lang}/search/: 30 spans served, translated, no full dict`,
            served.length === 30 && english.length <= 2 && shardsHit > 0 && dictHit === 0,
            `spans=${served.length} english=${english.length} shards=${shardsHit} fullDict=${dictHit}`);
    }

    console.log("\n=== real middleware render: /<lang>/tools/ runtime dictionary ===");
    for (const lang of ["de", "ar"]) {
        fetchLog.length = 0;
        const html = await render(lang, "tools/wedding-photo-collage");
        const m = html.match(/window\.__WA_I18N__=(\{[\s\S]*?\});<\/script>/);
        let runtime = {};
        try { runtime = JSON.parse(m ? m[1] : "{}"); } catch (e) { /* reported below */ }
        const missing = Object.values(KEYS.tools).filter(k => !runtime[k]);
        const enLeft = Object.entries(KEYS.tools).filter(([, k]) => runtime[k] === dicts.en[k]);
        check(`/${lang}/tools/: 5 new keys injected and translated`,
            missing.length === 0 && enLeft.length <= 1,
            `runtime keys=${Object.keys(runtime).length} missing=${missing.length} english=${enLeft.length}`);
    }

    // A localized URL with no localized twin is served from the ENGLISH
    // source file with the body translated at runtime. ru had ~35k missing
    // keys, so these pages showed English bodies. Cyrillic density is a
    // reliable structural check here (nav/footer alone stay well below 800).
    console.log("\n=== /ru/blog/* article body is Russian ===");
    {
        fetchLog.length = 0;
        const html = await render("ru", "blog/affordable-wedding-video-ai");
        const cyr = (html.match(/[\u0400-\u04FF]/g) || []).length;
        const shardFetches = fetchLog.filter(f => f.path.includes("/i18n/shards/")).length;
        const dictFetch = fetchLog.filter(f => /\/i18n\/[a-z]+\.json/.test(f.path)).length;
        check("Russian article body is translated, shards only",
            cyr > 800 && shardFetches > 0 && dictFetch === 0,
            `${cyr} Cyrillic chars, shards=${shardFetches}, fullDict=${dictFetch}`);
    }

    console.log("");
    if (failures) {
        console.log(`RESULT: ${failures} FAILURE(S)`);
        process.exit(1);
    }
    console.log("ALL CHECKS PASSED");
}

main().catch(err => {
    console.error(err);
    process.exit(1);
});
