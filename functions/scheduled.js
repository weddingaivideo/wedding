/**
 * Cloudflare Pages Cron Trigger — /scheduled
 * Runs daily at 9am UTC (configured in the Cloudflare dashboard under
 * Pages → weddingai-video → Settings → Functions → Cron Triggers).
 * NOTE: wrangler.toml does NOT configure cron triggers (Pages wrangler.toml
 * doesn't support [[triggers]]); the schedule is set in the dashboard only.
 *
 * Purpose (2026-10-29 rewrite): make the lead pipeline tell the truth.
 *
 *   pending    → fresh submission, email not yet attempted
 *   sent       → the provider accepted the request (HTTP 2xx). NOT proof of
 *                delivery — a suppressed or later-bounced address also
 *                answers 2xx. This state is what /api/quote.js writes now.
 *   delivered  → the provider's own delivery event confirmed it
 *   failed     → the provider rejected it, or the delivery event says it
 *                bounced / was suppressed / complained
 *   abandoned  → retries exhausted, or the recipient is suppressed (retrying
 *                a suppressed address can never succeed)
 *
 * Before this rewrite the lead was marked "delivered" on the strength of a
 * 2xx alone. Between 2026-10-12 and 2026-10-29 the domain had no MX, the
 * recipient was hard-bounced once and then silently suppressed by the
 * provider — and every new lead was recorded as "delivered" while nothing
 * was ever delivered. Two real customers waited two weeks for a reply.
 *
 * Two jobs now:
 *   1. VERIFY  — for every lead in "sent", read the provider's delivery
 *                event back and write the real outcome into KV.
 *   2. RETRY   — re-send the leads that really failed.
 * Plus a guard: if the notification address itself is on the provider's
 * suppression list, say so loudly in the log and in the response, because
 * every send to it is dropped without a trace.
 *
 * Manual test (any time):
 *   curl -H "Authorization: Bearer ${CRON_TOKEN}" \
 *        https://weddingai.video/scheduled
 *
 * (The HTTP entry point is gated by CRON_TOKEN. The cron entry point is
 *  internal — only Cloudflare can invoke it.)
 *
 * Notifications: removed 2026-10-12. Results are only in function logs and KV.
 */

const FROM_ADDRESS = "WeddingAI Quote <noreply@weddingai.video>";
const TO_EMAIL_DEFAULT = "order@weddingai.video";
const MAX_RETRIES = 5;
const LEAD_TTL_SECONDS = 60 * 60 * 24 * 90;
const KV_LIST_LIMIT = 100; // per-run cap; paginate if we ever exceed this
const RESEND_API = "https://api.resend.com";

// A lead that stayed "sent" longer than this is reported as unconfirmed.
const SENT_STALE_HOURS = 48;

// Terminal delivery events — anything else means "still in flight".
const DELIVERED_EVENTS = new Set(["delivered"]);
const FAILED_EVENTS = new Set(["bounced", "failed", "complained", "suppressed"]);

// Cloudflare Pages Cron Trigger entry point
export async function scheduled(event, env, ctx) {
    ctx.waitUntil(retryFailedLeads(env, { trigger: "cron" }));
}

// Manual HTTP entry point — protected by CRON_TOKEN. Useful for testing
// the retry logic without waiting for the daily cron, and for one-off
// "force a retry now" when Resend comes back from an outage.
export async function onRequestGet({ request, env }) {
    const expected = (env.CRON_TOKEN || "").replace(/^\ufeff+/, "").trim();
    const provided =
        request.headers.get("Authorization")?.replace(/^Bearer\s+/i, "") || "";
    if (!expected) {
        return new Response("Not Found", { status: 404 });
    }
    if (provided !== expected) {
        return new Response("Forbidden", { status: 403 });
    }
    const result = await retryFailedLeads(env, { trigger: "manual" });
    return new Response(JSON.stringify(result, null, 2), {
        status: 200,
        headers: { "Content-Type": "application/json" },
    });
}

// Same rule as /api/quote.js: env.TO_EMAIL wins when it is a valid address.
function resolveToEmail(env) {
    const raw = (env.TO_EMAIL || "").replace(/^\ufeff+/, "").trim();
    if (!raw) return TO_EMAIL_DEFAULT;
    if (!/^[^\s@,<>]+@[^\s@,<>]+\.[^\s@,<>]+$/.test(raw)) {
        console.warn(`[CRON] env.TO_EMAIL is not a valid address ("${raw}") — falling back to ${TO_EMAIL_DEFAULT}`);
        return TO_EMAIL_DEFAULT;
    }
    return raw;
}

