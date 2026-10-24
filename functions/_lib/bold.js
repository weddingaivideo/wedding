/**
 * WeddingAI.video — markdown-style bold markers → real <strong> markup.
 *
 * WHY THIS EXISTS
 * ---------------
 * The content pipeline writes emphasis as **text**. Nothing ever turned
 * those markers into markup: js/i18n.js only handles the language switcher,
 * and the middleware's applyDataI18n() copies the translation value in
 * verbatim. The result was that readers saw raw asterisks on 456 of the
 * 722 pages — 37,704 markers in the static HTML plus ~252,000 more inside
 * i18n/<lang>.json, i.e. in every one of the 11 languages.
 *
 * styles.css already carries `.blog-article strong { ... }`, and 12,784
 * i18n values already use a literal <strong> — so <strong> is the markup
 * this copy was always meant to render as.
 *
 * RULES (deliberately conservative)
 * ---------------------------------
 *  1. Only text is converted. Tags, comments, <script>, <style>, <pre> and
 *     <code> are opaque, so a ** inside an attribute value or a code
 *     sample can never be touched.
 *  2. A pair is only converted when both markers sit in the same block
 *     scope. A bold run therefore can never span a paragraph, list item or
 *     table cell and break the markup around it, while inline elements
 *     (<a>, <em>, <span>, <br>) may still sit inside the bold run.
 *  3. A marker without a partner, an empty run, or an implausibly long run
 *     is left as literal text rather than inventing emphasis. The corpus
 *     has 28 such live values; they are fixed at source, not guessed here.
 *
 * PERFORMANCE
 * -----------
 * One tokenizer pass over the document, ~1.8 ms for a 55 KB page once the
 * JIT is warm. The middleware already runs several full-document regex
 * passes (applyDataI18n, applyDataI18nAttr, the meta rewrites), so this
 * fits in the same budget; the whole transform is cached for 5 minutes
 * per (lang, path) anyway.
 */

/** Elements whose open/close tag ends the current bold scope. */
const BOLD_BLOCK_TAGS = new Set([
    "p", "div", "li", "ul", "ol", "dl", "dt", "dd", "td", "th", "tr", "thead",
    "tbody", "tfoot", "table", "section", "article", "header", "footer", "nav",
    "aside", "blockquote", "figure", "figcaption", "main", "body", "html", "head",
    "form", "fieldset", "legend", "h1", "h2", "h3", "h4", "h5", "h6", "hr",
    "pre", "address", "details", "summary", "caption", "colgroup", "picture",
    "video", "audio", "canvas", "noscript", "template",
]);

/**
 * The longest legitimate bold run in the corpus is 181 characters. Anything
 * longer than this is a stray marker, not emphasis.
 */
const BOLD_MAX_RUN = 400;

/**
 * Tokenizer. Every character of the input is covered by exactly one
 * alternative, so the tokens concatenate back to the original string.
 *   1 comment | 2 protected block | 3 tag | 4 ** marker | 5 text | 6 * | 7 <
 */
const BOLD_TOKEN_RE =
    /<!--[\s\S]*?-->|<(script|style|pre|code)\b[^>]*>[\s\S]*?<\/\1>|<[^>]*>|\*\*|[^*<]+|\*|</g;

const BOLD_TAG_NAME_RE = /^<\/?\s*([a-zA-Z][a-zA-Z0-9-]*)/;

function isProtectedStart(t) {
    return t.startsWith("<!--") ||
        t.startsWith("<script") ||
        t.startsWith("<style") ||
        t.startsWith("<pre") ||
        t.startsWith("<code");
}

/**
 * Convert **bold** markers in an HTML string to <strong>bold</strong>.
 * Returns the input unchanged when there is nothing to do.
 */
export function convertBoldMarkers(html) {
    if (typeof html !== "string" || html.indexOf("**") === -1) return html;

    const toks = html.match(BOLD_TOKEN_RE);
    if (!toks || toks.length < 2) return html;

    const n = toks.length;
    const scopeOf = new Array(n);
    const marks = [];
    let scope = 0;

    for (let i = 0; i < n; i++) {
        const t = toks[i];
        if (t.charCodeAt(0) === 60 /* '<' */) {
            if (!isProtectedStart(t)) {
                const mm = BOLD_TAG_NAME_RE.exec(t);
                const name = mm ? mm[1].toLowerCase() : "";
                if (BOLD_BLOCK_TAGS.has(name)) scope++;
            }
            scopeOf[i] = scope;
            continue;
        }
        scopeOf[i] = scope;
        if (t === "**") marks.push(i);
    }

    if (marks.length < 2) return html;

    const openAt = new Map();
    const closeAt = new Map();

    let k = 0;
    while (k < marks.length) {
        const ti = marks[k];
        const sc = scopeOf[ti];
        // The partner must live in the same block scope.
        let j = k + 1;
        while (j < marks.length && scopeOf[marks[j]] !== sc) j++;
        if (j >= marks.length) { k++; continue; }

        const cj = marks[j];
        let between = "";
        for (let x = ti + 1; x < cj; x++) {
            const tt = toks[x];
            if (tt.charCodeAt(0) !== 60) between += tt; // text only
        }
        // An empty run is not emphasis, and a run this long is a stray
        // marker that would swallow half a paragraph.
        if (between.trim() === "" || between.length > BOLD_MAX_RUN) { k++; continue; }

        openAt.set(ti, cj);
        closeAt.set(cj, ti);
        k = j + 1;
    }

    if (openAt.size === 0) return html;

    const out = [];
    for (let i = 0; i < n; i++) {
        if (openAt.has(i)) { out.push("<strong>"); continue; }
        if (closeAt.has(i)) { out.push("</strong>"); continue; }
        out.push(toks[i]);
    }
    return out.join("");
}

export default convertBoldMarkers;
