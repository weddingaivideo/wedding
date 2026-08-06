/**
 * Cloudflare Pages Function — /__csp_report
 * Receives Content-Security-Policy violation reports from the browser.
 * Logs them to Cloudflare's console (visible in Pages → Logs).
 * To escalate: pipe to a Slack webhook, Sentry, or Workers Analytics Engine.
 */
export async function onRequestPost({ request }) {
    try {
        const report = await request.json();
        const cspReport = report["csp-report"] || report;
        console.warn("CSP violation:", JSON.stringify({
            documentUri: cspReport["document-uri"],
            violatedDirective: cspReport["violated-directive"],
            blockedUri: cspReport["blocked-uri"],
            sourceFile: cspReport["source-file"],
            lineNumber: cspReport["line-number"],
            originalPolicy: cspReport["original-policy"]?.slice(0, 200),
        }));
    } catch (e) {
        console.error("CSP report parse failed:", e.message);
    }
    return new Response(null, { status: 204 });
}

export async function onRequest() {
    return new Response("Method Not Allowed", {
        status: 405,
        headers: { Allow: "POST" },
    });
}