async function retryFailedLeads(env, { trigger }) {
    const kv = env.RATE_LIMIT_KV || env.LEAD_STORAGE;
    if (!kv) {
        console.error("[CRON] no KV bound, aborting");
        return { ok: false, reason: "no_kv" };
    }
    const apiKey = (env.RESEND_API_KEY || "").replace(/^\ufeff+/, "").trim();
    if (!apiKey) {
        console.error("[CRON] RESEND_API_KEY missing, aborting");
        return { ok: false, reason: "missing_api_key" };
    }

    const toAddress = resolveToEmail(env);
    const list = await kv.list({ prefix: "lead:", limit: KV_LIST_LIMIT });
    const counts = {
        scanned: list.keys.length,
        truncated: list.list_complete === false,
        verified: 0,
        retried: 0,
        succeeded: 0,
        failed: 0,
        abandoned: 0,
        unconfirmed: 0,
        recipient_suppressed: false,
    };

    // ---- guard: is our own notification address suppressed? ----
    // This is the check that would have caught the 2026-10-12..10-29 outage.
    let suppressed = new Set();
    try {
        suppressed = await getSuppressedAddresses(apiKey);
        counts.recipient_suppressed = suppressed.has(toAddress.toLowerCase());
        if (counts.recipient_suppressed) {
            console.error(
                `[CRON] THE NOTIFICATION ADDRESS ${toAddress} IS ON RESEND'S SUPPRESSION LIST. ` +
                "Every send to it is dropped without an error — the site will keep reporting success " +
                "while no lead ever arrives. Fix the recipient (env.TO_EMAIL) or clear the suppression."
            );
        }
    } catch (e) {
        console.error(`[CRON] could not read the suppression list: ${e && e.message ? e.message : e}`);
    }

    // ---- read every lead once ----
    const leads = [];
    for (const key of list.keys) {
        const record = await kv.get(key.name, { type: "json" });
        if (record) leads.push({ key: key.name, record });
    }

    // ---- pass 1: VERIFY the leads we sent but never confirmed ----
    for (const { key, record } of leads) {
        if (record.email_status !== "sent") continue;
        if (!record.resend_email_id) {
            counts.unconfirmed++;
            continue;
        }
        let event = null;
        try {
            event = await getDeliveryEvent(apiKey, record.resend_email_id);
        } catch (e) {
            console.error(`[CRON VERIFY] ${key} event read failed: ${e && e.message ? e.message : e}`);
            continue;
        }
        if (!event) {
            counts.unconfirmed++;
            continue;
        }
        const now = new Date().toISOString();
        if (DELIVERED_EVENTS.has(event.last_event)) {
            record.email_status = "delivered";
            record.delivered_at = now;
            record.resend_error = null;
            counts.verified++;
            console.log(`[CRON VERIFY] ${key} → delivered`);
        } else if (FAILED_EVENTS.has(event.last_event)) {
            record.email_status = "failed";
            record.resend_error = describeEvent(event);
            counts.failed++;
            console.error(`[CRON VERIFY] ${key} → ${event.last_event}: ${record.resend_error}`);
        } else {
            // queued / sent — still in flight.
            const ageH = (Date.now() - Date.parse(record.updated_at || record.received_at || 0)) / 3600000;
            if (ageH > SENT_STALE_HOURS) {
                counts.unconfirmed++;
                console.warn(`[CRON VERIFY] ${key} still "${event.last_event}" after ${ageH.toFixed(0)}h`);
            }
            continue;
        }
        record.updated_at = now;
        await kv.put(key, JSON.stringify(record), { expirationTtl: LEAD_TTL_SECONDS });
    }

    // ---- pass 2: RETRY the leads that really failed ----
    for (const { key, record } of leads) {
        if (record.email_status !== "failed") continue;

        // A suppressed recipient can never be delivered to — retrying it just
        // burns the retry budget and the sender reputation.
        const recipient = (record.to_address || toAddress).toLowerCase();
        if (suppressed.has(recipient)) {
            record.email_status = "abandoned";
            record.resend_error = `recipient ${recipient} is on the provider's suppression list`;
            record.updated_at = new Date().toISOString();
            await kv.put(key, JSON.stringify(record), { expirationTtl: LEAD_TTL_SECONDS });
            counts.abandoned++;
            console.error(`[CRON RETRY] ${key} → abandoned (suppressed recipient ${recipient})`);
            continue;
        }

        if ((record.retry_count || 0) >= MAX_RETRIES) {
            counts.abandoned++;
            // Mark abandoned if not already (idempotent re-runs).
            if (record.email_status !== "abandoned") {
                record.email_status = "abandoned";
                record.updated_at = new Date().toISOString();
                await kv.put(key, JSON.stringify(record), { expirationTtl: LEAD_TTL_SECONDS });
            }
            continue;
        }

        counts.retried++;
        const result = await tryResend(env, apiKey, record, toAddress);
        const now = new Date().toISOString();

        if (result.ok) {
            // Accepted, not proven delivered. The next run's verify pass turns
            // this into "delivered" once the provider confirms it.
            record.email_status = "sent";
            record.resend_status = result.resendStatus;
            record.resend_error = null;
            if (result.emailId) record.resend_email_id = result.emailId;
            record.to_address = toAddress;
            counts.succeeded++;
        } else {
            record.retry_count = (record.retry_count || 0) + 1;
            record.last_retry_at = now;
            record.resend_status = result.resendStatus || null;
            record.resend_error = result.resendError || null;
            if (record.retry_count >= MAX_RETRIES) {
                record.email_status = "abandoned";
                counts.abandoned++;
            }
            counts.failed++;
        }
        record.updated_at = now;
        await kv.put(key, JSON.stringify(record), { expirationTtl: LEAD_TTL_SECONDS });
    }

    const summary =
        `trigger=${trigger} scanned=${counts.scanned} verified=${counts.verified} ` +
        `retried=${counts.retried} accepted=${counts.succeeded} failed=${counts.failed} ` +
        `abandoned=${counts.abandoned} unconfirmed=${counts.unconfirmed} ` +
        `recipient=${toAddress} recipient_suppressed=${counts.recipient_suppressed}` +
        `${counts.truncated ? " (truncated, more exist)" : ""}`;
    console.log(`[CRON] ${summary}`);

    return { ok: true, ...counts, to_address: toAddress };
}

