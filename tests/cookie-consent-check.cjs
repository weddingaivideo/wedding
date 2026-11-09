// Local test for js/cookie-consent.js.
//
// The banner is built at runtime, so the middleware's server-side data-i18n
// pass cannot reach it - it only rewrites attributes inside the HTML. The
// strings therefore live in /i18n/cookie/<lang>.json and are fetched once.
// Until 2026-10-31 the banner was hard-coded English on every language.
//
// This runs the real file against a minimal DOM stub and asserts:
//   1. a localized page renders the LOCALIZED banner,
//   2. the privacy link points at the LOCALIZED privacy page,
//   3. an English page renders the English banner and never fetches,
//   4. a stored choice suppresses the banner on the next visit,
//   5. a failed fetch falls back to English instead of rendering nothing.
//
// Run:  node tests/cookie-consent-check.cjs
const fs = require("fs");
const path = require("path");

const REPO = path.resolve(__dirname, "..");
const SRC = fs.readFileSync(path.join(REPO, "js", "cookie-consent.js"), "utf8");

// ------------------------------------------------------------- minimal DOM
let REGISTRY = null;   // id -> element, shared by the current document

function makeElement(tag) {
    const el = {
        tagName: String(tag || "div").toUpperCase(),
        _id: "",
        style: {},
        attrs: {},
        _html: "",
        children: [],
        listeners: {},
        setAttribute(k, v) { this.attrs[k] = v; },
        getAttribute(k) { return this.attrs[k]; },
        addEventListener(ev, fn) { (this.listeners[ev] = this.listeners[ev] || []).push(fn); },
        remove() { this.removed = true; if (this.parent) this.parent.children = this.parent.children.filter((c) => c !== this); },
        appendChild(c) { c.parent = this; this.children.push(c); return c; },
        click() { (this.listeners.click || []).forEach((fn) => fn()); },
    };
    Object.defineProperty(el, "id", {
        get() { return this._id; },
        set(v) { this._id = v; if (REGISTRY && v) REGISTRY[v] = el; },
    });
    // Setting innerHTML in a real browser creates the child elements. The
    // script then does getElementById('wa-cookie-accept') on them, so the stub
    // has to register every id it finds in the markup.
    Object.defineProperty(el, "innerHTML", {
        get() { return this._html; },
        set(v) {
            this._html = String(v);
            const re = /id="([^"]+)"/g;
            let m;
            while ((m = re.exec(this._html)) !== null) {
                const child = makeElement("button");
                child.id = m[1];
                this.children.push(child);
            }
        },
    });
    return el;
}

function installDom(lang, store) {
    const byId = {};
    REGISTRY = byId;
    const doc = {
        documentElement: { lang },
        body: makeElement("body"),
        createElement: (t) => makeElement(t),
        getElementById: (id) => byId[id] || null,
        // js/main.min.js queries these at load time. The stub returns null /
        // an empty list, which is what a page WITHOUT a mobile menu toggle
        // and WITHOUT an order form looks like.
        querySelector: () => null,
        querySelectorAll: () => [],
        addEventListener: () => {},
        _byId: byId,
    };
    globalThis.document = doc;
    globalThis.localStorage = {
        _d: store,
        getItem(k) { return Object.prototype.hasOwnProperty.call(this._d, k) ? this._d[k] : null; },
        setItem(k, v) { this._d[k] = String(v); },
    };
    return doc;
}

function installFetch(handler) {
    const log = [];
    globalThis.fetch = async (url) => {
        log.push(String(url));
        const r = handler(String(url));
        if (!r) return { ok: false, json: async () => ({}) };
        return { ok: true, json: async () => r };
    };
    return log;
}

