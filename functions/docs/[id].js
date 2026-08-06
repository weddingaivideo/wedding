// Catch-all 404 for /docs/<id> — used to keep internal operator docs out
// of the public site. Cloudflare Pages serves static files ahead of
// _redirects rules, so a redirect rule cannot override a real file; a
// Function can, and is the supported way to shadow a static path.
//
// This matches any single segment under /docs/. It also matches the
// directory itself via the (optional) index handler at the same path.
//
// Once the operator confirms the rotation is complete and the source
// file has been moved out of the project (e.g. to ~/.minimax/), this
// function can be deleted; the static file in the bucket will still
// be served until purged, so leave this in place for at least one
// full deploy cycle after the bucket entry is no longer needed.

export async function onRequest(context) {
    return new Response("Not Found", {
        status: 404,
        headers: {
            "Content-Type": "text/plain; charset=utf-8",
            "X-Robots-Tag": "noindex, nofollow",
            "Cache-Control": "public, max-age=300, must-revalidate",
        },
    });
}
