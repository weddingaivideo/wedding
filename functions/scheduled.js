/**
 * Cloudflare Pages Cron Trigger — /scheduled
 * Runs daily at 9am UTC (configured in the Cloudflare dashboard under
 * Pages → weddingai-video → Settings → Functions → Cron Triggers).
 * NOTE: wrangler.toml does NOT configure cron triggers (Pages wrangler.toml
 * doesn't support [[triggers]]); the schedule is set in the dashboard only.
 *
 * Purpose: re-send any /api/quote submission whose Resend email failed, so a
 * temporary email-service outage doesn't lose leads. Up to 5 retries per lead;
 * after that, marked "abandoned" and the operator is paged to handle manually.
 *
 *   pending    → fresh submission, email not yet attempted
 *   delivered  → Resend returned 2xx (either first try or a retry)
 *   failed     → Resend returned non-2xx OR threw; retried up to 5 times
 *   abandoned  → 5+ retries all failed; kept in KV for 90 days for audit
 *
 * Manual test (any time):
 *   curl -H "Authorization: Bearer ${CRON_TOKEN}" \
 *        https://weddingai.video/scheduled
 *
 * (The HTTP entry point is gated by CRON_TOKEN. The cron entry point is
 *  internal — only Cloudflare can invoke it.)
 *
 * Notifications: reuses the same TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID /
 * ALERT_WEBHOOK_URL env vars as /api/quote, so setup is one-shot.
 */

const FROM_ADDRESS = "WeddingAI Quote <noreply@weddingai.video>";
const TO_EMAIL_DEFAULT = "order@weddingai.video";
const MAX_RETRIES = 5;
const LEAD_TTL_SECONDS = 60 * 60 * 24 * 90;
const KV_LIST_LIMIT = 100; // per-run cap; paginate if we ever exceed this

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

async function retryFailedLeads(env, { trigger }) {
    const kv = env.RATE_LIMIT_KV || env.LEAD_STORAGE;
    if (!kv) {
        console.error("[CRON RETRY] no KV bound, aborting");
        return { ok: false, reason: "no_kv" };
    }
    const apiKey = (env.RESEND_API_KEY || "").replace(/^\ufeff+/, "").trim();
    if (!apiKey) {
        console.error("[CRON RETRY] RESEND_API_KEY missing, aborting");
        return { ok: false, reason: "missing_api_key" };
    }

    const list = await kv.list({ prefix: "lead:", limit: KV_LIST_LIMIT });
    const counts = {
        scanned: list.keys.length,
        truncated: list.list_complete === false,
        retried: 0,
        succeeded: 0,
        failed: 0,
        abandoned: 0,
    };

    for (const key of list.keys) {
        const record = await kv.get(key.name, { type: "json" });
        if (!record) continue;
        if (record.email_status !== "failed") continue;
        if ((record.retry_count || 0) >= MAX_RETRIES) {
            counts.abandoned++;
            // Mark abandoned if not already (idempotent re-runs).
            if (record.email_status !== "abandoned") {
                record.email_status = "abandoned";
                record.updated_at = new Date().toISOString();
                await kv.put(key.name, JSON.stringify(record), { expirationTtl: LEAD_TTL_SECONDS });
            }
            continue;
        }

        counts.retried++;
        const result = await tryResend(env, apiKey, record);
        const now = new Date().toISOString();

        if (result.ok) {
            record.email_status = "delivered";
            record.resend_status = result.resendStatus;
            record.resend_error = null;
            record.delivered_at = now;
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
        await kv.put(key.name, JSON.stringify(record), { expirationTtl: LEAD_TTL_SECONDS });
    }

    const summary = `trigger=${trigger} scanned=${counts.scanned} retried=${counts.retried} succeeded=${counts.succeeded} failed=${counts.failed} abandoned=${counts.abandoned}${counts.truncated ? " (truncated, more exist)" : ""}`;
    console.log(`[CRON RETRY] ${summary}`);

    // Only ping the operator when something actually happened — don't spam
    // "nothing to do" every day.
    if (counts.retried > 0 || counts.abandoned > 0) {
        await notifyCronResult(env, summary, counts);
    }

    return { ok: true, ...counts };
}

async function tryResend(env, apiKey, record) {
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
        const res = await fetch("https://api.resend.com/emails", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${apiKey}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                from: FROM_ADDRESS,
                to: [env.TO_EMAIL || TO_EMAIL_DEFAULT],
                reply_to: form.email || undefined,
                subject,
                text,
            }),
        });
        if (!res.ok) {
            return { ok: false, resendStatus: res.status, resendError: await res.text() };
        }
        return { ok: true, resendStatus: res.status };
    } catch (e) {
        return { ok: false, resendStatus: 0, resendError: String(e && e.message ? e.message : e) };
    }
}

async function notifyCronResult(env, summary, counts) {
    // Telegram
    if (env.TELEGRAM_BOT_TOKEN && env.TELEGRAM_CHAT_ID) {
        const lines = ["⏰ WeddingAI 死信重试报告", summary];
        if (counts.succeeded > 0) lines.push(`✅ 自动恢复: ${counts.succeeded}`);
        if (counts.failed > 0) lines.push(`❌ 仍失败: ${counts.failed}`);
        if (counts.abandoned > 0) lines.push(`🚫 已放弃 (≥${MAX_RETRIES} 次): ${counts.abandoned}`);
        if (counts.truncated) lines.push(`⚠️ 列表被截断 (>${KV_LIST_LIMIT} 条)，可能还有未处理的`);
        const text = lines.join("\n");
        try {
            await fetch(
                `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text }),
                }
            ).catch(() => null);
        } catch (_) { /* never block on alert */ }
    }
    // Slack/Discord webhook
    if (env.ALERT_WEBHOOK_URL) {
        try {
            await fetch(env.ALERT_WEBHOOK_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: `⏰ WeddingAI cron retry: ${summary}` }),
            }).catch(() => null);
        } catch (_) { /* never block on alert */ }
    }
}
