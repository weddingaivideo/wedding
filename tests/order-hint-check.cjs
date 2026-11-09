#!/usr/bin/env node
/**
 * Guards the /order/ service hint.
 *
 * Two things used to be wrong here and both are easy to reintroduce:
 *
 *  1. The page fetched the WHOLE i18n dictionary client-side
 *     (/i18n/<lang>.json) just to read about a dozen strings.
 *     For hi that was 16.4 MB, for th 14.3 MB - on the page that converts.
 *     It now loads one namespace shard (a few KB).
 *
 *  2. The delivery / best-for strings were hardcoded English.
 *     Ten of the eleven services reuse the pricing page's own delivery
 *     strings (pricing.td_text.*). The "other / not sure yet" service had
 *     no translated equivalent and fell back to English in every language.
 *
 * Both are checked here: statically (no page may fetch a whole dictionary)
 * and behaviourally (the hint must render in the visitor's language, and
 * must still fall back to English when the shard cannot be loaded).
 */
const fs = require("fs");
const path = require("path");

const REPO = path.resolve(__dirname, "..");
const ORDER_HTML = path.join(REPO, "order", "index.html");
const LANGS = ["en", "de", "es", "fr", "pt", "ja", "zh", "ar", "th", "hi", "ru"];
const SHARD_NS = "pricing.td_text";

let failures = 0;
function check(label, ok, detail) {
  console.log(`  ${ok ? "PASS" : "FAIL"}  ${label}${detail ? " - " + detail : ""}`);
  if (!ok) failures++;
}

// ---------------------------------------------------------------------------
// 1. Static: no page may download a whole dictionary client-side.
// ---------------------------------------------------------------------------
console.log("=== client-side dictionary downloads ===");
const pageFiles = [];
(function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith(".") || entry.name === "node_modules") continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full);
    else if (entry.name.endsWith(".html")) pageFiles.push(full);
  }
})(REPO);

