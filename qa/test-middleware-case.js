// Quick logic test for maybeLowercaseRedirect
// Mimics the function from _middleware.js to verify behavior

function maybeLowercaseRedirect(path, url) {
    if (path === path.toLowerCase()) return null;
    // Case-insensitive prefix check: /API/QUOTE should also be skipped, not
    // lowercased to /api/quote. The 308 would change the URL the client hits,
    // and even though 308 preserves the method, we don't want a behavioral
    // change for an API client that may be relying on the exact case path.
    const lower = path.toLowerCase();
    if (lower.startsWith("/api/") || lower.startsWith("/functions/")) return null;
    if (lower.startsWith("/i18n/") || lower.startsWith("/admin/")) return null;
    return new Response(null, {
        status: 308,
        headers: { "Location": path.toLowerCase() + url.search },
    });
}

const cases = [
    // [path, url, expected_action, expected_location]
    ["/About/",             "/About/",            "redirect", "/about/"],
    ["/Pricing/",           "/Pricing/",          "redirect", "/pricing/"],
    ["/BLOG/",              "/BLOG/",             "redirect", "/blog/"],
    ["/ZH/Blog/Foo/",       "/ZH/Blog/Foo/",      "redirect", "/zh/blog/foo/"],
    ["/STYLES.MIN.CSS",     "/STYLES.MIN.CSS",    "redirect", "/styles.min.css"],
    ["/FAVICON.ICO",        "/FAVICON.ICO",       "redirect", "/favicon.ico"],
    ["/about/",             "/about/",            "pass",     null],
    ["/blog/",              "/blog/",             "pass",     null],
    ["/zh/blog/foo/",       "/zh/blog/foo/",      "pass",     null],
    ["/api/quote",          "/api/quote",         "pass",     null],
    ["/API/QUOTE",          "/API/QUOTE",         "pass",     null],     // explicitly skipped
    ["/functions/foo",      "/functions/foo",     "pass",     null],
    ["/i18n/En.JSON",       "/i18n/En.JSON",      "pass",     null],     // explicitly skipped
    ["/admin/dashboard",    "/admin/dashboard",   "pass",     null],
    ["/About/",             "/About/?utm=x",      "redirect", "/about/?utm=x"],
    ["/BLOG/about-us/",     "/BLOG/about-us/",    "redirect", "/blog/about-us/"],
    ["/",                   "/",                  "pass",     null],
    ["/favicon.ico",        "/favicon.ico",       "pass",     null],
];

let pass = 0, fail = 0;
for (const [path, url, want, wantLoc] of cases) {
    const r = maybeLowercaseRedirect(path, new URL(url, "https://weddingai.video"));
    const got = r ? "redirect" : "pass";
    const gotLoc = r ? r.headers.get("Location") : null;
    const ok = (got === want) && (wantLoc === null || gotLoc === wantLoc);
    if (ok) { pass++; }
    else {
        fail++;
        console.log(`FAIL: ${path} → got ${got} (loc=${gotLoc}), want ${want} (loc=${wantLoc})`);
    }
}
console.log(`\n${pass}/${pass+fail} passed, ${fail} failed`);
process.exit(fail > 0 ? 1 : 0);
