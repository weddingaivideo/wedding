/**
 * Cloudflare Pages Function — /api/quote
 * Receives the order form POST, sends the inquiry to order@weddingai.video via Resend,
 * and redirects the user to the thank-you page.
 *
 * (2026-08-05 no-op redeploy to force Pages to pick up new DLQ_TOKEN env.)
 *
 * Lead storage model (2026-08-05): every submission is written to KV BEFORE
 * the email send. Email is just a notification; KV is the source of truth.
 * This way, Resend outages or misconfiguration can never drop a lead. The
 * prior model only wrote to KV on email failure, which meant the admin had
 * no fallback if Resend silently dropped a 2xx.
 *
 * Setup (one-time):
 *   1. Sign up at https://resend.com (free tier: 100 emails/day, 3000/month)
 *   2. Verify weddingai.video in Resend → Domains
 *   3. Add the DKIM records Resend gives you to your DNS
 *   4. Create an API key at https://resend.com/api-keys
 *   5. In Cloudflare Pages → Settings → Environment variables, add:
 *        RESEND_API_KEY = re_xxxxx
 *        TO_EMAIL       = order@weddingai.video  (optional, defaults below)
 *
 * Local test (creates .dev.vars in repo root with RESEND_API_KEY=re_xxx):
 *   npx wrangler pages dev . --port 8788
 *   then POST to http://localhost:8788/api/quote
 *
 * SECURITY:
 *   - RESEND_API_KEY MUST be set as a Cloudflare Pages secret. Do NOT
 *     hardcode the key in this file. Cloudflare Pages secrets are stored
 *     encrypted and never appear in the deployed bundle or in git.
 *   - If a key is ever committed to a public git repository, rotate it
 *     immediately at https://resend.com/api-keys — git history is forever.
 */

const TO_EMAIL_DEFAULT = "order@weddingai.video";
const FROM_ADDRESS = "WeddingAI Quote <noreply@weddingai.video>";
const SUCCESS_PATH = "/success";

const SERVICE_LABELS = {
    "slow-motion": "AI Slow Motion Enhancement",
    "vintage-restoration": "Vintage Footage Restoration",
    "family-tribute": "Family Tribute",
    "family-message": "Family Message",
    "celebrity-message": "Celebrity Message",
    "ai-video-generator": "AI Wedding Video Generator",
    "wedding-trailer": "Cinematic Wedding Trailer",
    "pet-wedding": "Pet Wedding Video",
    "multilingual": "Multilingual Dubbing & Subtitles",
    "cartoon-style": "Cartoon / Animated Style",
    "meme-generator": "Wedding GIFs & Memes",
    "other": "Other / Not Sure",
};

const COUNTRY_LABELS = {
    US: "United States", UK: "United Kingdom", CA: "Canada", AU: "Australia",
    DE: "Germany", FR: "France", ES: "Spain", IT: "Italy", IN: "India",
    CN: "China", JP: "Japan", other: "Other",
};

const BUDGET_LABELS = {
    "under-100": "Under $100", "100-300": "$100 – $300", "300-600": "$300 – $600",
    "600-plus": "$600+", "not-sure": "Not sure yet",
};

const VIDEO_DURATION_LABELS = {
    "under-1min": "Under 1 minute",
    "1-2min": "1 – 2 minutes",
    "2-3min": "2 – 3 minutes",
    "3-5min": "3 – 5 minutes",
    "5-10min": "5 – 10 minutes",
    "over-10min": "Over 10 minutes",
    "not-sure": "Not sure",
};

function label(map, key) {
    if (!key) return "—";
    return map[key] || key;
}

