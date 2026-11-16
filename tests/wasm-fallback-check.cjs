#!/usr/bin/env node
/**
 * The WebAssembly fallback must not be SILENT.
 *
 * THE DEFECT
 * -----------
 * pica (MIT) does the high-quality resize; its WASM resampler is INLINED in
 * the bundle, so it needs 'wasm-unsafe-eval' in the CSP. When the CSP
 * blocks the WebAssembly compile, pica's own has_wasm() returns FALSE and
 * pica falls back to its plain-JS resampler. The tool still worked, the
 * photo was just visibly softer - and NOTHING on the page said so. The
 * only trace was a console.warn, which nobody reads.
 *
 * The other two WASM consumers are already loud: the AVIF encoder throws
 * "The AVIF encoder did not load." and the MODNet matting throws. pica was
 * the quiet one.
 *
 * WHAT THIS TEST PROVES
 * ---------------------
 * It loads the REAL js/tools/common.js into a stubbed browser, forces the
 * WASM-absent path (pica.has_wasm() -> false) and asserts that a notice
 * element reaches document.body. A reader can see it.
 *
 * The negative control (--negative-control) removes the notice call from
 * the source and asserts the check then FAILS. A check that cannot fail
 * proves nothing.
 *
 * Run:  node tests/wasm-fallback-check.cjs
 *       node tests/wasm-fallback-check.cjs --negative-control
 */
const fs = require("fs");
const path = require("path");

const REPO = path.resolve(__dirname, "..");
const COMMON = path.join(REPO, "js", "tools", "common.js");

let failures = 0;
function check(label, ok, detail) {
    console.log(`  ${ok ? "PASS" : "FAIL"}  ${label}${detail ? " - " + detail : ""}`);
    if (!ok) failures++;
}

// ---------------------------------------------------------------------------
// A browser, in as much as the code under test needs.
// ---------------------------------------------------------------------------
function makeSandbox() {
    const appended = [];
    const notices = [];

    function makeElement(tag) {
        const el = {
            tagName: String(tag).toUpperCase(),
            style: { cssText: "" },
            children: [],
            textContent: "",
            className: "",
            attrs: {},
            setAttribute(k, v) { this.attrs[k] = v; },
            getAttribute(k) { return this.attrs[k]; },
            appendChild(child) { this.children.push(child); appended.push(child); return child; },
        };
        if (el.tagName === "CANVAS") {
            el.width = 0;
            el.height = 0;
            el.getContext = () => ({
                drawImage() {}, fillRect() {}, fillText() {}, getImageData: () => ({ data: [] }),
                save() {}, restore() {}, translate() {}, scale() {}, clearRect() {},
                measureText: () => ({ width: 0 }),
            });
        }
        return el;
    }

    const body = makeElement("body");
    const head = makeElement("head");
    const doc = {
        body,
        head,
        documentElement: makeElement("html"),
        createElement: makeElement,
        createTextNode: (t) => ({ textContent: t }),
        addEventListener() {},
        querySelector: () => null,
        querySelectorAll: () => [],
        fonts: { ready: Promise.resolve() },
    };

    const warnings = [];
    const sandbox = {
        window: null,
        document: doc,
        console: {
            warn: (...a) => warnings.push(a.join(" ")),
            log: () => {}, error: () => {}, info: () => {},
        },
        setTimeout, clearTimeout, setInterval, clearInterval,
        Promise, Math, Date, JSON, Uint8Array, Float32Array, Array, Object, Error,
        navigator: { userAgent: "node", language: "en" },
        location: { href: "https://weddingai.video/tools/compress-wedding-photos/" },
        URL: { createObjectURL: () => "blob:x", revokeObjectURL() {} },
        Blob: class { }, FileReader: class { },
        Image: class { set src(v) { } },
        __appended: appended,
        __warnings: warnings,
    };
    sandbox.window = sandbox;
    sandbox.self = sandbox;
    return sandbox;
}