const offenders = [];
for (const file of pageFiles) {
  const src = fs.readFileSync(file, "utf8");
  // A client-side fetch of a WHOLE dictionary is one whose path under
  // /i18n/ has no sub-directory: /i18n/<lang>.json.
  // /i18n/shards/<lang>/<ns>.json and /i18n/cookie/<lang>.json are fine -
  // they are small and purpose-built.
  // Quotes are stripped first so that both the template-literal form
  // (`/i18n/${lang}.json`) and the concatenation form
  // (`'/i18n/' + lang + '.json'`) are caught.
  // Normalise first: drop the quotes and glue the string pieces together,
  // so that `'/i18n/' + lang + '.json'` and `'/i18n/${lang}.json'` both
  // collapse to `/i18n/lang.json`. A path that gains a sub-directory
  // (`/i18n/shards/...`, `/i18n/cookie/...`) is a small purpose-built file
  // and is fine.
  // Line comments are ignored first: a comment that mentions the old path
  // must not trip the gate. `://` is preserved so that absolute URLs are
  // not truncated.
  const noComments = src.replace(/(^|[^:])\/\/[^\n]*/g, "$1");
  const flat = noComments.replace(/['"`]/g, "").replace(/\s*\+\s*/g, "");
  if (/\/i18n\/[^/]*\.json/.test(flat)) {
    offenders.push(path.relative(REPO, file));
  }
}
check(
  "no page fetches a whole i18n dictionary client-side",
  offenders.length === 0,
  offenders.length ? offenders.slice(0, 5).join(", ") : `${pageFiles.length} pages scanned`
);

// ---------------------------------------------------------------------------
// 2. Static: every key the hint script needs must exist in every shard.
// ---------------------------------------------------------------------------
console.log("\n=== hint keys are present in every language shard ===");
const orderSrc = fs.readFileSync(ORDER_HTML, "utf8");
const needed = new Set();
for (const m of orderSrc.matchAll(/'(delivery-key|best-for-key)'\s*:\s*'([^']+)'/g)) {
  if (m[2]) needed.add(m[2]);
}
check("the hint script declares keys", needed.size > 0, `${needed.size} keys`);

const missingPerLang = [];
for (const lang of LANGS) {
  const shard = path.join(REPO, "i18n", "shards", lang, `${SHARD_NS}.json`);
  if (!fs.existsSync(shard)) {
    missingPerLang.push(`${lang}: no shard file`);
    continue;
  }
  const d = JSON.parse(fs.readFileSync(shard, "utf8"));
  const missing = [...needed].filter((k) => !(k in d));
  if (missing.length) missingPerLang.push(`${lang}: ${missing.join(", ")}`);
}
check(
  "every language shard carries every hint key",
  missingPerLang.length === 0,
  missingPerLang.length ? missingPerLang.slice(0, 4).join(" | ") : `${LANGS.length} languages`
);

// ---------------------------------------------------------------------------
// 3. Behavioural: run the page's inline script against a minimal DOM.
// ---------------------------------------------------------------------------
console.log("\n=== the hint renders in the visitor's language ===");
(async () => {
const blocks = [...orderSrc.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)];
const target = blocks.find((b) => b[1].includes("var HINTS = {"));
if (!target) {
  check("the hint script exists in order/index.html", false);
} else {
  const scriptSrc = target[1];

  function makeEl(tag) {
    const el = {
      tagName: String(tag || "div").toUpperCase(),
      _id: "",
      style: {},
      attrs: {},
      innerHTML: "",
      children: [],
      listeners: {},
      setAttribute(k, v) { this.attrs[k] = v; },
      getAttribute(k) { return this.attrs[k]; },
      addEventListener(ev, fn) { (this.listeners[ev] = this.listeners[ev] || []).push(fn); },
      querySelector(sel) {
        const field = /data-field="([^"]+)"/.exec(sel);
        if (!field) return null;
        return this.children.find((c) => c.attrs["data-field"] === field[1]) || null;
      },
    };
    Object.defineProperty(el, "id", {
      get() { return this._id; },
      set(v) { this._id = v; },
    });
    return el;
  }

  function installDom(lang, service) {
    const registry = {};
    const sel = makeEl("select");
    sel.value = service;
    registry["service"] = sel;
    const hint = makeEl("div");
    for (const f of ["price", "delivery", "best-for"]) {
      const s = makeEl("span");
      s.attrs["data-field"] = f;
      hint.children.push(s);
    }
    registry["service-hint"] = hint;
    globalThis.document = {
      documentElement: { lang },
      body: makeEl("body"),
      createElement: (t) => makeEl(t),
      getElementById: (id) => registry[id] || null,
      querySelector: () => null,
      querySelectorAll: () => [],
      addEventListener: () => {},
    };
    globalThis.window = { location: { search: "" } };
    return registry;
  }

  const fetched = [];
  globalThis.fetch = async (url) => {
    fetched.push(String(url));
    const rel = String(url).split("?")[0].replace(/^\//, "");
    const file = path.join(REPO, rel);
    if (!fs.existsSync(file)) return { ok: false, json: async () => ({}) };
    return { ok: true, json: async () => JSON.parse(fs.readFileSync(file, "utf8")) };
  };

  const services = [...new Set([...orderSrc.matchAll(/^\s*'([a-z0-9-]+)':\s*\{price:/gm)].map((m) => m[1]))];
  let bad = [];
  let wholeDict = [];

  for (const lang of LANGS) {
    for (const svc of services) {
      fetched.length = 0;
      const reg = installDom(lang, svc);
      new Function(scriptSrc)();
      await new Promise((r) => setTimeout(r, 25));
      const hint = reg["service-hint"];
      const delivery = hint.querySelector('[data-field="delivery"]').innerHTML;
      const bestFor = hint.querySelector('[data-field="best-for"]').innerHTML;
      if (!delivery || !bestFor) bad.push(`${lang}/${svc}: empty hint`);
      if (lang === "ru") {
        if (!/[\u0400-\u04FF]/.test(delivery)) bad.push(`${lang}/${svc}: delivery not translated`);
        if (!/[\u0400-\u04FF]/.test(bestFor)) bad.push(`${lang}/${svc}: best-for not translated`);
      }
      if (fetched.some((f) => /\/i18n\/[^/]+\.json/.test(f))) wholeDict.push(`${lang}/${svc}`);
    }
  }
  check(
    `all ${services.length} services render a non-empty, translated hint`,
    bad.length === 0,
    bad.length ? bad.slice(0, 4).join(" | ") : `${LANGS.length} languages`
  );
  check(
    "no language downloads a whole dictionary",
    wholeDict.length === 0,
    wholeDict.length ? wholeDict.slice(0, 4).join(", ") : "shard only"
  );

  // The English fallback must still work when the shard cannot be loaded.
  const reg = installDom("ru", services[0]);
  globalThis.fetch = async () => ({ ok: false, json: async () => ({}) });
  new Function(scriptSrc)();
  await new Promise((r) => setTimeout(r, 25));
  const fbDelivery = reg["service-hint"].querySelector('[data-field="delivery"]').innerHTML;
  const fbBestFor = reg["service-hint"].querySelector('[data-field="best-for"]').innerHTML;
  check(
    "English fallback when the shard is unavailable",
    fbDelivery.length > 0 && fbBestFor.length > 0,
    `delivery="${fbDelivery.slice(0, 30)}"`
  );
}

console.log(`\n${failures === 0 ? "ALL CHECKS PASSED" : failures + " CHECK(S) FAILED"}`);
process.exit(failures === 0 ? 0 : 1);
})();

