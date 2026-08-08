// Offline check for the new stacked-locale 1-hop redirect algorithm.
// Mirrors the snippet now in functions/_middleware.js.

const LANGS = "(en|zh|es|fr|de|pt|ja|ru|ar|th)";

function resolve(rest, search = "") {
    let finalLang = null;
    let stripped = rest;
    for (let i = 0; i < 10; i++) {
        const m = stripped.match(new RegExp(`^/${LANGS}(/|$)`));
        if (!m) break;
        const innerRest = stripped.slice(3);
        const wouldStillHaveLang = innerRest.match(new RegExp(`^/${LANGS}(/|$)`));
        if (!wouldStillHaveLang) {
            finalLang = m[1];
            stripped = innerRest;
            break;
        }
        stripped = innerRest;
    }
    if (finalLang === null) return null;
    return `/${finalLang}${stripped}${search}`;
}

const cases = [
    // [input_rest, expected_target, description]
    ["/de/blog/", "/de/blog/", "1 layer (zh/de/blog/ → de/blog/)"],
    ["/zh/blog/", "/zh/blog/", "1 layer (zh/zh/blog/ → zh/blog/)"],
    ["/zh/zh/blog/", "/zh/blog/", "2 layers (zh/zh/zh/blog/ → zh/blog/)"],
    ["/zh/zh/zh/blog/", "/zh/blog/", "3 layers — the one that used to take 3 hops"],
    ["/zh/zh/zh/zh/blog/", "/zh/blog/", "4 layers"],
    ["/zh/zh/zh/zh/zh/blog/", "/zh/blog/", "5 layers"],
    ["/zh/zh/zh/zh/zh/zh/blog/", "/zh/blog/", "6 layers"],
    ["/zh/zh/zh/zh/zh/zh/zh/blog/", "/zh/blog/", "7 layers — max within i<8 loop"],
    ["/zh", "/zh", "zh/zh bare (rest=/zh, no trailing slash)"],
    ["/zh/", "/zh/", "zh/zh/ with trailing slash (rest=/zh/)"],
    ["/es/blog/", "/es/blog/", "de/pt/es/blog/ — non-zh peeling"],
    ["/es/blog/ai-photos-to-wedding-video/", "/es/blog/ai-photos-to-wedding-video/", "deep path"],
    ["/blog/zh/", null, "rest is NOT a lang segment — no redirect"],
    ["/blog/about/", null, "rest is NOT a lang segment — no redirect"],
    ["/zz/", null, "zz is not a supported lang — no redirect"],
    ["/", null, "bare '/' is a NON-stacked case (path was just /<lang>) — no redirect from here"],
    ["/about", null, "/about alone is non-stacked"],
    ["/de/zh/zh/zh/zh/zh/zh/zh/zh/blog/", "/zh/blog/", "9 lang segments (de+8 zh) — should 1-hop peel to /zh/blog/"],
    ["/zh/zh/zh/zh/zh/zh/zh/zh/zh/blog/", "/zh/blog/", "10 lang segments — should 1-hop peel to /zh/blog/"],
    ["/de/zh/zh/zh/zh/zh/zh/zh/zh/zh/zh/blog/", null, "11 lang segments — exceeds i<10 safety net, won't fully peel (shouldn't naturally occur)"],
];

let fail = 0;
for (const [rest, expected, desc] of cases) {
    const got = resolve(rest);
    const ok = got === expected;
    if (!ok) fail++;
    console.log(`${ok ? "PASS" : "FAIL"}  rest=${rest.padEnd(45)}  expect=${String(expected).padEnd(40)}  got=${got}  -- ${desc}`);
}
console.log(`\n${fail === 0 ? "ALL PASS" : `${fail} FAIL`}`);
process.exit(fail === 0 ? 0 : 1);