// Read the provider's suppression list. Returns a set of lower-cased
// addresses. An empty set on error — the caller must not treat "unknown" as
// "nothing is suppressed".
async function getSuppressedAddresses(apiKey) {
    const res = await fetch(`${RESEND_API}/suppressions`, {
        headers: { "Authorization": `Bearer ${apiKey}` },
    });
    if (!res.ok) throw new Error(`suppressions ${res.status}`);
    const body = await res.json();
    const data = Array.isArray(body) ? body : (body.data || []);
    return new Set(data.map((x) => String(x.email || "").toLowerCase()).filter(Boolean));
}

// Read one message's delivery event.
async function getDeliveryEvent(apiKey, emailId) {
    const res = await fetch(`${RESEND_API}/emails/${encodeURIComponent(emailId)}`, {
        headers: { "Authorization": `Bearer ${apiKey}` },
    });
    if (!res.ok) return null;
    const body = await res.json();
    if (!body || !body.last_event) return null;
    return body;
}

function describeEvent(event) {
    const diag = event.bounce && event.bounce.diagnosticCode
        ? (Array.isArray(event.bounce.diagnosticCode) ? event.bounce.diagnosticCode.join(" ") : event.bounce.diagnosticCode)
        : "";
    const msg = (event.bounce && event.bounce.message) || "";
    return [event.last_event, diag, msg].filter(Boolean).join(" — ").slice(0, 900);
}

async function tryResend(env, apiKey, record, toAddress) {
    const form = record.form || {};
    const attempt = (record.retry_count || 0) + 1;
    const subject = `[Retry ${attempt}/${MAX_RETRIES}] ${form.name || "—"} — ${form.service || "—"}`;

    // Minimal retry body — the original /api/quote sends a richly-formatted
    // HTML email, but we don't have FormData here (only the JSON record).
    // The operator only needs the lead details + context, so a plain text
    // body is enough. (If you want a fancier retry email, refactor
    // buildHtmlEmail / buildTextEmail in /api/quote.js into a shared helper.)
    const text = [
        `This is auto-retry #${attempt} of a previously failed /api/quote submission.`,
        ``,
        `Reference:   ${record.reference_id || "—"}`,
        `First seen:  ${record.received_at}`,
        `Last update: ${record.updated_at}`,
        `KV key:      lead:${record.received_at ? Date.parse(record.received_at) : "?"}:…`,
        ``,
        `--- Lead details ---`,
        `Name:     ${form.name || "—"}`,
        `Email:    ${form.email || "—"}`,
        `Country:  ${form.country || "—"}`,
        `Service:  ${form.service || "—"}`,
        `Date:     ${form.wedding_date || "—"}`,
        `Duration: ${form.video_duration || "—"}`,
        `Budget:   ${form.budget || "—"}`,
        `Referral: ${form.referral || "—"}`,
        form.upload_link ? `Upload:   ${form.upload_link}` : null,
        ``,
        `Project details:`,
        form.details || "(empty)",
    ].filter(Boolean).join("\n");

    try {
        const res = await fetch(`${RESEND_API}/emails`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${apiKey}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                from: FROM_ADDRESS,
                to: [toAddress],
                reply_to: form.email || undefined,
                subject,
                text,
            }),
        });
        const resText = await res.text();
        if (!res.ok) {
            return { ok: false, resendStatus: res.status, resendError: resText };
        }
        let emailId = null;
        try {
            const parsed = JSON.parse(resText);
            emailId = parsed && parsed.id ? parsed.id : null;
        } catch (e) { /* body was not JSON — still accepted */ }
        return { ok: true, resendStatus: res.status, emailId };
    } catch (e) {
        return { ok: false, resendStatus: 0, resendError: String(e && e.message ? e.message : e) };
    }
}

// 告警已移除（2026-10-12）：不再推送 Telegram / Slack / Discord。
// cron 结果写进 function 日志，操作员需要时手动 GET /api/dead-letters?token=&status=failed。
async function notifyCronResult(env, summary, counts) {
    // no-op
}
