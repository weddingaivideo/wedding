# weddingai.video

AI-powered wedding video services for couples worldwide. Static site with
Cloudflare Pages hosting, a serverless Functions backend (lead capture, email,
rate limiting), and a middleware-based 10-language i18n layer.

**Production**: https://weddingai.video

---

## What this site does

11 service offerings, each with its own landing page, gallery example, and
i18n strings:

| Category | Service |
|---|---|
| Video Enhancement | Slow Motion, Vintage Restoration |
| Personalization | Wedding Trailer, AI Video Generator, Pet Wedding, Multilingual, Cartoon Style, Wedding Memes |
| Absence Compensation | Family Tribute, Family Message, Celebrity Message |

Plus a portfolio (gallery), blog (10 languages, ~50 articles each), pricing,
order form, about, and resources.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Cloudflare Pages (weddingai-video project)                  │
│  ┌────────────────────────┐  ┌──────────────────────────┐   │
│  │  Static assets          │  │  Functions (serverless)  │   │
│  │  /index.html, /gallery, │  │  /api/quote              │   │
│  │  /blog/{lang}/*,        │  │  /api/contact            │   │
│  │  /services/*,           │  │  /scheduled              │   │
│  │  /images/, /js/,        │  │  /__csp_report           │   │
│  │  /styles/               │  │                          │   │
│  └────────────────────────┘  └──────────────────────────┘   │
│                ▲                       ▲                     │
│                │  functions/_middleware.js                    │
│                │  (i18n rewrite, CSP nonce, …)                │
└────────────────┼──────────────────────────────────────────────┘
                 │
   ┌─────────────┴─────────────┐
   │  Cloudflare KV            │  Rate-limit + dead-letter queue
   │  (LEAD_STORAGE)           │
   └───────────────────────────┘
```

### Key moving parts

- **`functions/_middleware.js`** — runs on every request. Detects lang from
  `Accept-Language` header or `?lang=` param, rewrites to `/<lang>/...` paths
  (or `/` for EN), injects per-request CSP nonce, and runs `applyDataI18n` to
  swap `<... data-i18n="key">` attributes with translated text fetched from
  the JSON dicts.
- **`i18n/{en,zh,es,fr,de,pt,ja,ru,ar,th}.json`** — translation dicts. Each
  has flat dot-separated keys (`pricing.cards.completes.name`,
  `404.a_text.gallery`).
- **`js/i18n.js`** — client-side i18n fallback. Loaded with `?v=N.N` cache
  bust. The `I18N_VERSION` constant in this file must match the
  `?v=N.N` query string in every HTML file.
- **`functions/api/quote.js`** — lead-capture form. Validates, rate-limits
  via KV, persists to KV, sends email via Resend.
- **`_headers`** — per-extension cache-control, security headers, and the
  MIME type overrides for `.mp4` / `.webm`.

---

## Local development

```bash
# 1. Install wrangler if you haven't already
npm install -g wrangler

# 2. Authenticate with Cloudflare
wrangler login

# 3. Run locally
wrangler pages dev .
# → http://localhost:8788 (note: not the same as `python -m http.server`)
```

`wrangler pages dev` is required (not just a static server) because the i18n
middleware lives in `functions/_middleware.js`. A bare `python -m http.server`
will serve the source HTML directly without rewriting paths, so `/zh/about/`
won't work and `data-i18n` attributes stay in the source language.

> **Note on i18n in local dev**: the middleware fetches
> `https://weddingai.video/i18n/{lang}.json` (production URL hard-coded in
> `_middleware.js`), not the local files. This means local dev always shows
> the **live** translations, not whatever is on your branch. To validate new
> translations before deploy, write a small Python script that mirrors the
> `applyDataI18n` regex against your local source + local i18n JSON.

---

## Cache-bust pattern

Every HTML page references CSS, JS, and i18n with a `?v=N.N` query string
(example: `/js/i18n.js?v=4.27`). The project uses a single monotonically
increasing version number for all assets:

- **`js/i18n.js`** — bump `I18N_VERSION` constant.
- **535 HTML files** — update `<script src="/js/i18n.js?v=N.N">` and
  `<link rel="stylesheet" href="/styles.min.css?v=N.N">` to match.
- **New media** — for video / image swaps, use `?v=YYYY-MM-DD` or bump the
  same `N.N` counter.

The Cloudflare CDN cache for static assets defaults to 4 hours (HTML is 1
minute). The `?v=N.N` query ensures visitors see the new version immediately
on the next deploy.

---

## Project structure

```
.
├── index.html              ← EN canonical homepage
├── {about,blog,gallery,…}/ ← EN canonical content directories
├── ar/, de/, es/, fr/, ja/, pt/, ru/, th/, zh/  ← localized homepages
│   └── blog/{slug}/        ← localized blog posts
├── functions/
│   ├── _middleware.js      ← i18n rewrite + CSP nonce injection
│   ├── api/quote.js        ← lead-capture form handler
│   ├── api/contact.js      ← contact form handler
│   ├── scheduled.js        ← daily cron (09:00 UTC)
│   └── __csp_report.js     ← CSP violation receiver
├── i18n/                   ← 10 language JSON dicts (en/zh/es/fr/de/pt/ja/ru/ar/th)
├── js/                     ← main.min.js, lazy-videos.js, i18n.js, langs.js
├── styles/                 ← styles.min.css, i18n.css
├── images/                 ← static images + videos
├── scripts/                ← build/QA/fix scripts (canonical, not one-offs)
├── tools/                  ← ad-hoc utility scripts
├── private/                ← internal docs (e.g. architecture overview)
├── _headers                ← Cloudflare Pages headers (cache, security, MIME) — LF
├── _redirects              ← Cloudflare Pages redirects — LF
└── AGENTS.md               ← agent-facing project notes
```

---

## Deploy

Production deploys happen automatically on push to `main`. The Cloudflare
Pages project `weddingai-video` is connected to the GitHub repo (private).

```bash
git push origin main        # → production deploy (weddingai.video)
git push origin dev         # → preview deploy (<branch>.weddingai-video.pages.dev)
```

For ad-hoc deploys (without going through Git):

```bash
wrangler pages deploy . --project-name weddingai-video --commit-dirty=true
```

**Important**: after the first Git-based deploy, the `wrangler pages deploy`
direct-upload path becomes a no-op. Use `git push` for everything.

---

## Adding a new translation key

1. Add the key to **`i18n/en.json`** (the canonical source). Format:
   `"section.element_text.short_slug.unique6chars": "English value"`
2. Add the same key with translated values to all 9 other language files
   (`zh`, `es`, `fr`, `de`, `pt`, `ja`, `ru`, `ar`, `th`).
3. Reference in HTML: `<span data-i18n="section.element_text.short_slug.unique6chars">English fallback</span>`.
4. Run `qa/full_qa.py` to verify the key exists in all languages and the
   HTML references resolve.
5. Bump `I18N_VERSION` in `js/i18n.js` and update the `?v=N.N` query string
   in all 535 HTML files.

---

## Adding a new language

1. Add `i18n/<lang>.json` with the same key set as `i18n/en.json`.
2. Add `<option value="<lang>">CODE</option>` to the language switcher
   in the nav (search for `wa-lang-switcher`).
3. Add the lang to:
   - The `<link rel="alternate" hreflang="<lang>">` block in `index.html`
     (and every page that has them).
   - The `lang` code list in `functions/_middleware.js`.
   - `sitemap-<lang>.xml` and a reference in `sitemap.xml`.
4. Translate the content under `<lang>/` directory (copy `en/`, translate).
5. Run `qa/full_qa.py` to validate.

---

## QA

`qa/full_qa.py` is the canonical linter. It runs the same checks the
project owner uses before each deploy:

- All `data-i18n` keys exist in all 10 language files
- No malformed i18n keys
- HTML tag balance (every `<div>` has a matching `</div>`)
- Internal link integrity (no broken local hrefs)
- And more (run with `--help` for the full list)

Ad-hoc one-off fix scripts from past projects live under `qa/_*.py` and
`scripts/archive/`. Don't run them on a fresh checkout — they're for one-time
historical fixes.

---

## Tech stack

- **Frontend**: vanilla HTML / CSS / JS (no framework, no build step)
- **Images**: hand-tuned `<picture>` elements with AVIF + WebP + JPEG
- **Video**: native `<video>` with deferred loading via `js/lazy-videos.js`
- **i18n**: server-side via `functions/_middleware.js`, client-side via
  `js/i18n.js` (fallback for static assets)
- **Hosting**: Cloudflare Pages (static + Functions)
- **Forms**: Cloudflare Functions + Cloudflare KV (rate-limit, lead capture) +
  Resend (transactional email)
- **Analytics**: Google Analytics 4 (lazy-loaded on interaction)
- **Search console**: Ahrefs + Bing Webmaster + IndexNow