function escape(s) {
    if (s == null) return "";
    return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function buildHtmlEmail(d) {
    const name = escape(d.get("name"));
    const email = escape(d.get("email"));
    const country = label(COUNTRY_LABELS, d.get("country"));
    const weddingDate = escape(d.get("wedding_date") || "Not provided");
    const service = label(SERVICE_LABELS, d.get("service"));
    const videoDuration = label(VIDEO_DURATION_LABELS, d.get("video_duration"));
    const uploadLink = d.get("upload_link");
    const budget = label(BUDGET_LABELS, d.get("budget"));
    const details = escape(d.get("details"));
    const referral = escape(d.get("referral") || "Not provided");
    const referenceId = escape(d.get("reference_id") || "—");
    const submittedAt = new Date().toISOString();

    return `
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #2C2C2C; line-height: 1.6;">
    <h2 style="color: #D4AF37; margin: 0 0 20px;">New Quote Request</h2>
    <p style="color: #6B6B6B; font-size: 14px; margin: 0 0 8px;">Submitted at ${submittedAt}</p>
    <p style="background: #FDFBF8; border-left: 4px solid #D4AF37; padding: 10px 14px; margin: 0 0 24px; font-size: 14px;">
        <strong style="color: #2C2C2C;">Reference:</strong>
        <code style="font-family: 'SF Mono', monospace; font-size: 16px; color: #2C2C2C; letter-spacing: 0.05em;">${referenceId}</code>
    </p>

    <table cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; max-width: 640px;">
        <tr style="background: #F5F0EA;"><td style="font-weight: 600; width: 180px;">Name</td><td>${name}</td></tr>
        <tr><td style="font-weight: 600;">Email</td><td><a href="mailto:${email}" style="color: #D4AF37;">${email}</a></td></tr>
        <tr style="background: #F5F0EA;"><td style="font-weight: 600;">Country</td><td>${escape(country)}</td></tr>
        <tr><td style="font-weight: 600;">Wedding Date</td><td>${weddingDate}</td></tr>
        <tr style="background: #F5F0EA;"><td style="font-weight: 600;">Service</td><td>${escape(service)}</td></tr>
        <tr><td style="font-weight: 600;">Video Duration</td><td>${escape(videoDuration)}</td></tr>
        ${uploadLink ? `<tr style="background: #F5F0EA;"><td style="font-weight: 600;">Upload Link</td><td><a href="${escape(uploadLink)}" style="color: #D4AF37;">${escape(uploadLink)}</a></td></tr>` : ""}
        <tr><td style="font-weight: 600;">Budget</td><td>${escape(budget)}</td></tr>
        <tr style="background: #F5F0EA;"><td style="font-weight: 600;">Referral</td><td>${referral}</td></tr>
    </table>

    <h3 style="color: #2C2C2C; margin: 28px 0 10px;">Project Details</h3>
    <div style="background: #FDFBF8; border-left: 4px solid #D4AF37; padding: 14px 18px; white-space: pre-wrap;">${details}</div>

    <hr style="border: none; border-top: 1px solid #E5E0D8; margin: 28px 0;">
    <p style="color: #6B6B6B; font-size: 12px;">Reply directly to this email — your reply will go to <strong>${email}</strong>. Reference: <code>${referenceId}</code></p>
</body>
</html>`.trim();
}

function buildTextEmail(d) {
    const lines = [
        "New Quote Request — WeddingAI.video",
        "====================================",
        `Reference:   ${d.get("reference_id") || "—"}`,
        "",
        `Name:        ${d.get("name") || "—"}`,
        `Email:       ${d.get("email") || "—"}`,
        `Country:     ${label(COUNTRY_LABELS, d.get("country"))}`,
        `Wedding:     ${d.get("wedding_date") || "Not provided"}`,
        `Service:     ${label(SERVICE_LABELS, d.get("service"))}`,
        `Duration:    ${d.get("video_duration") || "Not provided"}`,
    ];
    if (d.get("upload_link")) lines.push(`Upload:      ${d.get("upload_link")}`);
    lines.push(`Budget:      ${label(BUDGET_LABELS, d.get("budget"))}`);
    lines.push(`Referral:    ${d.get("referral") || "Not provided"}`);
    lines.push("", "Project Details:", "----------------");
    lines.push(d.get("details") || "(empty)");
    lines.push("", `Submitted: ${new Date().toISOString()}`);
    return lines.join("\n");
}

// 简易 rate limit：单 IP 每 5 分钟最多 3 次（用 KV，避免滥用）
async function rateLimit(env, ip) {
    if (!env.RATE_LIMIT_KV) return { allowed: true };
    const key = `rl:${ip}`;
    const current = parseInt((await env.RATE_LIMIT_KV.get(key)) || "0", 10);
    if (current >= 3) return { allowed: false, retryAfter: 300 };
    await env.RATE_LIMIT_KV.put(key, String(current + 1), { expirationTtl: 300 });
    return { allowed: true };
}

// Lead store：每个提交都先写进 KV（status=pending），发邮件后再回填状态。
// 关键变化（2026-08-05）：原来是 Resend 失败才写（writeDeadLetter），现在无条件写。
// 这样 KV 是真相源，邮件只是通知。再也不会因为 Resend 抽风而丢单。
// Key 格式：lead:{timestamp}:{reference_id}
// TTL 90 天（7 776 000 秒）—— 够人工跟进，又不会无限堆积。
const LEAD_TTL_SECONDS = 60 * 60 * 24 * 90;

async function writeLead(env, formData, request) {
    const kv = env.RATE_LIMIT_KV || env.LEAD_STORAGE;
    if (!kv) return null;
    const refId = ((formData.get("reference_id") || "").toString().trim()) || null;
    const safeRef = (refId || "no-ref").replace(/[^A-Z0-9_-]/gi, "_");
    const key = `lead:${Date.now()}:${safeRef}`;
    const record = {
        reference_id: refId,
        email_status: "pending",   // → "delivered" 或 "failed"，由 updateLeadStatus 改写
        resend_status: null,
        resend_error: null,
        received_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        form: {
            name: formData.get("name") || null,
            email: formData.get("email") || null,
            country: formData.get("country") || null,
            wedding_date: formData.get("wedding_date") || null,
            service: formData.get("service") || null,
            video_duration: formData.get("video_duration") || null,
            upload_link: formData.get("upload_link") || null,
            budget: formData.get("budget") || null,
            details: formData.get("details") || null,
            referral: formData.get("referral") || null,
        },
        meta: {
            cf_ray: request.headers.get("CF-Ray") || null,
            cf_connecting_ip: request.headers.get("CF-Connecting-IP") || null,
            user_agent: request.headers.get("User-Agent") || null,
        },
    };
    try {
        await kv.put(key, JSON.stringify(record), { expirationTtl: LEAD_TTL_SECONDS });
        return key;
    } catch (e) {
        console.error(`[LEAD WRITE FAIL] ref=${refId || "—"} err=${e && e.message ? e.message : e}`);
        return null;
    }
}

async function updateLeadStatus(env, key, emailStatus, resendStatus, resendError) {
    if (!key) return;
    const kv = env.RATE_LIMIT_KV || env.LEAD_STORAGE;
    if (!kv) return;
    try {
        const existing = await kv.get(key, { type: "json" });
        if (!existing) {
            console.error(`[LEAD UPDATE FAIL] key=${key} not found (TTL expired or KV evicted?)`);
            return;
        }
        existing.email_status = emailStatus;
        existing.resend_status = resendStatus;
        existing.resend_error = resendError;
        existing.updated_at = new Date().toISOString();
        await kv.put(key, JSON.stringify(existing), { expirationTtl: LEAD_TTL_SECONDS });
    } catch (e) {
        console.error(`[LEAD UPDATE FAIL] key=${key} err=${e && e.message ? e.message : e}`);
    }
}

// 失败告警：Telegram（首选，手机 push 即时）+ Slack/Discord webhook（保留兼容）。
// fire-and-forget：告警自身失败不影响主流程，也不延迟用户响应。
// 配置：
//   TELEGRAM_BOT_TOKEN  — 找 @BotFather 创建机器人拿到
//   TELEGRAM_CHAT_ID    — 给机器人发条消息后访问
//                         https://api.telegram.org/bot<TOKEN>/getUpdates 拿到
//   ALERT_WEBHOOK_URL   — Slack/Discord incoming webhook URL（可选，向后兼容）
async function alertAdmin(env, failLog, ctx) {
    const safe = (v) => (v == null ? "—" : String(v).slice(0, 200));
    // Telegram
    if (env.TELEGRAM_BOT_TOKEN && env.TELEGRAM_CHAT_ID) {
        const text = [
            "🚨 WeddingAI 新死信",
            `ref:     ${safe(ctx && ctx.ref)}`,
            `姓名:   ${safe(ctx && ctx.name)}`,
            `邮箱:   ${safe(ctx && ctx.email)}`,
            `国家:   ${safe(ctx && ctx.country)}`,
            `服务:   ${safe(ctx && ctx.service)}`,
            `错误:   ${safe(failLog)}`,
        ].join("\n");
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
    // Slack / Discord webhook
    if (env.ALERT_WEBHOOK_URL) {
        try {
            await fetch(env.ALERT_WEBHOOK_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    text: failLog,
                    attachments: [{
                        color: "danger",
                        text: failLog,
                        ts: Math.floor(Date.now() / 1000),
                    }],
                }),
            }).catch(() => null);
        } catch (_) { /* never block on alert */ }
    }
}

