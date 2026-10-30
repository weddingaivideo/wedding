/**
 * Cloudflare Pages Function — /api/dead-letters
 * List / read lead records from KV. Every /api/quote submission lands here
 * (status "pending" → "delivered" | "failed") so the operator can audit what
 * came in even when Resend drops a send. Originally this only stored the
 * failures (prefix "dl:"); since 2026-08-05 it lists all leads (prefix
 * "lead:"). The endpoint name / URL stays the same for backward compat.
 *
 * Auth: requires `?token=XXX` matching env.DLQ_TOKEN.
 * If DLQ_TOKEN is not set, the endpoint returns 404 (disabled).
 *
 * Endpoints:
 *   GET /api/dead-letters?token=XXX                    → list keys (newest first), max 100
 *   GET /api/dead-letters?token=XXX&key=lead:ts:ref   → read one entry's JSON
 *   GET /api/dead-letters?token=XXX&delete=lead:ts:ref → delete one entry
 *
 * Filtering: append `&status=pending|failed|delivered` to filter the list
 * to a particular delivery status. Without a filter, all leads are returned
 * (most recent first).
 */

const PAGE_SIZE = 100;

// Rate limit: per-IP, 10 requests per 5 minutes. Admin endpoint is meant to
// be hit manually by the operator, not programmatically — a tighter limit
// than /api/quote because token brute-force is the primary threat model.
// (Added 2026-07-28 after /admin/leads/ URL was found publicly accessible.)
async function rateLimit(env, ip) {
    if (!env.RATE_LIMIT_KV) return { allowed: true };
    const key = `rl:dlq:${ip}`;
    const current = parseInt((await env.RATE_LIMIT_KV.get(key)) || "0", 10);
    if (current >= 10) return { allowed: false, retryAfter: 300 };
    await env.RATE_LIMIT_KV.put(key, String(current + 1), { expirationTtl: 300 });
    return { allowed: true };
}

function clientIp(request) {
    return (
        request.headers.get("CF-Connecting-IP") ||
        request.headers.get("X-Forwarded-For")?.split(",")[0].trim() ||
        "unknown"
    );
}

export async function onRequestGet({ request, env }) {
    const expected = (env.DLQ_TOKEN || "").replace(/^\ufeff+/, "").trim();
    if (!expected) {
        return new Response("Not Found", { status: 404 });
    }
    const url = new URL(request.url);
    const provided = url.searchParams.get("token") || "";
    if (provided !== expected) {
        return new Response("Forbidden", { status: 403 });
    }

    // Token OK — apply per-IP rate limit (defense in depth against
    // compromised-token scenarios and accidental client loops).
    const rl = await rateLimit(env, clientIp(request));
    if (!rl.allowed) {
        return new Response("Too Many Requests", {
            status: 429,
            headers: { "Retry-After": String(rl.retryAfter) },
        });
    }

    const kv = env.RATE_LIMIT_KV || env.LEAD_STORAGE;
    if (!kv) {
        return new Response("KV not bound", { status: 503 });
    }

    const single = url.searchParams.get("key");
    if (single) {
        if (!/^lead:\d+:[A-Za-z0-9_-]+$/.test(single)) {
            return new Response("Invalid key", { status: 400 });
        }
        if (url.searchParams.has("delete")) {
            await kv.delete(single);
            return new Response(JSON.stringify({ deleted: single }), {
                status: 200, headers: { "Content-Type": "application/json" },
            });
        }
        const v = await kv.get(single, { type: "json" });
        if (!v) return new Response("Not found", { status: 404 });
        return new Response(JSON.stringify(v, null, 2), {
            status: 200, headers: { "Content-Type": "application/json" },
        });
    }

    // List mode: paginate by listing keys with prefix `lead:`
    const list = await kv.list({ prefix: "lead:", limit: PAGE_SIZE });
    const statusFilter = url.searchParams.get("status");
    const itemsRaw = list.keys
        .map((k) => ({ key: k.name, expiration: k.expiration || null }))
        .sort((a, b) => (a.key < b.key ? 1 : -1)); // newest first (timestamp is in key)

    // If status filter is set, hydrate each key so we can filter by email_status.
    // Cost: 1 KV read per item, max 100 reads per request — fine for an admin
    // tool that's manually hit by the operator.
    if (statusFilter) {
        // "sent" = the provider accepted the request but its delivery event has
        // not been confirmed yet (2026-10-29). It is deliberately NOT called
        // "delivered": a 2xx on the send request only means "accepted".
        const allowed = new Set(["pending", "sent", "delivered", "failed", "abandoned"]);
        if (!allowed.has(statusFilter)) {
            return new Response(`Invalid status filter: ${statusFilter} (allowed: pending, sent, delivered, failed, abandoned)`, { status: 400 });
        }
        const hydrated = await Promise.all(
            itemsRaw.map(async (it) => {
                const v = await kv.get(it.key, { type: "json" });
                return { ...it, email_status: v ? v.email_status : null };
            })
        );
        const filtered = hydrated.filter((it) => it.email_status === statusFilter);
        return new Response(
            JSON.stringify(
                {
                    count: filtered.length,
                    truncated: list.list_complete === false,
                    status: statusFilter,
                    items: filtered,
                },
                null,
                2
            ),
            { status: 200, headers: { "Content-Type": "application/json" } }
        );
    }

    return new Response(
        JSON.stringify(
            {
                count: itemsRaw.length,
                truncated: list.list_complete === false,
                items: itemsRaw,
            },
            null,
            2
        ),
        { status: 200, headers: { "Content-Type": "application/json" } }
    );
}