// ---------------------------------------------------------------------------
// Load the real common.js into the sandbox.
// ---------------------------------------------------------------------------
function loadCommon(source) {
    const sandbox = makeSandbox();

    // pica, already loaded, with its WASM missing - exactly what a CSP
    // without 'wasm-unsafe-eval' produces.
    function picaStub() {
        return {
            resize(source, out) {
                out.width = 10; out.height = 10;
                return Promise.resolve();
            },
        };
    }
    picaStub.has_wasm = function () { return false; };
    sandbox.window.pica = picaStub;

    const fn = new Function(
        "window", "document", "console", "navigator", "location", "URL",
        "Blob", "FileReader", "Image", "setTimeout", "clearTimeout",
        "setInterval", "clearInterval", "Promise", "Math", "Date", "JSON",
        "Uint8Array", "Float32Array", "Array", "Object", "Error",
        source + "\n;return window.weddingAITool;");
    const api = fn(sandbox.window, sandbox.document, sandbox.console,
        sandbox.navigator, sandbox.location, sandbox.URL, sandbox.Blob,
        sandbox.FileReader, sandbox.Image, sandbox.setTimeout,
        sandbox.clearTimeout, sandbox.setInterval, sandbox.clearInterval,
        sandbox.Promise, sandbox.Math, sandbox.Date, sandbox.JSON,
        sandbox.Uint8Array, sandbox.Float32Array, sandbox.Array, sandbox.Object,
        sandbox.Error);
    return { sandbox, api };
}

function visibleNotices(sandbox) {
    return sandbox.__appended.filter(el =>
        el && el.id === "wa-wasm-notice" &&
        typeof el.textContent === "string" && el.textContent.trim() !== "");
}

// ---------------------------------------------------------------------------
console.log("=== the WASM fallback reaches the reader ===");
const source = fs.readFileSync(COMMON, "utf8");
const { sandbox, api } = loadCommon(source);

check("the tool namespace loaded", !!api && typeof api.resizeCanvas === "function");

const fakeImage = { naturalWidth: 100, naturalHeight: 100, width: 100, height: 100 };

api.resizeCanvas(fakeImage, 50, 50)
    .then(() => {
        const notices = visibleNotices(sandbox);
        check("a notice element with text reached document.body", notices.length === 1,
            notices.length ? JSON.stringify(notices[0].textContent.slice(0, 60))
                : "no notice element");
        check("the notice is announced to assistive tech",
            notices.length === 1 && notices[0].getAttribute("role") === "status");
        check("the console still carries the detail",
            sandbox.__warnings.some(w => w.indexOf("wasm-unsafe-eval") >= 0),
            sandbox.__warnings.length ? sandbox.__warnings[0] : "no warning");

        // the notice is a runtime string: it has to resolve through the
        // tools.copy namespace, or it stays English on every page.
        const copyKey = (source.match(/wasmFallback:\s*'([^']+)'/) || [])[1];
        check("the notice resolves through the tools.copy namespace",
            !!copyKey && copyKey.indexOf("tools.copy.") === 0, copyKey || "no key");

        if (process.argv.indexOf("--negative-control") >= 0) {
            console.log("\n=== negative control: remove the notice and the check must fail ===");
            const broken = source.replace(/announceWasmFallback\('pica has no WASM'\);/, "");
            if (broken === source) {
                console.log("[FAIL] negative control: the notice call was not found to remove");
                failures++;
                return;
            }
            const b = loadCommon(broken);
            // the promise has to be RETURNED, or the summary below runs
            // before this check does
            return b.api.resizeCanvas(fakeImage, 50, 50).then(() => {
                const n = visibleNotices(b.sandbox);
                check("without the notice call the check FAILS", n.length === 0,
                    n.length ? "a notice still appeared" : "no notice - the check would fail");
            });
        }
    })
    .catch((e) => {
        console.log("  FAIL  resizeCanvas threw: " + e.message);
        failures++;
    })
    .then(() => {
        console.log(`\nRESULT: ${failures} failure(s)`);
        process.exit(failures ? 1 : 0);
    });