function leadCtx(formData, refId) {
    return {
        ref: refId || null,
        name: formData.get("name") || null,
        email: formData.get("email") || null,
        country: formData.get("country") || null,
        service: formData.get("service") || null,
    };
}

export async function onRequestPost({ request, env }) {
    const reqUrl = new URL(request.url);
    const origin_base = `${reqUrl.protocol}//${reqUrl.host}`;

    // CSRF defense: only accept same-origin POSTs. Browsers automatically
    // send Origin on cross-origin form POSTs and on all fetch/XHR; legitimate
    // form submissions from weddingai.video (including sub-pages) carry
    // Origin: https://weddingai.video. CLI tools / server-to-server calls
    // also send Origin when configured correctly. Bots that omit Origin
    // fall through to the Allow-Origin list below.
    const origin = request.headers.get("Origin") || request.headers.get("Referer") || "";
    if (origin && !origin.startsWith(origin_base)) {
        return new Response("Forbidden: cross-origin request blocked", { status: 403 });
    }

    let formData;
    try {
        formData = await request.formData();
    } catch (e) {
        return new Response("Invalid form data", { status: 400 });
    }

    // Honeypot: 隐藏字段被填了就静默丢弃（假装成功）
    if (formData.get("botcheck")) {
        return redirect303(origin_base, "/success");
    }

    // 必填校验
    // (budget added 2026-07-28 — was previously optional on the server even
    // though the form marks it required. This let leads through with budget
    // = null and forced the operator to ask in the reply email.)
    const required = ["name", "email", "country", "service", "budget", "details"];
    for (const key of required) {
        if (!formData.get(key) || !String(formData.get(key)).trim()) {
            return new Response(`Missing field: ${key}`, { status: 400 });
        }
    }

    // Email 格式
    const email = String(formData.get("email"));
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        return new Response("Invalid email", { status: 400 });
    }

    // Country / service / budget must be from the known label sets
    // (defense against bots that submit junk values; cheap to check).
    const country = String(formData.get("country") || "");
    if (country && !(country in COUNTRY_LABELS)) {
        return new Response(`Invalid country: ${country}`, { status: 400 });
    }
    const service = String(formData.get("service") || "");
    if (service && !(service in SERVICE_LABELS)) {
        return new Response(`Invalid service: ${service}`, { status: 400 });
    }
    const budget = String(formData.get("budget") || "");
    if (budget && !(budget in BUDGET_LABELS)) {
        return new Response(`Invalid budget: ${budget}`, { status: 400 });
    }

    // Rate limit
    const ip = request.headers.get("CF-Connecting-IP") || "unknown";
    const rl = await rateLimit(env, ip);
    if (!rl.allowed) {
        return new Response("Too many requests. Please try again later.", {
            status: 429,
            headers: { "Retry-After": String(rl.retryAfter || 300) },
        });
    }

    // 客户端已经生成了 reference_id；这里取出来给 success page 用
    const refId = (formData.get("reference_id") || "").toString().trim();
    const successUrl = (status) => {
        const u = new URL(SUCCESS_PATH, origin_base);
        if (refId) u.searchParams.set("id", refId);
        if (status) u.searchParams.set("status", status);
        return u.toString();
    };

    // 先存后发：把 lead 写进 KV（status=pending），再尝试发邮件。
    // 这样即使 Resend 抽风、API key 缺失、或 function 中途抛异常，lead 也不会丢。
    // 后面 updateLeadStatus 会把这条记录改成 "delivered" 或 "failed"。
    const leadKey = await writeLead(env, formData, request);
    if (leadKey) {
        console.log(`[LEAD STORED] ref=${refId || "—"} key=${leadKey}`);
    } else {
        console.warn(`[LEAD STORE FAILED] ref=${refId || "—"} KV write failed; lead will only live in email if it gets through`);
    }

    const apiKey = (env.RESEND_API_KEY || "").replace(/^\ufeff+/, "").trim();
    if (!apiKey) {
        // Misconfiguration: lead is already safe in KV, but email can't go out.
        // Mark this lead failed + alert the operator (push) so they fix the secret.
        const failLog = `[QUOTE FAIL] ref=${refId || "—"} reason=missing_api_key name=${formData.get("name")} email=${formData.get("email")} ` +
            "Configure RESEND_API_KEY in Cloudflare Pages → Settings → Environment variables.";
        console.error(failLog);
        await updateLeadStatus(env, leadKey, "failed", 0, "missing_api_key");
        await alertAdmin(env, failLog, leadCtx(formData, refId));
        return new Response(
            "Server is not configured to send email. Please email order@weddingai.video directly.",
            {
                status: 500,
                headers: { "Content-Type": "text/plain; charset=utf-8" },
            }
        );
    }

    const subject = `New quote: ${formData.get("name")} — ${label(SERVICE_LABELS, formData.get("service"))}`;

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
                reply_to: email,
                subject,
                html: buildHtmlEmail(formData),
                text: buildTextEmail(formData),
            }),
        });

        if (!res.ok) {
            const errBody = await res.text();
            // 详细日志：包含 reference_id + 关键字段 + Resend 错误体
            // 失败时不再 silent redirect —— 用户会看到 status=pending 的提示页
            const failLog = `[QUOTE FAIL] ref=${refId || "—"} resend_status=${res.status} name=${formData.get("name")} email=${formData.get("email")} country=${formData.get("country")} service=${formData.get("service")} body=${errBody}`;
            console.error(failLog);
            if (res.status === 401) {
                console.error("HINT: Resend returned 401. The API key is invalid or has been rotated. Check Cloudflare Pages secret RESEND_API_KEY.");
            } else if (res.status === 400) {
                console.error("HINT: Resend returned 400. Most common cause: API key is invalid/revoked. Re-create the key at https://resend.com/api-keys and update Cloudflare Pages secret RESEND_API_KEY.");
            } else if (res.status === 403) {
                console.error("HINT: Resend returned 403. The 'from' domain (weddingai.video) is likely NOT verified, OR the 'from' address is not allowed. Add it at https://resend.com/domains and add the DNS records (DKIM/SPF).");
            } else if (res.status === 422) {
                console.error("HINT: Resend returned 422. Validation error (e.g. malformed address). Body above.");
            } else if (res.status === 429) {
                console.error("HINT: Resend returned 429. Free tier rate limit reached (100/day or 3000/month). Wait or upgrade.");
            }
            // Lead 已经在前面 writeLead 时存进去了（status=pending）。
            // 这里把状态翻成 "failed" 并记录 Resend 错误码 + 错误体。
            await updateLeadStatus(env, leadKey, "failed", res.status, errBody);
            console.log(`[LEAD STATUS] ref=${refId || "—"} key=${leadKey || "—"} → failed (resend_status=${res.status})`);
            // 主动告警：Telegram（手机 push）+ Slack/Discord webhook（向后兼容）
            await alertAdmin(env, failLog, leadCtx(formData, refId));
            // Redirect with status=pending so the success page can warn the user
            return redirect303(origin_base, successUrl("pending"));
        }

        // Email sent successfully — flip the lead to "delivered"
        await updateLeadStatus(env, leadKey, "delivered", res.status, null);
        console.log(`[QUOTE OK] ref=${refId || "—"} name=${formData.get("name")} email=${formData.get("email")} country=${formData.get("country")} service=${formData.get("service")} lead=${leadKey || "—"}`);
        return redirect303(origin_base, successUrl(null));
    } catch (e) {
        // 网络层失败（fetch throw）——告诉用户 + 保留 lead + 告警
        const errMsg = String(e && e.message ? e.message : e);
        const failLog = `[QUOTE FAIL] ref=${refId || "—"} reason=exception name=${formData.get("name")} email=${formData.get("email")} err=${errMsg}`;
        console.error(failLog);
        await updateLeadStatus(env, leadKey, "failed", 0, errMsg);
        console.log(`[LEAD STATUS] ref=${refId || "—"} key=${leadKey || "—"} → failed (resend_status=0 / network)`);
        await alertAdmin(env, failLog, leadCtx(formData, refId));
        return redirect303(origin_base, successUrl("pending"));
    }
}

function redirect303(origin_base, location) {
    // 绝对 URL 或相对 URL 都支持
    const target = location.startsWith("http") ? location : new URL(location, origin_base).toString();
    return new Response(null, { status: 303, headers: { Location: target } });
}

// 其他 HTTP 方法 → 405
export async function onRequest({ request }) {
    if (request.method !== "POST") {
        return new Response("Method Not Allowed", {
            status: 405,
            headers: { Allow: "POST" },
        });
    }
}