async function run() {
    let failures = 0;
    const checks = [];
    const check = (name, ok, detail) => {
        checks.push([name, ok, detail]);
        if (!ok) failures++;
    };

    const settle = () => new Promise((r) => setTimeout(r, 30));

    // ---------------------------------------------------- 1. localized page
    {
        const store = {};
        const doc = installDom("zh", store);
        const log = installFetch((url) => {
            if (url === "/i18n/cookie/zh.json") {
                return JSON.parse(fs.readFileSync(path.join(REPO, "i18n", "cookie", "zh.json"), "utf8"));
            }
            return null;
        });
        // eslint-disable-next-line no-new-func
        new Function(SRC)();
        await settle();

        const banner = doc.getElementById("wa-cookie-banner");
        const html = banner ? banner.innerHTML : "";
        check("banner is rendered", !!banner, html.slice(0, 60));
        check("banner is localized (Chinese)", /我们使用 Cookie/.test(html), html.slice(0, 80));
        check("privacy link is localized", html.includes('href="/zh/privacy/"'), "href=" + (html.match(/href="[^"]+"/) || ["?"])[0]);
        check("the placeholder was substituted", !html.includes("{link}") && html.includes("<a href="), html.slice(0, 120));
        check("the localized dictionary was fetched once", log.length === 1 && log[0] === "/i18n/cookie/zh.json", log.join(", "));

        // clicking "accept" stores the choice and removes the banner
        const accept = doc.getElementById("wa-cookie-accept");
        check("accept button exists", !!accept, accept ? "yes" : "no");
        if (accept) {
            accept.click();
            check("the choice is persisted", store.wa_cookie_consent === "all", JSON.stringify(store));
            check("the banner is removed", doc.getElementById("wa-cookie-banner").removed === true, "removed=" + doc.getElementById("wa-cookie-banner").removed);
        }
    }

    // ------------------------------------------------- 2. English page
    {
        const store = {};
        const doc = installDom("en", store);
        const log = installFetch(() => null);
        new Function(SRC)();
        await settle();

        const banner = doc.getElementById("wa-cookie-banner");
        const html = banner ? banner.innerHTML : "";
        check("English banner is rendered", /We use cookies/.test(html), html.slice(0, 70));
        check("the English page does NOT fetch a dictionary", log.length === 0, log.join(", ") || "(no fetch)");
        check("the privacy link is /privacy/", html.includes('href="/privacy/"'), "href=" + (html.match(/href="[^"]+"/) || ["?"])[0]);
    }

    // ------------------------------------- 3. a stored choice suppresses it
    {
        const store = { wa_cookie_consent: "essential" };
        const doc = installDom("zh", store);
        const log = installFetch(() => null);
        new Function(SRC)();
        await settle();
        check("no banner on a returning visitor", doc.getElementById("wa-cookie-banner") === null, "banner=" + !!doc.getElementById("wa-cookie-banner"));
        check("no fetch on a returning visitor", log.length === 0, log.join(", ") || "(no fetch)");
    }

    // ------------------------------------------- 4. a failed fetch falls back
    {
        const store = {};
        const doc = installDom("th", store);
        installFetch(() => null);
        new Function(SRC)();
        await settle();
        const banner = doc.getElementById("wa-cookie-banner");
        const html = banner ? banner.innerHTML : "";
        check("a failed fetch still renders the banner", !!banner, html.slice(0, 60));
        check("the fallback is English", /We use cookies/.test(html), html.slice(0, 70));
        check("the fallback link is still localized", html.includes('href="/th/privacy/"'), "href=" + (html.match(/href="[^"]+"/) || ["?"])[0]);
    }

    // ------------------------------------------- 5. every language has strings
    {
        const langs = ["ar", "de", "en", "es", "fr", "hi", "ja", "pt", "ru", "th", "zh"];
        const missing = [];
        for (const l of langs) {
            const f = path.join(REPO, "i18n", "cookie", l + ".json");
            if (!fs.existsSync(f)) { missing.push(l + " (no file)"); continue; }
            try {
                const d = JSON.parse(fs.readFileSync(f, "utf8"));
                for (const k of ["heading", "body", "link", "essential", "accept", "label"]) {
                    if (typeof d[k] !== "string" || !d[k]) missing.push(l + "." + k);
                }
                if (!d.body.includes("{link}")) missing.push(l + ".body has no {link}");
            } catch (e) {
                missing.push(l + " (unparseable: " + e.message + ")");
            }
        }
        check("all 11 languages have a complete cookie dictionary", missing.length === 0, missing.join(", ") || "11/11 complete");
    }

    // ------------------------------------ 6. the REAL page load order
    //
    // The single-file test above cannot see the defect this group exists
    // for. On a real page BOTH js/main.min.js and js/cookie-consent.js run,
    // and the <script> order in every template puts main.min.js FIRST
    // (both are `defer`, so they execute in document order).
    //
    // Until 2026-11-02 main.min.js built its OWN hard-coded English banner
    // with the id 'wa-cookie-banner'; cookie-consent.js builds the
    // LOCALIZED one with the SAME id and guards on that id already existing.
    // So the English banner won on all 10 non-English sites: the localized
    // dictionary was fetched and thrown away, and the privacy link always
    // pointed at the English /privacy/ page.
    //
    // This group replays the real order for all 11 languages.
    {
        const MAIN_SRC = fs.readFileSync(path.join(REPO, "js", "main.min.js"), "utf8");
        const html = fs.readFileSync(path.join(REPO, "index.html"), "utf8");
        const orderMain = html.indexOf("main.min.js");
        const orderCookie = html.indexOf("cookie-consent.js");
        check(
            "main.min.js is loaded before cookie-consent.js (the order that used to break it)",
            orderMain > -1 && orderCookie > -1 && orderMain < orderCookie,
            "main.min.js at " + orderMain + ", cookie-consent.js at " + orderCookie
        );

        const langs = ["en", "ar", "de", "es", "fr", "hi", "ja", "pt", "ru", "th", "zh"];
        const bad = [];
        for (const l of langs) {
            const store = {};
            const doc = installDom(l, store);
            installFetch((url) => {
                const name = String(url).replace("/i18n/cookie/", "").replace(/\.json$/, "");
                try {
                    return JSON.parse(fs.readFileSync(path.join(REPO, "i18n", "cookie", name + ".json"), "utf8"));
                } catch (e) {
                    return null;
                }
            });
            // eslint-disable-next-line no-new-func
            new Function(MAIN_SRC)();   // first, as on a real page
            // eslint-disable-next-line no-new-func
            new Function(SRC)();        // second
            await settle();

            const banner = doc.getElementById("wa-cookie-banner");
            const dict = JSON.parse(fs.readFileSync(path.join(REPO, "i18n", "cookie", l + ".json"), "utf8"));
            const bhtml = banner ? banner.innerHTML : "";
            const prefix = l === "en" ? "" : "/" + l;
            if (!banner) bad.push(l + ": no banner");
            else if (bhtml.indexOf(dict.heading) === -1) bad.push(l + ": English heading");
            else if (bhtml.indexOf(dict.link) === -1) bad.push(l + ": English link text");
            else if (bhtml.indexOf(prefix + "/privacy/") === -1) bad.push(l + ": privacy link not localized");
        }
        check(
            "on the real load order the LOCALIZED banner wins in all 11 languages",
            bad.length === 0,
            bad.length === 0 ? "11/11 localized" : bad.join("; ")
        );

        // The regression this guards against is a SECOND implementation of
        // the banner appearing anywhere in the shared scripts. Only real
        // CODE counts -- a comment that merely names the id is fine, so the
        // comment blocks are stripped before the check.
        const mainJs = fs.readFileSync(path.join(REPO, "js", "main.js"), "utf8");
        const stripComments = (src) => src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
        const dup = [];
        for (const [name, src] of [["js/main.js", mainJs], ["js/main.min.js", MAIN_SRC]]) {
            const code = stripComments(src);
            if (code.indexOf("wa-cookie-banner") !== -1) dup.push(name + " still creates the banner");
            if (/createElement\(\s*["']div["']\s*\)[\s\S]{0,200}wa-cookie-banner/.test(code)) dup.push(name + " still builds the banner");
        }
        check(
            "no second banner implementation in the shared scripts",
            dup.length === 0,
            dup.length === 0 ? "js/cookie-consent.js is the single source of truth" : dup.join("; ")
        );
    }

    console.log("=== cookie consent ===");
    for (const [name, ok, detail] of checks) {
        console.log(`  ${ok ? "PASS" : "FAIL"}  ${name}`);
        console.log(`        ${detail}`);
    }
    console.log(`\n${failures === 0 ? "ALL CHECKS PASSED" : failures + " CHECK(S) FAILED"}`);
    process.exit(failures === 0 ? 0 : 1);
}

run().catch((e) => {
    console.error("TEST ERROR:", e && e.stack ? e.stack : e);
    process.exit(2);
});
