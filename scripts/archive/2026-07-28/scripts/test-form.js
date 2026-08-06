#!/usr/bin/env node
/**
 * Local form-submission test.
 * Usage:
 *   1. Start wrangler in another terminal:  npx wrangler pages dev . --port 8788
 *   2. Run:                                node scripts/test-form.js
 *
 * Sends a fake form submission to your local Pages Function and prints
 * the response status + redirect target. Verifies the function is wired up.
 */

const PORT = process.env.PORT || 8788;
const URL = `http://localhost:${PORT}/api/quote`;

const payload = new URLSearchParams({
    name: "Test User",
    email: "test@example.com",
    country: "US",
    wedding_date: "2026-08-15",
    service: "ai-video-generator",
    video_duration: "10 minutes",
    upload_link: "",
    budget: "100-300",
    details: "This is a test submission from scripts/test-form.js. If you got this, the function is wired up correctly.",
    referral: "Test",
    botcheck: "",  // honeypot must be empty
});

console.log(`POST ${URL}\n`);

fetch(URL, {
    method: "POST",
    body: payload,
    redirect: "manual",  // don't auto-follow; we want to see the 303
})
    .then((res) => {
        console.log(`Status: ${res.status} ${res.statusText}`);
        const location = res.headers.get("location");
        if (location) console.log(`Redirect: ${location}`);
        if (res.status === 303 && location?.includes("success.html")) {
            console.log("\n✅ Form backend working correctly.");
            if (!process.env.RESEND_API_KEY && !process.env.SILENT_OK) {
                console.log("   (Note: no RESEND_API_KEY in env → function silently redirected. Check Resend dashboard for actual delivery if you set the key.)");
            }
        } else if (res.status === 303) {
            console.log("\n⚠️  Got 303 but redirect target looks unexpected.");
        } else if (res.status === 405) {
            console.log("\n❌ Got 405 Method Not Allowed. Function not deployed to this URL?");
        } else {
            console.log("\n❌ Unexpected status. Check function logs in the wrangler terminal.");
        }
    })
    .catch((err) => {
        console.error("\n❌ Request failed:", err.message);
        console.error("   Is wrangler running? Start it with:  npx wrangler pages dev . --port 8788");
    });
