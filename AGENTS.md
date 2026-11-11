# WeddingAI.video — Agent Notes

Architecture facts that affect SEO audits, performance work, and deploys.

## Middleware-translated pages have NO backing .html

The following URL patterns are served **at runtime** by
`functions/_middleware.js` translating content from `i18n/<lang>.json`:

- `/<lang>/` (e.g. `/de/`, `/zh/`) — home for any of 11 langs
- `/<lang>/pricing/`
- (any other top-level page where the lang dir has no `index.html`)

Their meta_description / og_description / twitter_description all
come from JSON keys like `index.meta_description.*` or
`pricing.meta_description`. The corresponding **`<lang>/index.html`
files do not exist** — verified 2026-10-19 (`de/`, `ar/`, etc. have
no `index.html`; only `de/blog/.../index.html` and `de/tools/.../index.html`).

### Audit checklist (must scan both sources)

For any meta_description / title / H1 length audit, scan:

1. All `*.html` files (handles most blog, tools, services sub-pages)
2. **All `i18n/*.json` files** — look for keys matching:
   - `<page>.meta_description` (top-level pages)
   - `<page>.meta_description.<hash>` (the i18n-key-hash pattern)
   - `<page>.og_description`, `<page>.twitter_description`

When auditing, probe at least one `/<lang>/` URL live to confirm
whether the middleware is in play (404 on `/de/index.html` direct
file access, but 200 on `/de/` URL — confirms middleware-only path).

### Why this matters

Caught 2026-10-19: 8 meta_description entries >155 chars in
`i18n/*.json` that a static-HTML-only scanner missed entirely.
Affected: `index.meta_description` in de/hi (156, 160 chars) +
`pricing.meta_description` in de/es/fr/hi/pt/th (167-188 chars).
All fixed in commit `f91b20ef`.

## A localized URL without a localized twin falls back to the ENGLISH file

The middleware probes `/<lang><rest>` first and only falls back to
`/rest` (the English source) when that probe 404s. A 404 does not mean
the language is missing — it means **that one page** has no pre-translated
twin. Measured 2026-10-24: 140 English pages, but only 63 localized pages
per language, so ~77 English pages per language are served from the English
source (`ru` has only 13 localized pages in total).

Consequences for any audit:

- The page BODY is translated at runtime (the `data-i18n` bindings are
  resolved from `i18n/<lang>.json`), so the text is fine **only if the
  dictionary has the key**. `ru` has ~36k blog keys missing, so its blog
  pages render the English body with a translated navigation.
- The `og:` / `twitter:` tags are NOT bound to the dictionary, so on such
  a page they stay English unless the middleware rewrites them.
- A localized page that IS backed by a static file keeps its own
  hand-written og:title — 139 of the 140 English pages deliberately use a
  different headline for the card than for the `<title>` (the `<title>`
  targets one search intent, the card another). Do not "normalise" a card
  to the `<title>`; the middleware only replaces it when the page's own
  title was actually translated.

Audit rule: a page is localized only if `<lang>/<rest>/index.html` exists.
A file-count comparison across the language folders is the fastest way to
see how much of the site is actually translated.

## The 13 wedding photo tools are FREE — no price may appear on a tool page

All tools are client-side browser utilities. None of them charges the user,
so a price on a tool page contradicts the product claim. Established
2026-10-23 (commit `f66ee5f3`).

### Scope

- **No price** on: `tools/<slug>/index.html`, `<lang>/tools/<slug>/index.html`,
  the hub `tools/index.html` (+ the middleware-rendered `/<lang>/tools/`),
  and the homepage's **tool list** section.
- **Prices stay** on the paid AI-wedding-video product: `/pricing/`,
  `/order/`, the homepage's "By the Numbers" table (incl. the
  `AggregateOffer` `lowPrice: 9.90`), and the
  `index.p_text.based_on_9_400_*` market-average paragraph. Those are real,
  purchasable products.
- "free" is NOT a price — "13 Free Wedding Photo Tools", "100% free",
  "Try free →" are the product promise and must survive any price sweep.

### TRAP: the couple count is 500+, but the KEYS still say 9_400

Since 2026-10-24 (commit `5720fbcc`) the site claims **500+ couples** and
**500+ customer reviews**, not "9,400+". The old figures had no external
source, while the published Goodfirms and ReviewNexa listings both say
"500+ couples, 4.9/5". The same pass removed "since 2023" everywhere - the
domain was registered 2026-03-17.

The **key names were left untouched** (`pricing.td_text.9_400_couples_served_*`,
`index.p_text.based_on_9_400_*`, `index.td_text.9_400_verified_reviews.*`,
`gallery.h2_text.gallery_by_the_numbers_9_400_*`), so the value and the key
now disagree. **That is intentional, not a bug to repair.** A future pass
that "fixes" the value back to 9,400 to match its key would reintroduce a
claim the site cannot source.

Same trap with the revision policy: the site says **two** free revisions
everywhere (`pricing.td_text.two_free_revisions_included.*`), while some
key names still read `...1_free_revision_and...`. Trust the value.

### Price-audit checklist

`i18n/*.json` keys are namespaced `tools.*` for tool pages but `index.*` /
`pricing.*` for the pages that legitimately show prices. Scan both, and
decide per namespace — a blanket price regex over the whole repo will flag
the intentionally-priced surfaces.

### TRAP: `รูป` is the Thai baht AND "photo"

On this site the Thai word for *photo* is `รูป`, which is also the Thai
currency word for *baht*. A price regex that includes `รูป` will:

- report false positives (`1,000 รูป` = "1,000 photos"), and
- if used to DELETE content, eat real copy — it removed the photo-count
  labels `label: '1 รูป'` from `th/tools/wedding-photo-book-planner` and the
  success message `แปลงรูปภาพสำเร็จแล้ว 0 รูป` from
  `th/tools/heic-to-jpg-wedding-photos`.

Use `บาท` / `ดอลลาร์` for Thai money and keep `รูป` out of currency lists.
Same class of trap: `写真` (photo) vs a currency word, `rub` vs `Rubber`.

### Anti-pattern: bulk token deletion leaves silent damage

A pass that deletes price tokens also deletes whatever the regex matched
next to them. The reliable detector is **not** a content heuristic — diff
each changed line against HEAD and check whether the current line is a
*pure deletion* of the HEAD line:

- deleted span contains a price -> expected, leave it
- deleted span contains a plain number (a year, a count, a ratio, an id) ->
  **damage**, restore the HEAD line

That single rule recovered 68 damaged lines across 45 files after a
digit-stripping pass had eaten `2026`, `12 designs`, `1,000 photos`,
`9:16`, `from 3 templates` and the `msvalidate` verification code.

## `**bold**` is converted to `<strong>` at render time

The content pipeline writes emphasis as `**text**`. Nothing in the client
(`js/i18n.js` only handles the language switcher) or in the dictionaries
turns those markers into markup — the conversion happens in
`functions/_middleware.js`, which calls `convertBoldMarkers()`
(`functions/_lib/bold.js`) as the **last** step of the transform, in both
the English and the translated branch.

Consequences for audits and edits:

- A `**` in an i18n value, or in the English source text of a
  `data-i18n` element, renders as bold. It is **not** a defect — grep
  hits for `\*\*` across the content are expected and must not be
  "cleaned up".
- The converter pairs two markers only when they sit in the same block
  scope, so a bold run never spans a paragraph, list item or table cell.
  An unpaired, empty or over-long marker stays literal text — *that* is a
  real source defect, and it is fixed in the content, not in the
  converter.
- To find those real defects, count the markers per `data-i18n` element
  and per i18n value and look for an **odd** count. A whole-document
  count is useless, because one stray marker shifts the parity of
  everything after it.
- `styles.css` styles `.blog-article strong` and 12,784 i18n values
  already use a literal `<strong>`, so `<strong>` is the intended
  markup.

Established 2026-10-24 (commit `692898ad`). Before it, readers saw raw
asterisks on 456 of the 722 pages — 37,704 markers in the static HTML
plus ~252,000 inside `i18n/<lang>.json`.

## Analytics stack: GA4 and Baidu Tongji are gone (2026-10-28)

The GA4 property `G-4FE7KSJDNB` was **deactivated by the account owner**
and Baidu Tongji (`hm.baidu.com`) was dropped because the site no longer
targets the domestic China market. Both loaders were stripped from every
static page — 688 pages, 1374 script blocks, plus the `generate_lead`
event in `js/main.js` / `js/main.min.js`.

What remains, and what may NOT be removed:

- **Cloudflare Web Analytics** — injected by Cloudflare Pages at the edge
  (`static.cloudflareinsights.com/beacon.min.js`). It is **not** in the
  source HTML, so a page that "looks missing" it is fine. Cookie-free.
- **Microsoft Clarity** (`clarity.ms/tag/ywxiu97hg8`) — free heatmaps +
  session replay, and now the only cookie-setting analytics.
- **Google AdSense** (`pagead2.googlesyndication.com`) — the revenue
  product. Never remove it while auditing analytics.

The retired origins were removed from the CSP in **both** places that
carry it: `functions/_middleware.js` (`buildCsp()`, the live per-request
policy) and `_headers` (the static fallback for non-HTML responses). A
whitelist entry left behind in either one re-opens the door.

`internal-tools/pre-deploy-check.ps1` check #6 now **FAILS** if a GA4 or
Baidu loader reappears, and also fails if the CSP whitelists a retired
origin. Do not soften it back into a "GA4 ID present" check.

The privacy policy paragraph that named Google Analytics 4 was rewritten
in all 10 dictionaries that carry the key
(`privacy.p_text.we_use_cookies_and_similar_tracking_tech.21144169`) plus
the static fallback in `privacy/index.html`. `ru.json` has no such key at
all — the Russian privacy page is served from the English source.

### TRAP: `gtag` matches `imgTag`

A case-insensitive grep for `gtag` hits `imgTag` in the tool pages
(`tools/wedding-photo-book-planner`), which reads like a live GA4
reference and is not one. Anchor on `googletagmanager.com/gtag/js`,
`G-4FE7KSJDNB` or `__loadGtag` instead.

### The removed lead event was never the lead path

The `/order/` form posts server-side to `/api/quote` (Resend email + KV),
so lead capture never depended on the browser-side events. The removed
client code was `gtag('event','generate_lead', …)` plus a
`navigator.sendBeacon('/__lead_event', …)` fallback — and
**`/__lead_event` had no handler anywhere** (not in `_redirects`, not in
`functions/`), so that fallback was already dead. Removing it loses
nothing. If a conversion signal is ever needed again, put it in
`functions/api/quote.js` (server-side), not in a third-party tag.

### Still open: the cookie banner gates nothing

`js/cookie-consent.js` writes the choice to localStorage but **no code
reads it to gate a loader**. Clarity therefore runs for users who chose
"Essential only". This predates the GA4 removal and is unchanged by it —
the site's "GDPR Compliant" badge is not yet backed by the behaviour.

### The custom domain's DNS lives only in the Cloudflare dashboard

`weddingai.video` / `www.weddingai.video` are Cloudflare Pages custom
domains. The zone is served by `valentin.ns.cloudflare.com` /
`ines.ns.cloudflare.com`, and **the records are not in the repo** — no
`_redirects` rule, no `wrangler.toml`, no DNS-as-code file. Nothing in
`internal-tools/pre-deploy-check.ps1` resolves the production hostname,
so a deleted apex record keeps CI green while the whole site (722 pages,
11 languages) is unreachable.

Found 2026-10-28: the zone held only NS + SOA + a yandex-verification TXT.
The apex had **no A / AAAA / CNAME** (NOERROR / NODATA) and `www` was
**NXDOMAIN**. The Pages project itself was healthy —
`weddingai-video-bin.pages.dev` still served the current build, and the
Cloudflare edge still answered for `weddingai.video` with the repo's own
CSP headers, so re-adding the DNS record restores service immediately
without any redeploy.

**Two independent things break, and both must be undone.** Restoring the DNS
record alone is not enough:

1. **DNS** — the apex CNAME was deleted from the zone → the domain did not
   resolve at all.
2. **Pages** — Cloudflare Pages **deactivates a custom domain whose DNS
   record disappears**. A deactivated Pages custom domain answers **HTTP 403**
   even after the DNS record is back, until Pages re-verifies it. The
   `GET …/pages/projects/weddingai-video/domains` object then shows
   `status: deactivated` (while `www` could still read `active`, which is
   why the outage looks inconsistent).

Repair, in this order:

| step | action |
|---|---|
| 1 | DNS → Records → CNAME `@` → `weddingai-video-bin.pages.dev`, proxy ON, TTL Auto |
| 2 | `PATCH /accounts/{account_id}/pages/projects/weddingai-video/domains/weddingai.video` body `{"status":"active"}` → status goes `deactivated` → `pending` → `active` |

`PUT` on that domain endpoint answers **405**; `PATCH` is the verb that works.

### TRAP: the Pages project name is NOT its pages.dev subdomain

The project is named `weddingai-video`, but its subdomain is
**`weddingai-video-bin.pages.dev`** (the plain `weddingai-video.pages.dev`
belongs to a leftover project from an earlier account that still serves an
older copy of the site — it is **not** the deployment target, and it is what
the repo's README / `qa/validate-deploy.py` used to point at).

Never guess the CNAME target from the project name. Read it:
`GET /accounts/{account_id}/pages/projects/weddingai-video` → field
`subdomain`. The same trap hits the preview URL pattern:
`<branch>.weddingai-video-bin.pages.dev`, not `<branch>.weddingai-video.pages.dev`.

`internal-tools/restore-dns-record.ps1` does all of the above (zone lookup →
read the real subdomain → ensure the CNAMEs → re-activate the Pages custom
domains → verify through DoH) and is the fastest way back.

#### TRAP: the local proxy hides a dead domain

This machine runs Clash Verge (Mihomo) in TUN + fake-ip mode, so
`Resolve-DnsName` returns a `198.18.x.x` fake IP for every name and the
real resolution happens at connect time through a Singapore proxy node.
A domain that no longer resolves can still return **HTTP 200** locally
for minutes or hours, because the node still holds the old answer; once
that expires the same URL fails with a TLS error (curl exit 35) and
`www` fails outright. Never diagnose this site with local
`Resolve-DnsName` or a plain `curl`.

Use a resolver path that cannot be hijacked or served from cache:

- `curl.exe -s -H 'accept: application/dns-json' 'https://dns.google/resolve?name=weddingai.video&type=A'`
- `curl.exe --doh-url https://dns.google/dns-query https://weddingai.video/` — exit code 6 = "could not resolve host"
- a raw DNS query over TCP/53 straight to an authoritative NS (bypasses the TUN's UDP-53 hijack)

**An A record from `Resolve-DnsName` is not proof the domain resolves, and
a 200 from this machine is not proof the site is live.** Public third-party
HTTP checkers (allorigins, codetabs) are useless here — Cloudflare answers
their egress with 522 even for the healthy `pages.dev` control.

#### TRAP: the DoH connect path is unreliable on this box

`curl --doh-url` resolves correctly but then connects straight to the
Cloudflare anycast IPs, and the local TUN drops a large share of those
connections: measured 2/8 successes for `weddingai.video`, 6/8 for
`cloudflare.com`, 7/8 for `example.com`. The failures are the **path**, not
the site. So the deploy gate's HTTPS probe retries across both the system
resolver and DoH and only fails when every attempt fails — never on a single
attempt.

## SEO metadata: the 10-language title/description pass (2026-10-28)

`internal-tools/pre-deploy-check.ps1` runs `scripts/check-seo-lengths.py`, which
is the **only** definition of "this title/description is too long":

```
title <= 60 chars, description <= 160 chars
```

Its regexes are strict and narrow, and that decides what the gate can see:

```python
title_pat = re.compile(r'<title>(.*?)</title>', re.DOTALL)
desc_pat  = re.compile(r'<meta\s+name="description"\s+content="(.*?)"', re.DOTALL)
```

* A `<title data-i18n="…">` is **invisible** to the gate — only a bare
  `<title>` is measured. Most blog pages therefore never reach the check.
* The measured length is the **unescaped** length (`html.unescape(...).strip()`).
* `og:description` / `twitter:description` are **not** measured at all. A long
  or broken social description never fails the gate.

### TRAP: the gate cannot see a `<details>` that grew an attribute

`scripts/verify-schemas.py` compared the visible FAQ count with the FAQPage
schema using `DETAILS_RE = re.compile(r'<details class="faq-item">')` — a regex
that only matches when the tag ends **immediately** after the class attribute.
Adding `id="faq-N"` to the element (so the `#faq-N` anchors inside the
schema actually resolve) made the regex match **nothing**, and the page then
reported `visible=0`.

A regex that silently matches nothing looks exactly like "nothing is wrong".
`DETAILS_RE` is now `<details[^>]*class="faq-item"[^>]*>` — tolerant of
attribute order and extra attributes. Any future scanner that counts markup
must be written the same way, and must be re-checked after the markup changes.

### TRAP: `re.sub` over a whole element deletes the body

The first version of `scripts/sync-faq-schema.py` added the `id` with

```python
DETAILS_RE.sub(repl, html_text)   # pattern captured the BODY as group 3
```

`re.sub` replaces the **entire match**, and the replacement only contained the
opening tag — so all four visible FAQ answers were deleted from the page. The
JSON-LD was still correct, so every count-based check still passed.

The fix is to match the **opening tag only** (`DETAILS_TAG_RE`, no body group)
and never to substitute an element that carries content. The bodies were
restored from `git show HEAD:<path>`.

### TRAP: an over-long field silently discards the whole file

`scripts/fix-seo-metadata.py` writes a file atomically: if any one field of a
file is over its limit, the **whole file is skipped** — including the fields
that were fine. A title fix therefore never lands while the description is
still one character too long. The script now reports the offending field by
name, and each field is applied independently.

### What was actually wrong (all pre-existing)

| defect | scope |
|---|---|
| title over 60 | 13 pages: 10 localized tool pages + `offline.html` + 2 EN tool pages |
| description over 160 | 8 pages, same set |
| description cut mid-word | ~30 pages across en/de/es/fr/pt/ru/ar/th/hi ("en estilos clásico", "dans des styles", "романтическ", "музыкальным сопровожде") |
| orphaned price-strip token | `en/tools/wedding-photo-collage` — title ended `"8 Styles at "`, description `"styles at in 9 minutes"` |
| Chinese copy in a Japanese page | `ja/tools/{add-text-to-wedding-photo, compress-wedding-photos, crop-wedding-photo-for-reels, heic-to-jpg-wedding-photos, remove-background-wedding-portrait}` carried the **zh** og/twitter description verbatim |
| English word inside a Japanese sentence | `ja/tools/wedding-budget-calculator` listed the category as `transportation` |
| invisible characters | `th/tools/save-the-date-maker` carried two U+200B inside its og/twitter description |
| missing FAQPage schema | `blog/wedding-video-trends-2026` showed 4 visible FAQs and shipped no FAQPage JSON-LD |

Localized titles keep each language's **own** suffix style (`… | WeddingAI.video`,
`… — Gratis`, `… — 無料`) so no language folder becomes internally
inconsistent. Where the head keyword and the "free" promise did not both fit
in 60 characters, the keyword won and "gratis"/"kostenlos" was dropped from
that title only — it stays in the description.

`scripts/sync-faq-schema.py` now exists and rebuilds the FAQPage block from
the **visible** copy, so the schema can never describe something the reader
does not see. It refuses to touch a page whose visible FAQ it cannot parse
(the tool pages ship a FAQPage schema with their own visible layout).

### `scripts/` is gitignored — new scripts need `git add -f`

`.gitignore:21` ignores the whole `scripts/` directory, but 321 files in it are
already tracked (they pre-date the rule). A **new** file there is invisible to
`git add .` and must be staged explicitly:

```powershell
git add -f scripts/sync-faq-schema.py
```

Both `.assetsignore` (`scripts/`, `internal-tools/`) and `.gitignore` keep the
local tooling off the deployed site.

## The gate was BLIND to the metadata the middleware actually serves

This is the single biggest SEO finding of 2026-10-28 and it changes what
"the gate is green" means.

### Two layers of metadata, only one of them checked

| layer | where the value lives | checked before 2026-10-28? |
|---|---|---|
| hard-coded | the static html, 132 pages | yes |
| i18n-bound | `i18n/<lang>.json`, 525 pages | **no** |

A translated page carries the English source in the html and the middleware
swaps in the dictionary value:

```html
<title data-i18n="blog.foo.title_text.bar">English source</title>
<meta name="description" data-i18n-attr="content:blog.foo.meta_description.baz"
      content="English source" />
```

The gate's regexes matched only the bare form, so **neither tag was ever
measured**. And the middleware runs the translation pass only when the
language is not the default (`if (lang === DEFAULT_LANG) return null;` in
`functions/_middleware.js`), so for an English visitor the static text is
literally what is served — and it was not measured either.

### The size of the blind spot

Resolving the live bindings (525 title keys + 525 description keys across the
11 dictionaries) shows **2 046 titles and 813 descriptions** over the limits
that the gate applies to hard-coded pages. The gate reported "751 OK, 0 over".

> **STATUS 2026-11-11: CLOSED — the numbers above are a 2026-10-28 snapshot,
> not a live backlog.** The per-language rewrite finished on 2026-10-30 (see
> the two "Result" sections below); the live check now reports **0 titles /
> 0 descriptions over** in all 11 languages, re-proven with an injected
> 220-char negative control so the zero is not a blind checker. Gate step 9b
> was flipped from `Warn` to `Fail` on 2026-11-11.
>
> A fresh scan that still returns ~2 000 / ~800 is measuring **ORPHAN keys**
> (the naive all-key scan currently gives 1 808 / 430). Each dictionary holds
> ~63 k keys but only ~250 of them are live per language. Orphans never render,
> so do NOT re-translate or truncate them — that is wasted work and repeats the
> mid-word-cut failure this section documents. Always resolve OWN + FALLBACK
> bindings first, the way `scripts/check-i18n-meta-lengths.py` does.

### The values are not merely long — they are machine-translation garbage

Sampling them shows the real problem. An Arabic title:

```
دليل فيديو Hochzeit Einladungs: So beeindruckst du deine Gäste
```

An Arabic title with Portuguese inside it:

```
Como Fotógrafos de Casamento Podem Ganhar Dinheiro com فيديو
```

An Arabic title with French inside it:

```
Quelle Durée pour Votre Vidéo de Mariage ? لو دليل Ultime
```

Truncating these to fit 60 characters would produce **shorter garbage** — the
same failure mode as the earlier mid-word cuts. The localized layer is a
**translation-quality** job, not a length job, and it needs a per-language
pass (or a re-translation), not a regex.

### What was done about it

- `scripts/check-seo-lengths.py` now matches the tag with any attributes
  (`<title\b[^>]*>`, `<meta\b[^>]*\bname="description"[^>]*\bcontent="`),
  so the **static** layer — which is what English visitors get — is enforced.
  195 values were over the limit there and all were fixed
  (`scripts/fix-static-meta.py`: 77 curated titles + 118 descriptions cut at a
  sentence, then clause, then word boundary).
- `scripts/check-i18n-meta-lengths.py` resolves the live bindings and reports
  the localized backlog. It is wired into the gate as step **9b** and was
  **report-only** until the backlog closed. Since 2026-11-11 the gate runs it
  with `--strict` and **fails the deploy** on any over-limit live value; the
  checker by itself still exits 0 unless `--strict` is passed.
- `scripts/sync-en-json-meta.py` keeps `i18n/en.json` in step with the static
  html, so the English row of the backlog is zero.

### The rule

**Never let a checker measure only the form it was written against.** When a
regex is relaxed to tolerate attributes, the same relaxation must be applied
to every other checker that looks at the same markup — and a checker that
reports "0 found" must be re-proven against a known-positive sample before
its zero is believed.

## The order@ mailbox: MX deleted, Resend silently suppressed, site said "delivered" (2026-10-29)

Found 2026-10-29 while chasing "the mail client can't connect to
order@weddingai.video". Three independent failures stacked, and each one
alone would have looked harmless.

### 1. The domain had NO MX for 17 days

The zone was cleaned on 2026-10-12 — the Resend send log still carries a
message literally titled "Resend API test (after DNS cleanup)" at 13:26 that
day. The Tencent enterprise mail MX records went with the cleanup, a
temporary Resend MX was added for the domain verification and removed again
within the hour, and `weddingai.video` answered NOERROR/NODATA for MX from
2026-10-12 ~14:57 until 2026-10-29.

A mail client cannot connect without an MX (autodiscover and every
MX-based client resolve the mail server through MX first), so "客户端连不上"
was only the visible symptom.

Restored 2026-10-29: MX `mx1.qq.com` (10), `mx2.qq.com` (20), `mx3.qq.com`
(30), plus apex SPF
`v=spf1 include:amazonses.com include:spf.mail.qq.com ~all`.

**The SPF deliberately carries two includes**: `amazonses.com` is Resend (the
site's only sending path), `spf.mail.qq.com` is Tencent enterprise mail (the
operator sends by hand from the mailbox). One record, two senders.

### 2. Resend's 2xx is NOT delivery, and one bounce suppresses the address for good

`POST /api/resend.com/emails` returned **200** for every one of those sends
and the site wrote `email_status: "delivered"` into KV. Resend's own event
log says `last_event: "suppressed"`. The hard bounce of 2026-10-12 14:57 put
`order@weddingai.video` on Resend's **suppression list**, and from then on
every send was accepted and silently dropped — no error, no log, no retry.

**`resend_status: 200` in a lead record proves only that Resend accepted the
request.** The truth lives in `GET /api/resend.com/emails/{id}` (`last_event`:
delivered | bounced | suppressed) and in `GET /api.resend.com/suppressions`.
Check both whenever a lead mail "did not arrive" — and note that the next
bounce re-suppresses the address, so clearing the suppression before the
mailbox itself is fixed buys nothing.

### 3. The mailbox was gone on the Tencent side as well

With the MX restored the test send still bounced, with Tencent's own reason
`550 Mailbox not found` (https://service.mail.qq.com/detail/122/169 = "您要发送的收件人不存在").

Probing every local part on the domain (`order`, `orders`, `admin`, `support`,
`contact`, `weddingai`, `noreply`, `mail`, `info`) returns the same 550,
while a known-good `541545849@qq.com` returns `250 OK`. **The whole domain
was unbound from Tencent enterprise mail, not just one mailbox.** No DNS
change can fix that — the operator has to re-add the domain and the `order@`
mailbox in the Tencent console. Always run that control probe before
concluding "the mailbox is fine, the DNS was the problem".

### Reading the lead records back

`GET /api/dead-letters?token=&key=lead:<ts>:<ref>` returns one lead.
**The endpoint allows only 10 reads per 5 minutes per IP** (429 after that),
so a bulk read has to filter on the reference id embedded in the key before
fetching any body. `internal-tools/resend-backlog-leads.ps1` does exactly
that and re-sends the backlog through Resend.

### Customer impact (2026-10-18 .. 2026-10-26)

4 real leads never reached the operator: Lisa Pellegrino (10-24 and 10-26)
and Monica (10-18 and 10-19). Lisa's 10-26 submission reads "Can someone
please reach out to me and just let me know if you can do this or not so I
can move on" — nobody could, because the notification was suppressed. Both
customers re-submitted because no reply ever came.

### Still open

* `functions/api/quote.js` hard-codes `TO_EMAIL_DEFAULT = "order@weddingai.video"`
  and **ignores** `env.TO_EMAIL` (commit 48cf7c14 forced the default to work
  around an env-pollution bug). Repointing the notification address is a code
  change plus a redeploy, not an env edit.

## The 企业微信邮箱 rules: MX hosts, DKIM and the anti-spoofing wall (2026-10-29)

Same day, later: the mailbox came back, and every guess about it that had
been made earlier turned out to be wrong. The rules below are the ones that
actually decided the outcome.

### 企业邮的 MX 是 mxbiz1/mxbiz2 —— 不是 mx1/mx2/mx3

腾讯企业邮 / 企业微信邮箱 (exmail.qq.com) require:

```
MX   @              mxbiz1.qq.com   priority 5
MX   @              mxbiz2.qq.com   priority 10
TXT  @              v=spf1 include:spf.exmail.qq.com ~all
CNAME mail          exmail.qq.com        (personalised webmail login)
```

`mx1.qq.com` / `mx2.qq.com` / `mx3.qq.com` are the **personal QQ mail**
cluster. Point the domain's MX there and Tencent answers `550 Mailbox not
found` for *every* local part, because that cluster has never heard of the
domain. The two errors look identical from the outside but mean opposite
things:

| state of the domain | unknown local part | meaning |
|---|---|---|
| not bound to 企业邮 | `550 Mailbox not found` | the domain is not bound here at all |
| bound to 企业邮 | `550 Mailbox unavailable or access denied` | **anti-abuse burst limit — NOT "no such mailbox"** |

⚠️ The second row was mis-read for hours. 企业微信帮助中心 doc 20057
(https://open.work.weixin.qq.com/help2/pc/20057) says exactly:

> **出错原因:** 您要发送的收件人短时间内收到大量邮件，为避免受到恶意攻击，
> 暂时禁止向该收件人发信。
> **改善建议:** 暂停向该收件人发信，稍后重新尝试。

So it is a **rate limit on the recipient** ("stop sending, try again later").
Behind a catch-all every local part shares one mailbox, so one burst of test
mails blocks the whole domain. It says nothing about whether a mailbox exists —
and it is a *transient* block, unlike a hard bounce, which lands on the
suppression list forever.

### TRAP: two DKIM TXT records at the same name break the verification

Resend publishes its key at `resend._domainkey.<domain>`. The zone had **two
TXT records at that exact name** (an old key and the current one). Tencent's
verifier picked the stale key, the signature failed, and the mail hit the
anti-spoofing wall below. Deleting the stale record fixed it. Keep exactly
one DKIM TXT per selector, and compare it against
`GET /api/resend.com/domains/{id}` → `records[]` before assuming a key is right.

### TRAP: a DKIM TXT published with literal quotes does not verify

The record was byte-perfect except for two quote characters: the Cloudflare API
stored `"p=MIGf...ABAQAB"` (220 bytes) while Resend's expected value is
`p=MIGf...ABAQAB` (218 bytes). A TXT RDATA is a character-string, so those
quotes are part of the key -- a validator reads the first tag as `"p` and finds
no `p=` key, so **the DKIM signature never verifies** and 企业邮 rejects the
mail as forged (`550 Mime from domain is a local domain`, doc 20072).

Two traps make this hard to see:

* **Resend's "verified" is a substring match, not a DKIM validation.** The
  domain object said `status: verified` with the quoted record in place.
* **DoH quotes every TXT value in its presentation.** `dns-query` returns
  `"v=spf1 ..."` for the SPF record too -- and that record has no quotes in the
  Cloudflare API. DoH output is *never* evidence either way.

The only reliable check is the **byte length in the Cloudflare API vs the length
of Resend's value**:

```powershell
$c = (Invoke-RestMethod ".../dns_records?type=TXT").result | Where-Object { $_.name -like 'resend._domainkey*' }
$c.content.Length          # must equal the Resend value's length, and must not start/end with a quote
```

Compare against `GET /api/resend.com/domains/{id}` -> `records[]` ->
`record: DKIM` -> `value`. Fix = `PATCH` the record with the exact value, no
quotes. Fixed 2026-10-29; the anti-spoofing 550 disappeared immediately.

### The anti-spoofing wall: a local domain may not send from a foreign server

Tencent's own rule (企业微信帮助中心 doc 20072,
https://open.work.weixin.qq.com/help2/pc/20072):

> **550 Mime from domain is a local domain** — the domain in the message's
> From header is registered with Tencent enterprise mail, so a mail sent from
> an outside server is rejected unless the domain has a DKIM signature that
> **verifies**. Fixes: (1) make the DKIM signature verify, or (2) use a
> subdomain in From (e.g. `mail.domain.com`) or a domain whose MX is not
> Tencent enterprise mail.

So once `weddingai.video` is bound to 企业邮, the site's own notifications
(`noreply@weddingai.video` → `order@weddingai.video`) only pass if the DKIM
signature verifies. This is why the site must never publish two keys for one
selector, and why the apex SPF must keep both senders:

```
TXT @ v=spf1 include:amazonses.com include:send.weddingai.video include:spf.exmail.qq.com ~all
```

`include:amazonses.com` = Resend (the site). `include:send.weddingai.video`
= Resend's newer `rmta.net` sending ranges (CNAME -> `send.forge.rmta.net`).
`include:spf.exmail.qq.com` = the operator's own Tencent mailbox. **Mind the
10-lookup SPF budget** — `spf.exmail.qq.com` alone expands to 4 more, and
each CNAME delegation costs another.

Resend's current expectation for this domain (`GET /api/resend.com/domains/{id}`):
TXT `resend._domainkey`, CNAME `rsend` -> `rsend-apne1.forge.rmta.net`,
CNAME `send` -> `send.forge.rmta.net`.

### TRAP: Resend's suppression is address-level and cannot be deleted away

Resend's own rule: *"if you do not address the issue that caused the email to
bounce, it will be automatically re-suppressed"*. `DELETE /api/resend.com/
suppressions/{id}` removes the **list entry** (the list then reads 0) but the
internal suppression survives and every later send to that address is
`suppressed` again. Case variants (`Order@`, `ORDER@`) do not help:
suppressions apply across all domains, subdomains and the whole team.

Consequence: an address that hard-bounced during an outage can stay
undeliverable long after the outage is fixed. The only reliable way through
is a **different recipient address** (an alias on the same mailbox) or a
Resend support/dashboard action.

Two API details that cost hours:

* `DELETE /api.resend.com/suppressions/{email}` takes the **email address**;
  `{id}` also answers `deleted: true`, and `{email}` answers **404** for an
  address that is not on the list. Both forms appear to work, and the list
  reads empty afterwards either way.
* **An empty suppression list does NOT mean the address is deliverable.** After
  deleting `order@` / `leads@` the list read `{"data":[]}` and a fresh send
  still came back `last_event: suppressed`. The suppression list is a *view*,
  the sending path is the *truth* — and the only oracle for the truth is the
  result of an actual send. Treat "the list is empty" as unproven.

### Probing a mailbox

The only cheap oracle is the SMTP `RCPT TO` stage (nothing is delivered):
`EHLO` -> `MAIL FROM:<probe@example.com>` -> `RCPT TO:<candidate>`. Always run
one **known-good control address in the same session** — without it, "550" and
"the domain is not bound here" are indistinguishable. Note that `mx1.qq.com`
returns `501 Bad address syntax` for a `@qq.com` control (personal accounts are
not valid on the enterprise cluster), so the control must be an address on the
same kind of domain.

⚠️ **A `250` at RCPT does not mean the mailbox exists.** With a catch-all
enabled, `order@`, `leads@`, `admin@` *and* `zzz-no-such-mailbox-9x8@` all
answered `250 Ok` — and the delivery of the first three still failed. RCPT is
only an existence oracle on a domain where unknown local parts are rejected.
The only real oracle for "does this land in an inbox" is an actual delivery
attempt — which costs one email and one suppression entry if it bounces.

The two 企业邮 errors to tell apart on a delivery attempt:

| bounce | doc | meaning | what to do |
|---|---|---|---|
| `550 Mime from domain is a local domain` | 20072 | the From domain is registered with 企业邮 and the DKIM signature did not verify | fix the DKIM record (see above) or use a subdomain in From |
| `550 Mailbox unavailable or access denied` | 20057 | the recipient got a burst of mail; the sender is temporarily blocked | stop sending for a while, then retry one mail at a time |

Order matters: the anti-spoofing check fires first for a real member mailbox,
so a `20072` bounce says nothing about whether the mailbox exists either.

### Re-sending the backlog

`internal-tools/resend-backlog-leads.ps1` reads the leads back out of KV
(skipping test leads by the reference id embedded in the key, so it stays
under the endpoint's 10-reads-per-5-minutes limit) and re-sends them through
Resend. `-To` and `-From` are parameters, so the same script can target the
mailbox, an alias, or a fallback inbox.

### The backlog goes in ONE message at a time

The first attempt sent all four leads back-to-back. Every one of them bounced
with `550 Mailbox unavailable or access denied` — the enterprise mail server's
anti-abuse limit (doc 20057), triggered by the burst itself. The script now:

* sends one message, **waits for its delivery event**, and only then sends the
  next one (`-SendDelaySeconds`, default 90);
* **stops the run on the first failure** instead of pushing the rest of the
  backlog into the same wall, and prints the bounce verbatim;
* re-checks every message at the end and reports `sent / delivered` counts.

Do not "optimise" this back into a batch send. A burst is what triggers the
block, and the block is invisible from the outside: the mails are accepted by
the API and then dropped by the receiving server.

### The delivery target is order@weddingai.video — the code default, no env var

The owner's decision (2026-10-29): new leads are notified to
`order@weddingai.video`. `TO_EMAIL_DEFAULT` in both `functions/api/quote.js` and
`functions/scheduled.js` already is that address, and `resolveToEmail()` only
lets `env.TO_EMAIL` override it when the value is a valid address.

**No Pages environment variable was added on purpose.** PATCHing
`deployment_configs.production` with a partial object risks dropping the KV
bindings that live in the same object — and those bindings are where the leads
are stored. The default gives the wanted behaviour with zero risk to the
storage layer.






## The live metadata lives in TWO places, and they drifted apart

Established 2026-10-29 while closing the localized title/description backlog.
Everything here was verified against the running middleware.

### A title/description reaches a visitor through one of two paths

| path | what the middleware serves | which dictionary key |
|---|---|---|
| **OWN** — `/es/blog/x/` exists | the localized file, with its `<title>` / `<meta description>` swapped for the dictionary value | the **Spanish-variant** key the page binds |
| **FALLBACK** — no `/es/` twin | the **English** file, with its `<title>` / `<meta description>` swapped for the dictionary value | the **English-source** key |

Both paths end at the same place: `dict[key]` (functions/_middleware.js:
`applyDataI18n` / `applyDataI18nAttr` — a direct lookup, no path traversal).

### The key model (this is the part that is easy to get wrong)

A key identifies a **source string**, not a language. The slug and the hash
come from the source text; the dictionary holds that string **translated into
its own language**. So:

    i18n/es.json["blog.affordable-wedding-video-ai.title_text.sin_presupuesto_para_videgrafo…"]
        -> "¿Vale la Pena el Vídeo de Boda con IA? Sin Presupuesto"   (Spanish)
    i18n/es.json["blog.affordable-wedding-video-ai.title_text.no_budget_for_a_videographer…"]
        -> "¿No puedes permitirte un videógrafo?…"                     (also Spanish)

The English-source key is what the ENGLISH page binds, and `es.json` holds
the **Spanish** translation under it. That is what the FALLBACK path serves.

### The checker used to measure only HALF of it

`scripts/check-i18n-meta-lengths.py` attributed a binding to the language of
the page that carries it, so the English-source keys counted for **en only**.
The translations under those keys — served to every language that has no
localized twin — were never measured. That is why the backlog was reported as
"212 titles + 122 descriptions" when the real live backlog was larger, and
why a language could show `0 over` while serving over-length titles.

**Rule**: the live set for language L is

    (keys bound by /L/ pages)  U  (English keys of English pages with no /L/ twin)

### The two layers must agree, and they did not

The static copy under `/<lang>/` and the dictionary copy under the same key
held **different text** on 40 of 100 es+pt bindings — both within the limit,
so the length backlog never saw them. The middleware serves the dictionary
copy; the file on disk carries the static copy. The site was therefore
serving something different from what it shipped.

Which side is right differs per language, and it has to be read, not guessed:

* **de / fr / es / pt** — the static copy was written in English-style Title
  Case ("Was Passt für euch?", "Steigern", "Quelle Option Choisir ?"), which
  is wrong in those languages. The titles were rewritten by hand in sentence
  case (nouns capitalised, verbs and adjectives lowercase).
* **ar / hi / th** — the static copy is the correct native text and was
  already within the limit. The **dictionary** copy was the stale one, so the
  dictionary was brought in line with the page (`SYNC_TITLE_FROM_STATIC` in
  `scripts/fix-lang-meta.py`).
* the Arabic dictionary held the **wrong article's** title under the LGBTQ+
  key ("أنشئ أول فيديو زفاف بالذكاء الاصطناعي…"). The page's own copy wins.

### The machine-translation garbage is in the ORPHAN keys, not in the live ones

Each dictionary holds ~63k keys; only ~100 of them are bound by a page of
that language. The mixed-language junk (a Portuguese "casamento" inside a
French description, Spanish "IA" inside German) lives on the **orphan**
variant keys. Each dictionary keeps its own language's value for every key,
so an orphan never renders — but a **live** key can still carry a foreign
word, and that one has to be fixed by hand.

## The localized metadata scripts

All four live in `scripts/` (which `.gitignore` ignores — a new file there
needs `git add -f`):

| script | what it does |
|---|---|
| `scripts/build-lang-meta-worklist.py` | the live worklist for a language: OWN vs FALLBACK, over-limit, drift, untranslated, missing |
| `scripts/fix-lang-meta.py` | hand-written titles and descriptions, published to **both** layers; also `DICT_ONLY` (no localized twin) and `MISSING_KEYS` |
| `scripts/cut-lang-desc.py` | shortens a description to the limit **without breaking it**, and writes it to both layers |
| `scripts/check-i18n-meta-lengths.py` | the live check — now parses meta attributes BY NAME, and also reports the bound `og:description` / `twitter:description` values |

### The description cutter's traps

A description must stay a sentence. Five things break that, and each one
produced a real defect before it was caught:

1. **Abbreviations are not sentence ends.** "Canva vs." was cut to 9
   characters. The sentence splitter must not break after a known
   abbreviation (`vs`, `z. B.`, `ca.`, `bzw.`, `u. a.`, …).
2. **A clause cut can land right after the subject.** "Entdecken Sie, wie
   KI-Tools …" became "Entdecken Sie." — a clause with no predicate. A cut
   clause must be substantial (≥ 5 words, ≥ 35 characters) and must not end
   with a pronoun or a function word that promises more.
3. **A clause that starts with a preposition is a fragment.** "Von
   Kindheitsfotos bis hin zum Hochzeitstag." is not a sentence.
4. **Hindi closes a sentence with the devanagari dandra `।` (U+0964)**, not
   a full stop. Without it in the splitter, every Hindi description looked
   like one long sentence and the cut could not find a boundary.
5. **Thai does not close a sentence at all.** There is no terminator to
   append, and the clause boundaries are commas and colons only.

A description that ends on a list ("… die Vorteile, die Nachteile.") or on
a subordinate question ("… was die Zeit spart.") is not usable either. Those
need a hand-written value — the cutter has an `OVERRIDES` table for them.

### The layer-agreement check is the one that matters

`scripts/check-seo-lengths.py` measures the file. `check-i18n-meta-lengths.py`
measures the live values. Neither proves the two agree. The invariant is:

    for every localized page:  static <title>/<meta description>
                              == i18n/<lang>.json[key that page binds]

and it is checked by comparing the **unescaped** static value with the
dictionary value (`&#x27;` in the file, `'` in the JSON).

### Result (2026-10-29)

All eleven languages: **0 titles over 60, 0 descriptions over 160, 0 missing
keys**. 700 localized bindings agree across both layers. The static layer
stays at `751 OK, 0 over`. The gate's step 9b is now clean — it stayed
report-only for another 12 days, then became blocking on 2026-11-11.

## The currency tokenizer read three locales wrong (2026-10-30)

`functions/_middleware.js` → `localizeCurrencyForLang` rewrites every USD
price in the served document into `$X <span class="wa-local-price">(≈ €9)</span>`,
so a visitor in a non-USD locale sees a rough local equivalent. The **number
parser** was the weak part, and it was wrong in three ways at once. Every case
below was proven by running the real function (old vs new) over the whole
corpus — 403 distinct price tokens, 13 294 documents that contain a `$`.

| what the copy says | what the OLD code did | what it does now |
|---|---|---|
| `$9,9` (decimal comma) | `$9 <span>(≈ R$49)</span>,9` — the span landed **inside** the number and 9 USD was converted instead of 9.9 | `$9,9 <span>(≈ R$53)</span>` |
| `$15.000` (European thousands) | parsed as **15** — a 1000× error — and the range `$1.000-$3.000` was cut mid-number | `$15.000 <span>(≈ €13.800)</span>` |
| `R$3.000` (Brazilian reais) | treated as USD and "converted" into euros/rupees | left alone — it is already a local amount |

Two more shapes the old regex simply did not match, so those prices got **no**
local equivalent at all: `US$ 9,9` and `$ 34,90` (a space between the symbol
and the amount).

The rules now in `USD_AMOUNT` / `USD_MARK` / `parseUsdAmount`:

* a separator followed by **three** digits is a thousands separator
  (`$1,000` → 1000), one or **two** digits is a decimal comma (`$9,9` → 9.9);
* the `$` starts a USD amount only when **no letter precedes it**, or when it
  is explicitly `US$` — so `R$` (reais) is never converted;
* one space after the `$` is allowed (`US$ 9,9`);
* the span is placed after the **whole** token, range included.

**A plain `$9.9` is byte-for-byte unchanged.** The gate's served-title model
in `scripts/check-i18n-meta-lengths.py` was updated to the same tokenization
(`parse_usd_amount`), because a checker that models a different tokenizer
measures a title the visitor never sees.

### The gate's title budget must include the injected currency text

The `<title>` is **not** a `<meta>` tag, so the middleware's meta-stash does
not protect it: the price in a title is rewritten too, and the span's *text*
counts towards the title a visitor sees. `served_title_length()` adds the
length of `(≈ EUR9)` per price. The localised homepage titles were shortened
until the **served** length fits — `pt 60`, `es 59`, `ru 57`, `th 54`,
`ar 53`, `de 50`, `fr 49` — and the price itself was kept, not deleted.

## The machine translation transliterated the DOMAIN (2026-10-30)

The brand is `WeddingAI.video`. The machine translation wrote the **domain**
in the target script — `वेडिंगएआई.वीडियो` in Hindi (1 812 dictionary values)
and `СвадьбаAI.видео` / `СвадьбаAI.video` in Russian (5). A visitor in Delhi
was told the site was called `वेडिंगएआई.वीडियो`.

The authoritative native layer never did this: the Hindi static pages write
`WeddingAI.video` **835** times and `वेडिंगएआई.वीडियो` **0** times; the Russian
static pages write it 179 times and `СвадьбаAI.видео` 0 times. So the
transliteration was machine residue, not a house style — and both layers were
rewritten with the same token list so they keep agreeing.

**TRAP: `वेडिंग` is the Hindi word "wedding", not the brand.** The bare
transliterated *product* name is `वेडिंगएआई`; the common word is `वेडिंग`.
Grepping for the short form flags 800+ legitimate values. Match the full
`वेडिंगएआई` (or the brand in Latin) and never the three-letter prefix.

## The localized fallback titles had drifted from their English source (2026-10-30)

The last 23 over-limit titles were the **fallback** ones: `hi` (18) and `ru`
(5), each bound by exactly one page — the **English** one. Changing the
dictionary value therefore touches no localized page and creates no
two-layer drift (a key bound by a localized page would).

They were not just long, they were **stale**: they translated the *old*
English title. The English title now reads "15 Unique Wedding Video Ideas",
the Hindi one still said **25** — a factual contradiction between the two
languages on the same page. The rewritten values translate the **current**
English title in the language's own native house style (Hindi: natural
sentence, no brand suffix, no price; Russian: `… | WeddingAI.video` on the
service pages, matching the native `ru/tools/*` pages).

## Result (2026-10-30)

All eleven languages: **0 titles over 60, 0 descriptions over 160, 0 missing
keys** (ru still lacks 214 translation keys — a content gap, not a length
one). 700 localized bindings agree across both layers, the static layer stays
at `751 OK, 0 over`, all 11 dictionaries round-trip byte-identically, and the
full pre-deploy gate reports **Errors 0, Warnings 1, READY TO DEPLOY**.

## The blog hub says 100+, but its KEY still says 50 (2026-11-11)

The canonical article count is **100+ articles in 11 languages**. There are
100 posts under `blog/*/index.html`, commit `38091edd` deliberately picked the
"100+ articles in 11 languages" SERP angle, and the `resources` / `search`
pages plus the `hi` and `ru` titles already say 100+.

**TRAP: `blog.meta_description.50_in_depth_articles_on_wedding_video_re.17313271`
is a KEY NAME, not a claim.** It was never renamed, so a pass that "fixes" the
value back to 50 to match the key reintroduces a stale number — exactly the
`9_400` / `1_free_revision` trap. Trust the value. Until 2026-11-11 the ten
non-English dictionaries still described the OLD 50-article source while the
English `<title>` said 100+; they were rewritten per language, keeping each
language's own sentence.

**The blog hub has NO localized static file.** No `<lang>/blog/index.html`
exists, so all 11 languages reach `/<lang>/blog/` through the FALLBACK path:
the English file, with the title and description swapped from
`i18n/<lang>.json`. Those two keys are therefore live in EVERY language, and
a language that lacks them keeps the English copy. `ru` lacked both until
2026-11-11.

**Four layers, not two.** A fallback key of the blog hub must agree across:

1. `i18n/<lang>.json`
2. `i18n/shards/<lang>/bundle.dfde240c30a6255f.json` — the hub binds ~100
   namespaces, so it is served from the page BUNDLE, not per-namespace shards
3. `i18n/shards/<lang>/blog.{title_text,meta_description}.json`
4. `i18n/<lang>.manifest.json` — both namespace entries

Editing only the dictionary changes nothing a visitor sees, and
`verify-i18n-shards.py` will report the drift. `ru` was missing all four.

**TRAP: a mid-word cut can be UNDER the limit.** The English meta description
had been cut to 155 characters ending in `9 styl`, so `check-seo-lengths.py`
reported it as fine. It was rewritten as a complete 154-character sentence,
and the `og:description` / `twitter:description` / Blog JSON-LD — which stay
English on fallback pages and are NOT bound to the dictionary — had their
stale "50 in-depth articles" bumped to 100+ too. Do not "normalise" those
cards to the `<title>`; only the number was wrong.

Step **9b** of `pre-deploy-check.ps1` now also fails on a missing live key
(`total_m` had been computed but never used). Both failure modes have a
negative control: inject a 220-char title, or delete one live key, and
`--strict` must exit 1.

### The SERP angle is now in all 11 `<title>` values

Until 2026-11-11 only `en`, `hi` and `ru` carried "100+ / 11 languages" in the
blog hub `<title>`; the other eight still used the older
"tips, guides and AI insights" angle with no count at all. All eight were
rewritten in their own house style:

* sentence case for `de` / `es` / `fr` / `pt` (French keeps the space before
  the colon), not English Title Case;
* **no brand suffix** — only ~15 of ~450 `.title_text.*` values per language
  carry `| WeddingAI.video`, so a suffix here would be the outlier;
* head keyword first, then the 100+ / 11-languages angle. All 11 titles are
  20-55 characters, so nothing had to be dropped to fit the 60-char budget.

**The social card is deliberately NOT part of this.** `og:title` /
`twitter:title` on the English hub still read
"Wedding Video Blog: Tips, Guides & AI Insights | WeddingAI.video". They are
not bound to the dictionary, stay English on every fallback page, and this
site intentionally gives the card a different headline from the `<title>`.
Do not "normalise" them to the SERP title.

## The 13 tools got a full bug-fix pass on 2026-10-16 — a bug report may describe the pre-fix build (2026-10-30)

Commits `869d4504` (Bug #7/#10/#17 + iOS PWA meta + IIFE->DOMContentLoaded) and
`5a0f4b59` fixed the P0/P1 tool bugs in one pass. Verified 2026-10-30: the
**live** site already serves the fixed build (marker check on all 13 tool
pages: `DOMContentLoaded`, `PRESET100`, `SEAT-SORT`, `CSV-ROWS`, `SIGN`,
`BINDPHOTO`, `CROP-DISCLOSE`, `RM-BG-AUTO`, `BOOK-STAT` all present).

A test report claiming "100% reproducible, 5-6 of 13 tools crash on load"
therefore describes a **pre-2026-10-16 snapshot**, not the current site.

### What the report got right, and what is still open

* **#18 Crop "Smart center" is fake — TRUE, and only half-fixed.** The code
  has no face detection (hard-coded `biasY = H * 0.6`). The *control* now
  says "Off-center bias (heuristic, not face detection)", but the page still
  advertises AI face detection in the `<meta name="description">`, the
  comparison table ("AI face-centered auto-crop"), the body paragraph
  ("runs the face-detection model in the browser"), the SERP paragraph and
  the tools-hub card. The page contradicts itself in the same viewport.
* **Same class, not in the report:** `tools/compress-wedding-photos` claims
  "face-aware quality preservation" / "Face-aware AI quality 60-85%
  reduction" and beats competitors on "no face detection" — its JS is plain
  canvas re-encode, no face logic at all.
* **#19 `apple-mobile-web-app-capable` — only the English pages were fixed.**
  Still present on 153 files: 130 localized tool pages, `services/*`,
  `about/`, `gallery/`, `terms/`, `privacy/`, `order/`, `search/`,
  `resources/`, `success/`. Root cause: `internal-tools/inject-pwa-tags.ps1`
  still writes the deprecated tag, so fixing the pages alone lets the next
  run re-inject it. **Fix the script and the pages together.**

### Audit rule

Before acting on a bug report for this site, check the **live build's**
markers, not just the repo. And when a report says "100% reproducible" in a
real browser against the live site, treat that as a claim about an older
build until the live HTML is checked.

## 63% of the site returned 503: the dictionaries were parsed per request (2026-10-31)

### The measurement

Crawling all 1539 sitemap URLs against the pinned edge IP (correct SNI, no
local DNS cache) gave:

```
en  2.2% 503    ru  7.9%    ar 26.4%    de 53.6%    es 77.9%
hi 82.9%        ja 86.4%    pt 85.7%    th 93.6%    zh 97.1%
-----------------------------------------------------------------
ALL 63.3%  (974 of 1539 URLs)
```

The error body is exactly `error code: 1102` - Cloudflare's Worker CPU limit.
English is fine because `if (lang === DEFAULT_LANG) return null;` means the
English path never loads a dictionary. Every other language degrades in
proportion to the size of its dictionary.

The dictionaries are 6-17 MB; a pure `JSON.parse` of one costs **219-591 ms**
against the 50 ms the CF Pages Free plan allows.

**The 5-minute body cache cannot rescue this.** `getCachedProcessedBody` only
helps a page whose build already succeeded once; the first build blows the
limit, throws, and the cache never receives an entry. The failure is permanent
for that URL.

### The fix: namespace shards

`qa/build-i18n-shards.py` splits each dictionary into per-namespace shards
(407-408 per language, biggest 366 KB) plus a manifest at
`i18n/<lang>.manifest.json`. A page loads only the namespaces its own
`data-i18n` keys live in - about 10 of the 407. Parse cost drops from
219-591 ms to **1.2-13.9 ms**.

`functions/_lib/i18n-shards.js` does the loading; `functions/_middleware.js`
calls it and falls back to the full dictionary if anything is missing, so the
behaviour degrades instead of breaking.

### TRAP: namespace granularity is too coarse for the blog hub

`blog/index.html` binds the title and the meta description of ~100 articles.
But each article lives in its own namespace that holds the **entire article
body** (~1000-1400 keys, 170-370 KB each). So the hub needed **111
namespaces** - over the 40-shard budget of the loader and over the
50-subrequest limit of the plan - and the union of those namespaces is
**85-87% of the whole dictionary** (9-15 MB).

Re-bundling by prefix does NOT help: the payload would be the same 9-15 MB,
and parsing it is exactly what blows the CPU limit. The only fix is to stop
loading the article bodies.

### The page bundle

For a page over the budget, the builder emits ONE bundle file holding
exactly the keys that page binds, plus the few keys the middleware looks up
by a fixed name (`index.og_*`, `index.twitter_*`, `pricing.meta_*`,
`homepage_faq.qN.*`, `pricing_faq.qN.*`). For the blog hub that is ~190 card
strings - **47 KB instead of 9-15 MB, one request instead of 111**.

The bundle is keyed by the hash of the page's **namespace set**, because that
is what the runtime can compute from the html it is about to serve. The
manifest carries it under `__bundles__`; the runtime looks the hash up and,
if it finds a bundle, fetches that one file. No bundle -> the old namespace
path.

### The freshness gate (step 9d)

The shards are a DERIVED artefact. Editing `i18n/<lang>.json` without
rebuilding them makes the middleware serve the OLD translations - silently,
because the page still returns 200. Nothing in the old gate could see it.

`scripts/verify-i18n-shards.py` (wired into
`internal-tools/pre-deploy-check.ps1` as step 9d, FATAL) proves:

1. **Coverage** - every namespace of every dictionary has a manifest entry.
2. **Freshness** - the shards, merged, equal the dictionary exactly. This is
   the real staleness test.
3. **Parity** - `namespaceOf()` in `functions/_lib/i18n-shards.js` agrees with
   `ns_of()` in `qa/build-i18n-shards.py`. If they drift, the middleware asks
   for shard files that do not exist and every translation silently falls
   back to English.

It also proves the bundles: the right file, keyed by the right namespace-set
id, carrying every key the page binds.

### TRAP: the builder's key parser filed `title:key` under `_root`

The builder used to understand only `data-i18n="key"` and
`data-i18n-attr="content:key"`. So:

* `data-i18n-attr="title:key"` was parsed as the key `"title:key"`, whose
  namespace came out as `_root` - no shard was ever built for the real
  namespace, and the binding stayed English.
* `data-i18n-attr="content:a|b"` was parsed as ONE key `"a|b"`, so only one of
  the two namespaces was ever requested.

Both bugs show up as untranslated text, never as an error. All three
implementations (builder, verifier, runtime) now use the same rule, and the
verifier cross-checks the Python and the JavaScript against each other.

### TRAP: a concurrent writer can empty `i18n/<lang>.json`

`i18n/ja.json` was once reduced to **0 bytes** by a plain
`open(path, "w")`, which truncates BEFORE the write. `scripts/set-i18n-values.py`
now writes to a temp file, fsyncs it and `os.replace()`s it over the target,
which is atomic on Windows.

Read a dictionary that is being rewritten and you can get a torn or empty
file - a `json.loads` error that looks like a corrupt file but is really a
race. Another agent session working on the same workspace is enough to cause
it.

### The rule

**Rebuild the shards as the last step before a deploy, and let the gate
prove it.** The shards and the manifests are NOT tracked by git yet - they
have to be `git add`ed, or the middleware falls back to the full dictionary
and the 503s come straight back.

```
powershell -File internal-tools/refresh-i18n-shards.ps1
```

rebuilds and verifies in one go, and exits non-zero if anything is still out
of sync. Run it AFTER every other session that touches `i18n/<lang>.json` has
finished - see the trap below.

`node tests/middleware-i18n-check.cjs` runs the real middleware against the
real files with a mocked origin and asserts the whole chain: no markup in
the `<title>`, the trust line and the footer badge translated, the shard path
used (not the full dictionary), and the blog hub served from a bundle with
its card titles translated.

`node tests/cookie-consent-check.cjs` does the same for the cookie banner,
which the middleware's server-side pass cannot reach because it is built at
runtime.

## The hreflang graph was broken in three ways (2026-11-01)

### What the live site served

The middleware builds a correct hreflang block (11 languages + x-default)
and injects it, but it first has to REMOVE the author's own block. The
strip regex only matched ONE attribute order:

```
<link rel="alternate" hreflang="xx" href="...">      stripped
<link href="..." hreflang="xx" rel="alternate"/>      NOT stripped
```

The 50 `hi/blog/*` pages are written in the second form, so their block
survived next to the injected one and the live page served **24 alternate
links instead of 12** - "Hreflang: Multiple Entries" in Search Console.

Measured live (pinned edge IP, correct SNI): 12 of 13 sampled pages were
fine; `/hi/blog/affordable-wedding-video-ai/` was the broken one.

### The author's blocks were themselves wrong

Three defects, all invisible to a naive read of the markup:

* **MISSING LANGUAGES** - 670 pages advertised only 10 languages. The `hi`
  graph (added with the November 2026 Hindi launch) was never backfilled:
  622 pages had no alternate for a language that exists.
* **THE WRONG LANGUAGE IN THE `zh` SLOT** - the block was copied from the
  ENGLISH page with the page's own language prefix substituted into the
  FIRST localized entry, which in the template is `zh`. So every localized
  page outside the zh folder advertised `zh` pointing at ITSELF: an `/ar/`
  page told Google the Arabic version of the page is the Urdu one.
* **DUPLICATED ENTRIES** - 34 pages carried the English page's `en` +
  x-default pair next to their own, so the same hreflang value appeared
  twice (68 duplicate values in total).

### The fix

* `functions/_middleware.js` - `stripCanonicalAndAlternates()` parses the
  attributes instead of matching them positionally, so any order and any
  quoting is handled.
* `scripts/fix-hreflang-blocks.py` - rewrites every page's block to the
  canonical 12-entry form and verifies each file before writing it.
* `scripts/verify-hreflang.py` - the checker; wired into the pre-deploy
  gate as step 9e (FATAL).

**The lesson**: the middleware was already generating the right thing. The
defect was that the cleanup step only understood one spelling of the markup
it had to remove, so the stale copy leaked through. A cleanup that matches
one form is a cleanup that silently does nothing on the other form.

### TRAP: 633 of the 722 html files started with a UTF-8 BOM

Harmless in a browser, but it breaks every naive text tool:
`text.startswith("<!DOCTYPE")` is False, `re.match(r"^<html")` is None. It
also blocked `scripts/fix-hreflang-blocks.py` from touching those files at
all - the script refused to rewrite a file it could not reason about. The
BOMs were removed in the same pass.

## `js/langs.js` and `functions/_lib/langs.js` are NOT byte-identical

The older note in this file said the two must stay byte-identical. They
deliberately are not any more: `js/langs.js` also assigns
`window.WA_LANGS` / `window.WA_DEFAULT_LANG` / `window.WA_RTL` for the
browser, and the Functions copy has no `window`. What must match is the
**LANGS array**, and `scripts/check_langs_sync.py` checks exactly that.

### TRAP: that script also reported a false positive about `_redirects`

It demanded a `/en/* → /:splat 200` rule for every language including the
default one. The default language needs NO such rule: `/about/` IS the
English source, and the rule exists to reach the English source FROM a
localized url. Adding it would be actively harmful - it would match
`/en/blog/01-<old-slug>/` BEFORE the 50 blog 301 rules that migrate those
slugs, sending visitors to a 404 instead of the 301.

`scripts/check_langs_sync.py` now excludes the default language.

## The free tools advertised AI they never had (2026-11-01)

A capability audit of the 13 free browser tools against their own JavaScript.
Every claim in their copy was checked against the implementation, and the two
layers had drifted apart. **Nine tools shipped claims their code cannot
support.**

### What each free tool actually does

| tool | actual implementation | what the copy claimed |
|---|---|---|
| crop-wedding-photo-for-reels | hard-coded off-center bias (`biasY = H*0.6` landscape / `H*0.5` portrait) | "AI face-centred", "face detection" |
| compress-wedding-photos | canvas re-encode + quality slider | "face-aware compression" |
| wedding-photo-collage | 6 fixed `LAYOUTS` (grid-2x2, grid-2x3, grid-3x3, grid-3x4, strip-h, strip-v) and **no filter/preset system at all** | "8 AI styles (cinematic, vintage, cartoon, pet, meme, multilingual)", "AI auto-pair detects wedding chapters" |
| wedding-photo-book-planner | 5 plain layouts (1/2/3/4 photos + cover); `autoDistribute()` fills slots in upload order | "AI auto-pairs photos per chapter", "auto-pairs by theme (preparation/ceremony/reception/portraits)", "9 AI styles", "AI Layout" |
| remove-background-wedding-portrait | RGB colour key (`hexToRgb`) | "AI face preservation", "9 Thai wedding background styles" - there is no background library, only colour-key presets |
| heic-to-jpg-wedding-photos | `<img>` decode (Safari only) + `drawImage` -> `canvasToBlob` | "EXIF preserved", "auto-pair into the video workflow", and a "Hand off to AI Video Generator" button + "upload queue" that **do not exist** |
| add-text-to-wedding-photo | fixed text positions, no caption generator | "AI 10 IG captions auto-generated" |
| wedding-hashtag-generator | template combinations in the browser | "AI generates 50+ hashtag ideas" |
| wedding-seating-chart-maker | `autoAssign()` sorts guests by group (vip > family > friends > work > other) and fills the seats | "AI no-overlap auto-assign", plus invented constraints ("no divorced parents together", "grandparents near the exit") and "runs in 9 seconds" |
| wedding-invitation-maker | `getTemplate()` / `render()` over a fixed template set | "AI auto-designs layout from names + venue" |
| save-the-date-maker | local canvas card render | "AI save-the-date card" |

### The rule

A free in-browser tool must not claim a capability its own JavaScript does
not implement. Two kinds of claim were removed:

1. **Invented capability** - face detection, chapter detection, auto-pairing,
   EXIF preservation, a button that does not exist.
2. **Overstated mechanism** - calling a deterministic local algorithm "AI".
   The comparison tables list "no AI auto-design" as a *competitor's* weakness,
   so the label is a comparative claim, not decoration.

What was kept: every "AI" that modifies the **AI wedding video product** (the
paid server-side service). Those cannot be verified from this repository, so
they stay - the same boundary that keeps `blog.*` and `services.*` untouched.

### The dictionary KEY NAMES are not the bug

`td_text.8_ai_styles_2_30_photos`, `th_text.ai_layout`,
`td_text.ai_auto_pairs_photos_per_ch` still carry the old words in their key
names. That is intentional - the key is an identity, the value is the copy.
Same trap as `pricing.td_text.9_400_couples_served_*`: a value that disagrees
with its key is not automatically wrong.

### The static layer and the dictionary layer both carry the English source

The localized static pages keep the ENGLISH text in their `data-i18n` lines,
so one byte-level replacement pass fixes the English page, the localized page
and the fallback path at the same time. The dictionary then needs its own
translation per language. Both layers must be done, or the site serves two
different stories for the same key.

### TRAP: zero-width spaces make a substring replacement match nothing

Several stored values contain U+200B inside a phrase (`EXIF preservado`).
A literal `str.replace` silently finds nothing there and reports "0
replacements" - which looks exactly like "nothing to fix". Use a regex with
an optional zero-width-space class and **assert the match count**.

### TRAP: my own correction propagated a false claim into 9 languages

The collage copy said "8 distinct styles (cinematic, vintage, ...)" and the
styles do not exist - the tool has 6 layouts and no style system. A first
pass replaced the *chapter detection* claim and left the style list intact,
then translated that English into 9 languages. The number was wrong in every
one of them. **Verify the nouns in a claim, not only the verb.**

### Writing a 10 MB dictionary must be atomic

`open(path, "w")` truncates first, so a failure mid-write leaves a 0-byte
file. `scripts/set-i18n-values.py` writes a sibling temp file, fsyncs it and
`os.replace`s it into place. A worker once truncated `i18n/ja.json` to 0 bytes
this way.

### The gates

* `scripts/scan-false-capability-residuals.py` - full-site scanner for the
  claim phrases above. Its classification is **negation-aware** ("no face
  detection", "顔認識なし", "人脸识别不明确" are honest) and its scope
  excludes `blog/` and `services/`, which describe the AI video product.
* `scripts/scan-face-claims.py` - capability-assertion parity between every
  localized value and its English canonical. A localized value that asserts a
  capability the English value does not is machine-translation drift.
  **Thai has no space after the negation**: "ไม่รับรู้ใบหน้า" puts "ไม่"
  directly in front of the token, so a negation list that only knows
  "ไม่ " (with a space) misses every Thai negation and reports six false
  positives. The bare "ไม่" belongs in the list.
* `scripts/check-shard-values.py` - compares the **values** of the keys this
  pass changed against the rebuilt shards. `verify-i18n-shards.py` compares
  key SETS, so a stale shard set with matching keys would still pass it.
* `scripts/verify-no-false-face-claims.py` - the per-change gate.
* Fixers: `scripts/fix-en-false-ai-claims.py` (English layer + all localized
  static pages), `scripts/fix-tierb-ai-labels.py` (the "AI" mechanism labels),
  `scripts/fix-residual-claims.py` (last batch), `scripts/build-lang-false-ai-fixes.py`
  and `scripts/build-th-drift-fixes.py` (per-language packages).

Every dictionary change requires a shard rebuild afterwards - `i18n/shards/`
is the artifact the middleware reads first, and a stale shard set serves the
old copy silently.




## The numbers the copy gave and the code never had (2026-11-01)

A second pass over the same 13 free tools found a class the earlier one
missed: the copy quoted a **count**, and the count was wrong. Every number
below was measured from the tool JavaScript, not inferred:

| tool | real | the copy said |
|---|---|---|
| `wedding-invitation-maker` | `TEMPLATES` = 3 (formal, modern, photo) | 8 styles |
| `wedding-video-invitation-maker` | `TEMPLATES` = 5 (classic, romantic, modern, bold, photo) | 8 styles |
| `wedding-photo-collage` | `LAYOUTS` = 6, max **12** photos | 8 styles, 2-30 photos |
| `add-text-to-wedding-photo` | `FONT_STACKS` = 14 keys | 50 fonts |
| `compress-wedding-photos` | `canvas.toBlob()` drops EXIF | "EXIF kept" |

The invitation maker is the clearest case: its own `og:description` and
`twitter:description` had already been corrected to "3 templates - Formal,
Modern, Photo Forward", and its JSON-LD said "3 templates" - but the
`<title>`, the `<h1>`, the `<meta name="description">`, the comparison table
and the tool card still said **8 styles**, and in some languages they listed
the AI *video* styles (cinematic / trailer / vintage / pet / storybook) as
if the card maker produced them.

### TRAP: three layers, three different truths

| layer | what it holds | who wins |
|---|---|---|
| `og:` / `twitter:` | usually the honest copy | - |
| `<title>` / `<h1>` / `<meta name="description">` | often the stale copy | the code |
| `data-i18n` element text | the ENGLISH source, in every language | the dictionary |

The localized pages carry **native** `<title>` / `<meta description>` (de
"Kostenloser Hochzeitseinladungs-Generator", ja "5 つのテンプレート") but the
**English** source inside their `data-i18n` elements. So one byte-level pass
over the element fixes the English page, the localized page and the runtime
fallback path at once - while the localized `<title>` needs a separate,
native edit.

### TRAP: a wrong count is not automatically a wrong sentence

The collage comparison table has one row per tool. Pi7, PhotoJoiner,
Photovisi and PhotoCollage.com really do take 2-30 photos, and their cells
carry the SAME key family (`td_text.2_to_30.<hash>`) as our own cell
(`2_to_30.9c0d1e2f`). A blanket "no 2-30 in the collage namespace" rule
flags the competitors' true claims. The discriminator that works: our row
either uses one of the two known our-cell keys, or lists our own layout grid
(`2x2 / 2x3 / 3x3 / 3x4`).

Same for "8 styles": the AI wedding **video** product genuinely ships 8
styles, and they are quoted in `tools.faq.*`, `tools.why.*`,
`tools.p_text.*`, `tools.video_section.*` and the save-the-date card
(`tools.card.tag.gen.11`). Those are true and must stay. Only the two
invitation tools' own namespaces are scanned for a count.

### TRAP: canvas re-encoding does not keep EXIF

`js/tools/common.js` -> `canvasToBlob()` is a bare `canvas.toBlob()`
wrapper. The output is written from the canvas bitmap, which carries no
metadata, and nothing in the repo re-injects EXIF. So the compress page's
"browsers keep EXIF when re-encoding is done this way" was false, and the
page contradicted itself two sentences later ("EXIF is read again from the
original files"). The same mechanism made the HEIC converter's "EXIF
preserved" false earlier.

`canvas.toBlob()` never keeps EXIF - that is why libraries like
`piexifjs` exist. The honest phrasing is "re-encoding writes raw pixels, so
camera info and dates are not carried over".

### TRAP: I reproduced the `re.sub`-deletes-the-element bug

`scripts/fix-count-claims.py` replaced a `<title>` with
`text[:start] + group1 + text[end:]` where `group1` was the element's
**content**, not the whole match. The result: the `<title>` and
`<meta name="description">` tags were deleted from three pages and their
bare text was left behind in `<head>`. This is the same trap AGENTS.md
records for `scripts/sync-faq-schema.py`, and I walked straight into it.

The lesson is now enforced by a gate:

* `scripts/check-html-structure.py` - every deployed page must have exactly
  one `<title>`, one `<meta name="description">`, one `</head>`, one `<body>`
  pair, at least one `<h1>`, and **no bare text directly inside `<head>`**.
  The text is located with `html.parser`, not a regex: a `>` inside an
  attribute value breaks every tag-stripping regex, and the title's own
  content is legitimate prose.
* `scripts/repair-meta-tags.py` - puts the deleted markup back.
* `scripts/fix-stray-gt.py` - removes the stray `>` that earlier passes left
  after a self-closing `<meta>` (30 files, 60 spots). A browser ignores it,
  but it makes the structural check impossible.
* `scripts/fix-head-tag-leftovers.py` - cleans the `... /> />` duplicate and
  the `<meta property="og:title" ...</title>` that lost its closing `>`.

**Always replace the content in place** (`group1 + new + group3`), never
rebuild the match from the content alone.

### The gates for this pass

* `scripts/scan-false-capability-residuals.py` - rewritten. It now carries a
  **truth table** (the counts above), scopes every count rule to the tool
  that makes the claim, and knows the difference between our row and a
  competitor row. It also **proves itself before reporting**: a synthetic
  false claim must be flagged and a synthetic honest one must not, so "0
  findings" can never be confused with "matches nothing".
* `scripts/check-html-structure.py` - the structural gate described above.
* `scripts/verify-no-false-face-claims.py` - still PASS; its canonical file
  `scripts/en.face-canonical.json` is the approved English wording for the
  19 tracked keys and has to be refreshed whenever one of them changes.
* `scripts/check-seo-lengths.py` - still 751 OK / 0 over.

### New helper: the setter can add a key

`scripts/set-i18n-values.py --add-missing` appends a key that does not exist
yet instead of aborting. Nine of the eleven dictionaries had no
`tools.card.badge.edit.06` at all, so the badge fell back to English on
every localized page. The insert keeps the house format (2-space indent, one
key per line) and inserts before the closing brace, where JSON forbids a
trailing comma.

### Still open (deliberate, for the owner to weigh)

* Three English titles still label the free tool's own output as AI -
  "Add Text to Wedding Photo: **AI** Batch", "Save the Date Maker: **AI**
  Save-the-Date", "Remove Background Wedding Portrait: **AI** Bundle". The
  localized titles already omit it. It is a copy/SEO decision, not a
  code-vs-copy contradiction, so it was left alone.
* The "9 minutes" house number appears on the browser-only tool cards
  ("Auto-fills 6 collage layouts in 9 minutes"). It is the site's product
  number, consistent across 13 cards x 11 languages, so it was not touched
  - but for a tool that renders instantly it is arguable.
* `blog.*` and `services.*` still describe the AI video product's face
  detection. That is a server-side capability and cannot be verified from
  this repository, so it stays.

## The cookie banner existed in TWO implementations (2026-11-02)

### What was wrong

`js/main.min.js` built its OWN hard-coded **English** banner with the id
`wa-cookie-banner`. `js/cookie-consent.js` builds the **localized** one with
the SAME id, and it guards on that id already existing:

```js
if (document.getElementById('wa-cookie-banner')) return;   // in render()
```

Every page lists `main.min.js` BEFORE `cookie-consent.js`, and both scripts
are `defer` - so they execute in document order, and the **English** banner
won on all 10 non-English sites. Consequences, proven by replaying the real
load order for all 11 languages:

* the localized dictionary was still FETCHED (`/i18n/cookie/<lang>.json`) and
  then thrown away - one wasted request per first visit;
* the privacy link always pointed at the ENGLISH `/privacy/`;
* the banner read "We use cookies" / "Essential only" / "Accept all" on
  every non-English site.

`tests/cookie-consent-check.cjs` could not see it: it exercised
`js/cookie-consent.js` ALONE. The defect only exists when both scripts run,
in that order.

### The fix

The banner was REMOVED from `js/main.js` and `js/main.min.js` (both - the
build step rewrites `main.js` -> `main.min.js`, so fixing one is not enough).
`js/cookie-consent.js` is now the single source of truth. It is injected on
every page by `functions/_middleware.js` -> `injectCookieConsent()`.

### The lesson

**Two implementations of the same UI can coexist and one can silently win.**
The guard that was supposed to make the second one safe (`if the id exists,
skip`) is exactly what made the LOSS silent: the localized banner was
skipped, not the English one.

A cleanup guard protects whoever runs SECOND. It protects nobody against a
first implementation that should not have existed at all.

### The gate

`tests/cookie-consent-check.cjs` now has a 6th group that replays the REAL
load order (`main.min.js` first, then `cookie-consent.js`) for all 11
languages, and asserts that no second implementation exists in the shared
scripts (comments are stripped before the check, so a comment that merely
names the id does not trip it).

`internal-tools/pre-deploy-check.ps1` step **9f** runs that test (FATAL).
The stub's DOM needed `querySelector`/`querySelectorAll`/`addEventListener`
added, because it had never loaded `main.min.js` before.

### TRAP: a guard is not a licence to have two implementations

The same reasoning applies to any "if it already exists, skip" pattern: check
WHAT is being skipped, not only that something was skipped.

## The `<html>` rewrite only matched the English page (2026-11-02)

The middleware rewrote the document's language attribute with a single
positional pattern:

```js
text.replace(/<html\s+lang="en"\s*>/i, `<html lang="${lang}"${rtl}>`);
```

That matches the **English source** page - the FALLBACK path, where a URL
has no localized twin. But a **localized** Arabic page ships
`<html lang="ar">`, which the pattern does not match. So **57 of the 63
Arabic pages served their first HTML without `dir="rtl"`**; the direction was
only applied later, at runtime, by `js/i18n.js` -> `setDir()`.

The layout was therefore NOT broken for a human reader (the runtime fix plus
`styles/i18n.css`'s `html[dir="rtl"]` rules handled it), but the first HTML
the search engine saw had no direction semantics.

### The fix

The attribute list is now **parsed**, not matched positionally, and `lang` is
forced to the language actually being served. Any attribute order and any
quoting works, and the rewrite is idempotent:

```
<html lang="en">                  ->  <html lang="ar" dir="rtl">
<html lang="ar">                  ->  <html lang="ar" dir="rtl">
<html lang="ar" dir="rtl">        ->  <html lang="ar" dir="rtl">
<html lang="en" class="x">        ->  <html lang="ar" class="x" dir="rtl">
```

`tests/middleware-i18n-check.cjs` now asserts this against the real
middleware for 8 URLs (Arabic localized pages, the Arabic fallback, and
non-Arabic pages that must NOT get a `dir` attribute).

### The lesson

**The same trap as the hreflang block (2026-11-01), one layer up.** A
cleanup/rewrite step that understands only ONE spelling of the markup it
handles silently does nothing on the other spelling - and the result looks
like "there was nothing to fix".

## The gallery social card pointed at a file that did not exist (2026-11-02)

`gallery/index.html` referenced `/images/og-gallery-1200x630.jpg` as its
`og:image`, as its `twitter:image` variant, and as the JSON-LD
`primaryImageOfPage` - but the repo only had `.avif` and `.webp`. The `.jpg`
had never been generated, so the social card was a **404** (live-verified:
HTTP 404 returning the 404 page body).

Every other `og:image` on the site uses `.jpg` (2000 references), and social
platforms handle `.jpg` most reliably, so the file was generated rather than
the reference changed.

### The source image had AI-generated garbled text

The generated `.jpg` came from `og-gallery-1200x630.webp`, and that source
is a crop of `gallery-collage.png` - which carries a **text band** whose
typography is AI-mangled nonsense:

```
"Wedding ej portfolio"
"WEDDING IDEIE"
"A MERIAG CON-AIC CUREIN THE NVITORS"
```

That band was visible on the site's own gallery collage and on the social
card. The card was rebuilt from the collage's photo rows (below the text
band) with a correctly-spelled brand band composed by sharp:

```
WeddingAI.video
WEDDING VIDEO PORTFOLIO```

### The rule

**A social card is published content, not a build artifact.** Before
shipping an `og:image`, look at it. An AI-generated caption that reads as
garbage is a visible brand defect on every share, and a missing file is
worse - the card is simply blank.

### The gate gap

Nothing checked that an `og:image` target exists. `scripts/verify-image-404s.ps1`
exists but did not cover the `og:image` / `twitter:image` references.

## The Russian dictionary is 13.5% of the English one (2026-11-02)

`i18n/ru.json` holds 5,979 keys; `i18n/en.json` holds 44,139 (13.5%).

The consequence is not uniform across the two serving paths:

| path | bound keys | missing in ru | translated |
|---|---|---|---|
| localized page (`/ru/x/` has a twin) | 657 | 54 | 91.8% |
| fallback page (no twin) | 22,197 | **16,660** | **24.9%** |

Live-verified: 32 of the first 40 Russian sitemap URLs still serve an
**English** `<title>`, while the German equivalent is already German. The
`og:locale` says `ru_RU` and the JSON-LD `inLanguage` says `ru-RU`, so the
**metadata claims Russian while the page is English**.

Every other language is at 94.4%-97.6% on the same fallback path.

### What was done (2026-11-02)

The 12 **SEO-critical** keys for the six top-level pages that have no Russian
twin were translated by hand and added to `i18n/ru.json`:

```
gallery / privacy / resources / search / success / terms
  -> title_text + meta_description
```

All 12 are within the house limits (title <= 60, description <= 160). The 6
Russian page titles now render in Cyrillic (verified through the real
middleware).

### What is STILL open

The **~15,200 blog BODY** keys are still missing. The title/description
keys (200) and every core page are DONE - see below.

### The Russian dictionary was 13.5% of the English one (2026-11-02)

`i18n/ru.json` held **5,979 keys** against `i18n/en.json`'s 44,139. The
consequence was not uniform across the two serving paths:

| path | bound keys | missing in ru | translated |
|---|---|---|---|
| localized page (`/ru/x/` has a twin) | 657 | 54 | 91.8% |
| fallback page (no twin) | 22,197 | **16,660** | **24.9%** |

Every other language sits at **94.4%-97.6%** on the same fallback path
(de/es/fr/pt 98.8%, ja/zh/ar/th/hi 97.5%). Russian was the outlier by an
order of magnitude, and it was the ONLY language with **zero** pre-translated
blog files (`de/blog/` has 50, `ru/blog/` has 0).

So the Russian blog pages were never "partly translated" - the corpus simply
did not exist. Live-verified before the fix: 32 of the first 40 Russian
sitemap URLs served an English `<title>`, while `og:locale` already said
`ru_RU` and the JSON-LD `inLanguage` said `ru-RU`. **The metadata claimed
Russian while the page was English.**

### What was translated (2026-11-02)

| target | keys | result |
|---|---|---|
| 100 blog titles + 100 meta descriptions | 200 | 100/100 titles render in Cyrillic |
| 6 top-level pages (gallery, privacy, terms, search, success, resources) | 12 + 120 | 100% |
| order / pricing / about / tools / services | 56 + 41 + 8 + 26 + 7 | 100% |
| shared values (table headers, CTA, competitor cells) | 1,794 | one translation covers up to 138 keys |
| **total** | **~2,400** | `i18n/ru.json` 5,979 -> 8,547 |

**All 12 core pages are now 100% translated**, verified through the real
middleware.

### The highest-leverage move was grouping by ENGLISH VALUE

12,494 of the ~15,200 remaining keys were **unique to one page**, but 117
English VALUES were repeated across up to 138 keys each - the shared table
headers, the CTA buttons, the competitor cells of the SERP comparison
tables. Translating those 117 values once covered **2,438 keys**.

The comparison tables are the clearest case: the `th.*` headers ("Tool",
"Style", "Languages", "Output", "Price", "Workflow") are **identical across
40 pages**, and the `td.<competitor>` cells follow one naming scheme
(`td.style_vidu`, `td.price_pollo`...). Only the per-competitor data
differs.

**A key identifies a source string, not a slot.** Grouping the missing keys
by their English value turns a 15,000-key translation job into a 2,400-key
one - and it is exactly how the other nine languages were built.

### TRAP: do NOT hand-type the i18n keys

The key name comes from the ORIGINAL source text, not from the current
English string. `blog.wedding-video-trends-2026.title_text...` does not
look like the title it holds. Writing the keys by hand produced wrong keys
on the first attempt.

Write a **`slug -> translation` map** and let a script take the real keys
out of the source files. The slug is the key minus its hash suffix, which
is stable and readable.

### TRAP: a slug can map to TWO keys

`resources.li_text.no_contract_always_walk_away` exists twice, with
different hashes and slightly different English ("No contract. Always. Walk
away." vs "No contract - always walk away."). A slug-indexed map silently
picks one. Match on the ENGLISH VALUE when a slug is ambiguous.

### TRAP: check the HTML entities survive the translation

The pricing and gallery tables carry `&amp;`, `&ndash;`, `&mdash;`,
`&ldquo;`, `&rdquo;` inside their values. Translating them and dropping an
entity changes the rendered text (a bare `&` instead of `&amp;`, or a lost
en-dash). Compare the ENGLISH value's entity set with the RU one before
writing.

### TRAP: check the tag skeleton too

Some values carry markup (`<br>`, `<strong>`, a nested `<span>` with its
own `data-i18n`). A translation that drops or reorders a tag breaks the
render, and the key set looks fine. Compare the tag-name sequence of the
EN and the RU value.

### TRAP: an optional marker has no single grammatical gender

`order.label_text.optional` was `(необязательный)` - masculine - but it
follows three labels of different gender (Бюджет / Страна / Ссылка). The
neutral `(необязательно)` is the standard form for such UI markers.

### What is STILL open in Russian

1. **~12,500 blog body keys.** Every Russian blog article now has a Russian
   TITLE and a Russian meta description, but the body text is still
   English. The articles are therefore "Russian headlines over English
   articles" - better than before, but not a finished translation. This
   wants a dedicated pass (it is ~100 full articles of prose).

2. ~~**The `HINTS` table on `/order/` is hard-coded English.**~~ **DONE
   (2026-11-02).** See "The order form no longer downloads a whole
   dictionary" below.

### The 200 blog title/description keys are DONE (2026-11-02, later pass)

All 100 Russian blog pages had **no localized twin at all** (`ru/blog/` has
none), so every one of them was served from the English source with an
English `<title>`. All 200 keys (100 titles + 100 meta descriptions) are now
translated and live.

**Verified: 100/100 Russian blog titles render in Cyrillic** through the real
middleware.

Two things had to be right for that to show up on the live site:

1. the dictionary edit, and
2. the SHARDS - see the two traps below, both of which bit during this pass.

### The order form no longer downloads a whole dictionary (2026-11-02)

`/order/` shows a per-service hint (delivery time + what the service suits).
The inline script used to fetch the **entire per-language dictionary**,
`/i18n/<lang>.json`, to read about a dozen strings:

| visitor | dictionary downloaded | strings needed |
|---|---|---|
| hi | **16.4 MB** | 12 |
| th | 14.3 MB | 12 |
| ar | 12.1 MB | 12 |
| ru | 1.2 MB | 12 |

That is the page that converts. The fix loads the **one namespace shard** that
holds those strings - `i18n/shards/<lang>/pricing.td_text.json`, 3.5-6.3 KB -
a 99.9% reduction.

The same strings were also **hard-coded English**, so the hint read in English
in every language. Ten of the eleven services already had translated
equivalents: the pricing page's own delivery strings
(`pricing.td_text.5ndash7_days` and friends). The "other / not sure yet"
service had none, so it fell back to English everywhere; it now has two new
keys (`pricing.td_text.reply_within_24_hrs`,
`pricing.td_text.not_sure_yet_sofia_recommends`) in all 11 languages.

`price` was always localized - the middleware's currency localizer rewrites
`$9.9` inside the script literal into `$9.9 <span>(≈ EUR9)</span>`.

**The gate**: `tests/order-hint-check.cjs`, wired into the pre-deploy check as
step 9b. It checks statically that no page fetches a whole dictionary, that
every hint key exists in all 11 shards, and behaviourally that the hint
renders translated with an English fallback when the shard cannot be loaded.

Two things the check had to get right:

* **The old URL could be written two ways** - `'/i18n/${lang}.json'` and
  `'/i18n/' + lang + '.json'`. A regex for the first missed the second, and
  the second is what the code actually used. The check now normalises the
  source (strip quotes, glue the string pieces) before matching.
* **A comment that mentions the old path must not fail the gate.** The check
  strips line comments first, keeping `://` intact so absolute URLs are not
  truncated.

### TRAP: a VALUE edit leaves the key set identical, so a key-set check misses it

The incremental shard writer first compared the namespace's keys with the
shard's keys. A **value** edit (shortening a title) does not change the key
set, so the namespace was skipped and the shard kept the OLD value:

```
RESULT: 1 FAILURE(S)  - ru: 24 key(s) have a DIFFERENT value in the shard
                        than in the dictionary (stale shards)
```

The freshness gate caught it - which is exactly what it is for. The fix is to
compare values too:

```python
if set(kv).issuperset(have) and all(have.get(k) == v for k, v in kv.items()):
    continue
```

**A stale shard and a missing key fail identically**: the page returns 200 and
serves the old text. Checking "is the key there" is not enough.

### TRAP: a page BUNDLE is a second copy of the page's keys

The blog hub needs 111 namespaces, over the 40-shard budget, so it is served
from ONE bundle file (`bundle.<hash>.json`) instead of the namespace shards.
A new key on that page therefore has to land in **two** places:

* the namespace shard (`blog.<slug>.json`), and
* the bundle.

Writing only the namespace shard leaves the hub on the old text while the
individual articles are already translated - and the shard gate reports it:

```
- ru: bundle bundle.dfde240c30a6255f.json is missing 189 key(s) the page binds
```

The bundle is keyed by the hash of the page's NAMESPACE SET, and it must also
carry the fixed-name keys the middleware looks up directly (`extra_keys`).
`scripts/add-shards-for-keys.py` now rebuilds both.

### The served title is LONGER than the dictionary value

The static check measures the dictionary value; the live check measures what
the middleware serves. The middleware rewrites every USD price into
`$X <span>(≈ EURY)</span>`, so **a title containing a price grows** - `$9,9`
adds ~17 characters of localised price text.

24 of the 100 Russian titles were over the 60-character budget only AFTER
that rewrite, so the static check passed and the live check failed. The
rewrite that fixed them had to be measured with the live checker's own
`served_title_length()`, not with `len()`.

The practical rule: **a title that carries a price needs ~17 fewer
characters** than one that does not.

### TRAP: a dictionary edit without a shard rebuild serves the OLD text

The shards under `i18n/shards/` are what the middleware reads first. Adding
12 keys to `i18n/ru.json` and shipping without rebuilding the shards would
have left the Russian pages English **with a 200 response** - the change
would have looked like it did nothing.

`qa/build-i18n-shards.py --lang ru` rebuilds the language, but it rewrites
every shard and is slow enough to get interrupted. For a handful of added
keys there is now a narrow alternative:

```
python scripts/add-shards-for-keys.py i18n/ru.json i18n/ru.manifest.json
```

It uses the builder's own `ns_of` rule and its own atomic write, so the
result is byte-identical to a full rebuild, and it leaves complete
namespaces untouched. It is idempotent. Always follow it with
`python scripts/verify-i18n-shards.py` (the gate) - which reported
`0 FAILURE(S), 0 WARNING(S)` for the result.

Note: the shards ARE tracked by git (4,282 files), contrary to what an
older note in this file says.

## A `data-i18n` key resolves only if its NAMESPACE exists (2026-11-10)

**A key is not a key - it is a file.** The middleware files every key under
its **first two dotted segments** (`namespaceOf()` in
`functions/_lib/i18n-shards.js`): `blog.foo.bar.baz` -> namespace
`blog.foo`. The namespace is what the manifest maps to shard files.

A binding needs THREE things, and missing any one of them fails SILENTLY
(the page still returns 200, the translation is simply absent):

1. the key must exist in `i18n/<lang>.json`, or the element keeps its
   static source (`applyDataI18n()` does `if (v == null) return m`),
2. the namespace must be in `i18n/<lang>.manifest.json`, or no shard is
   ever fetched for it,
3. the namespace must exist as a shard file.

**The failure mode that hid for months.** A page was copy-pasted from a
sibling page and its `data-i18n` attributes were rewritten to a namespace
that exists NOWHERE:
`blog.include_remote_family_wedding_video.serp_comparison.*` (underscores)
while every dictionary uses the hyphenated
`blog.include-remote-family-wedding-video.*`. The middleware filed it under
`blog.include_remote_family_wedding_video`, which is not in the manifest,
so no shard was fetched and all 51 elements stayed empty - 6 blank headers,
42 blank cells, an empty heading, in all 11 languages, with no error
anywhere.

**The rule:** a namespace name is part of the data contract. When a page is
copied, copy the `data-i18n` keys verbatim or repoint them at a namespace
that exists. After any rename, check it:

```powershell
python scripts/verify-i18n-shards.py
```

A page with no localized static file is served from the English source and
translated at runtime, so one fix reaches all 11 languages - but only for
those pages. 63 pages per language DO have a hand-written localized file,
and those can drift from the English source (the zh copy of
`blog/best-ai-wedding-video-tools-2026/` has no comparison table at all
while the English one does).

## The CI gate pointed at scripts that did not exist (2026-11-10)

Both GitHub Actions jobs were red on every push since `c7747902` - the
housekeeping commit that deleted 140 one-off QA scripts. The workflows were
never updated:

- `.github/workflows/ci.yml` ran `python qa/verify_sitemap.py` -> deleted,
- `.github/workflows/pre-deploy.yml` ran `python qa/full_qa.py` -> deleted.

Both steps died with "can't open file" (exit 1) before they checked
anything, and nobody noticed because the Cloudflare Pages deploy is a
separate workflow. The surviving production scripts are
`qa/{deploy,gen_sitemap,qa_full_recheck,validate-deploy,validate-sitemap}.py`.

**A deleted script and a workflow that calls it fail in exactly the same
way as a real regression.** Before blaming the change, find out WHICH step
failed: `git log --diff-filter=D -- <path>` says whether the script was
ever there.

`ci.yml` also requires `sitemap.xml` to carry today's (UTC) lastmod, so
every push needs the dates refreshed with
`python scripts/_refresh_sitemap_lastmod.py` (UTC, because the gate compares
against `date -u`, not local time).

## The scratch directory is `.tmp`, not `tmp` (2026-11-10)

`.tmp/` holds ~1,400 backup / one-off HTML files and is gitignored, but the
scripts that walk the tree excluded `tmp` - not `.tmp` - so the scratch
files were counted as site pages:

- `qa/gen_sitemap.py` would have published internal URLs to search engines,
- `qa/full_qa.py` scanned 2,142 files instead of 721 and reported 13,358
  broken hrefs that live in scratch files (CI checks out a clean tree, so
  the two numbers were never comparable).

**A directory whose name starts with a dot is a DIFFERENT directory from
the one without it** - the same trap as `tmp/` vs `.tmp/` documented in
`.assetsignore`. Exclude both.

## The shard builder is not byte-deterministic (2026-11-10)

`qa/build-i18n-shards.py` emits the JSON keys in a different order on every
run (Python's per-process string-hash randomisation), so a rebuild always
shows the 11 blog-hub bundles and the manifests as changed even when
nothing moved. The gate compares SEMANTICALLY ("the shards merged back
equal the dictionary exactly"), so the churn is harmless - but do not
commit it: `git checkout` the bundles and manifests and keep only the
shards whose CONTENT actually changed.

## The 13 free tools: what they really are, and the library shortlist (2026-11-09)

The `/tools/*` suite is **13 tools, all zero-dependency vanilla ES2018**, each page
carrying its own inline `<script>` plus the shared `js/tools/common.js`
(`window.weddingAITool`: `fileToImage`, `canvasToBlob`, `bindDropZone`,
`renderFileList`, `download`, `downloadZip`, `toast`). No build step, no
package.json, no framework. Tool pages are localized into 11 languages through
the normal `data-i18n` bindings, so **any library with its own UI strings is a
localisation liability**.

### Measured gaps (not guesses - read from the pages)

| tool | what it actually does | the gap |
|---|---|---|
| `heic-to-jpg-wedding-photos` | relies on the browser's native decoder | **only Safari decodes HEIC**; Chrome/Edge/Firefox cannot. The page says so honestly. |
| `remove-background-wedding-portrait` | per-pixel RGB distance to a picked backdrop colour + feather band | chroma-key only. The page already states it "needs a full AI semantic segmentor" for real scenes. |
| `crop-wedding-photo-for-reels` | fixed aspect ratios + an off-centre bias heuristic | no drag, no zoom, no rotate, no manual crop |
| `add-text-to-wedding-photo` | 9 preset text positions, auto-shrink | no drag / rotate / free placement |
| `wedding-photo-collage` | 6 fixed grids, photos auto-placed | no reordering, no per-cell drag |
| `wedding-video-invitation-maker` | renders **5 PNG frames** | no MP4 at all (deliberate: ffmpeg.wasm rejected as 30 MB) |
| `wedding-budget-calculator` | table + `Export CSV` + `Print` | no chart, no PDF |
| `wedding-seating-chart-maker` | canvas render + `Export PNG` + `Print` | no drag-drop seats |
| `compress-wedding-photos` | canvas re-encode, jpeg/png/webp | no AVIF, no HEIC input |
| `wedding-photo-book-planner` / `save-the-date-maker` / `wedding-invitation-maker` | canvas render + PNG | no PDF |

**TRAP: `downloadZip()` is not a zip.** `js/tools/common.js` implements "Save all"
as sequential auto-downloads 120 ms apart. Browsers block or spam multiple
downloads; the user gets N loose files, not one archive. A real zip is one
small library away.

**TRAP: the pages claim PDF and there is no PDF.** The comparison tables on
`wedding-photo-collage` ("PNG + PDF + 4K + print + share"),
`wedding-seating-chart-maker` and `wedding-budget-calculator` say PDF, but the
only export buttons are `Download PNG` / `Export PNG` / `Export CSV` / `Print`.
A printer-friendly page can be saved as PDF by hand, but the copy says the tool
offers PDF. Same category of defect as the stale-figure traps elsewhere in this
file - fix the copy or add the button, do not leave the gap.

### The constraints any replacement must respect

- **CSP**: `script-src 'self' 'nonce-…'` plus a few allowlisted origins.
  **No CDN scripts are allowed** - a library must be self-hosted under `/js/`.
  **`'wasm-unsafe-eval'` IS present** in both `functions/_middleware.js`
  `buildCsp()` and `_headers` (added 2026-11-09), so a WebAssembly library
  compiles; `'unsafe-eval'` is still absent, so no `eval()` / `new Function`.
  `worker-src 'self' blob:` is explicit too - `default-src 'self'` does NOT
  cover it, and the vendored libraries build their Worker from a `blob:`
  URL (without it pica silently degrades to its JS resampler).
- **No build step**: a library needs a UMD/global build (or an ESM file loaded
  with `<script type="module">`).
- **11 languages**: a library with visible UI strings needs 11-language
  overrides or it leaks English.
- **No price on a tool page** (see the tools section above) - this also rules
  out any "free tier / upgrade" UI a library might ship.

### Verified library shortlist (checked 2026-11-09 against the npm registry)

| library | version / last publish | license | shipped size | wasm? | verdict |
|---|---|---|---|---|---|
| `heic2any` | 0.0.4, 2023-03 (stale) | MIT | 1.32 MB | **no - asm.js** | **use it.** The only HEIC decoder that passes the current CSP untouched. Vendor it, freeze the version, accept no-EXIF and no-animation limits. |
| `libheif-js` | 1.23.5, 2026-10 (alive) | **LGPL-3.0** | 1.4 MB wasm + 2 MB glue | yes | not directly - LGPL + raw C API. Use heic2any's MIT-wrapped copy. |
| `cropperjs` | 2.3.1, 2026-10 (alive) | MIT | 50 KB UMD | no | **yes, for the crop tool.** Verified zero user-facing strings. v2 is a Web-Components/shadow-DOM rewrite - the v1 API (`getCroppedCanvas`) is gone, so write new code. |
| `fflate` | 0.8.3, 2026-07 (alive) | MIT | 32 KB UMD | no | **yes, to make `downloadZip` a real zip.** |
| `jspdf` | 4.2.1, 2026-03 (alive) | MIT | 410 KB UMD | no | **yes, for the missing PDF export.** `addImage` with `image/png` verified in the shipped bundle. |
| `modern-screenshot` | 4.7.0, 2026-04 (alive) | MIT | 29 KB UMD | no | **yes, for DOM -> PNG** (replaces hand-written canvas renderers). |
| `pica` | 10.0.3, 2026-08 (alive) | MIT | 53 KB | wasm inlined | only with `wasm-unsafe-eval`; without it it silently falls back to the JS resampler. |
| `mediabunny` | 1.65.2, 2026-11 (alive) | MPL-2.0 | 706 KB **ESM only** | no (WebCodecs) | right library for the video tool, wrong phase: no UMD build, and WebCodecs `VideoEncoder` is missing on Firefox for Android. |
| `@imgly/background-removal` | 1.7.0 | **AGPL-3.0** | lib 167 KB + ORT wasm 11 MB + model ~44 MB | yes | **no.** Copyleft, ~45 MB, needs `wasm-unsafe-eval`. See below. |
| `@huggingface/transformers` | 4.3.2, 2026-10 (alive) | Apache-2.0 | 574 KB + ORT wasm | yes | only if AI background removal is a product requirement; RMBG-1.4 q8 is ~42 MB and can be **self-hosted** (`env.allowRemoteModels=false`). |
| `pdf-lib` | 1.17.1, 2021-11 (abandoned) | MIT | 513 KB | no | no - dead and bigger than jsPDF. |
| `browser-image-compression` | 2.0.2, 2023-03 (abandoned) | MIT | 56 KB | no | no - dead; the canvas + quality loop is ~20 lines. |
| `fabric` / `konva` | 7.4.0 / 10.9.1 (alive) | MIT | 292 KB / 193 KB | no | not yet - right for a future drag-and-drop sticker/collage editor, wrong for this pass. |

### TRAP: the search results lie about `@imgly/background-removal`'s license

Several 2026 blog posts and search snippets call it **MIT** ("the library is
MIT-licensed"). Its own `LICENSE.md` inside the published package is the full
**GNU AGPL-3.0** text, and `npm view` reports the license field as
`SEE LICENSE IN LICENSE.md` - which is itself the tell. Do not let a search
snippet decide a commercial site's dependency. Verify from
`https://cdn.jsdelivr.net/npm/<pkg>@<ver>/LICENSE.md`.

### The chart question has a 0-byte answer

For the budget calculator's breakdown, do **not** pull in Chart.js (205 KB, and
its tooltip/legend/axis defaults are English - 11 languages of overrides) or
ECharts (1.07 MB). An inline SVG or a `conic-gradient` pie is 0 KB, needs no
CSP change, and takes its labels straight from the existing `i18n/*.json`
dictionary.

### If the tool pages gain new UI strings

They are localized through the normal `data-i18n` path, so the **shards must be
rebuilt** - `scripts/verify-i18n-shards.py` is a fatal gate (pre-deploy step
9d). For a handful of new keys use
`python scripts/add-shards-for-keys.py i18n/<lang>.json i18n/<lang>.manifest.json`
(atomic, idempotent, byte-identical to a full rebuild), then run the verifier.

## The tool suite was rebuilt on 2026-11-09: the English page is now the single source of truth

The audit section above (2026-11-09, "The 13 free tools") described what the
tools could not do. That same day the fixes were implemented. This section
records the architecture that resulted, because three of the rules are now
load-bearing and a future edit that breaks one of them fails SILENTLY.

### 44 of the 144 tool pages were DEAD, and the page still returned 200

The localized copies of the tool pages carry a MACHINE-TRANSLATED copy of
the English page's JavaScript. The translator translated the CODE, not only
the strings:

    de/tools/add-text-to-wedding-photo/index.html
      226:  Funktion addFiles(picked) {        <- "function" translated
      227:    var hinzugefügt = 0;             <- "added" translated

A SyntaxError kills the WHOLE inline script, so the drop zone, the buttons
and the file list were inert - while the page rendered perfectly and
returned 200. Measured: 44 of 144 tool pages broken (every localized copy of
add-text / compress / crop / heic / remove-background in es, fr, de, ar, th,
hi; ALL ten localized budget calculators; three photo-book planners; the
French seating chart). `ru/tools/heic-to-jpg-wedding-photos` had no script
at all.

**THE RULE: the English tool page owns the behaviour; the localized copies
own only the prose.** `scripts/propagate-tool-js.py` copies the English
inline script into the ten localized copies byte-for-byte. Run it after
ANY change to an English tool page's script, before the syntax gate.

    python scripts/propagate-tool-js.py --dry-run
    python scripts/propagate-tool-js.py
    python scripts/check-tool-script-syntax.py     # 286 scripts, 0 broken

`check-tool-script-syntax.py` runs `node --check` on every inline script of
every tool page and exits 1 on the first broken one. It is the gate that
would have caught this in the first place.

The price of the rule: a hardcoded English string in a localized copy's
script comes back in English. That is why every runtime string now goes
through `window.weddingAITool.t('alias', 'English fallback', params)`.

### Runtime strings: `t()` and the injected dictionary

`functions/_middleware.js` injects the `tools.copy` namespace into the page
as `window.__WA_I18N__` (tool pages only). `js/tools/common.js` exposes
`t(alias, fallback, params)`:

* `alias` -> a key in the `tools.copy` namespace (the COPY alias table in
  common.js maps the short alias to the full dotted key);
* `fallback` -> the English text, used on an English page or if the
  injection failed;
* `params` -> optional `{name: value}` map; `{n}` in the result is
  replaced (both in the translated string and in the fallback).

A static label still uses `data-i18n`; only strings produced AFTER the page
has loaded (toasts, per-file buttons, canvas titles) need `t()`.

### The CSP now carries TWO new keywords, and one of them is easy to miss

`functions/_middleware.js` `buildCsp()` AND `_headers` both carry:

    'wasm-unsafe-eval'      WebAssembly compilation (pica, ONNX Runtime)
    worker-src 'self' blob:  the vendored libraries' worker pools

**TRAP: pica AND heic2any both create their Worker from a blob: URL.**
`new Worker(URL.createObjectURL(new Blob([...])))`. Without `worker-src`,
`worker-src` falls back to `default-src 'self'`, which does not allow
`blob:` - so the Worker is blocked. pica does NOT crash: `has_wasm()`
returns false and it silently falls back to its plain-JS resampler, i.e.
the page keeps working and the quality quietly drops. heic2any's decoder
fails the same way. Both keyword changes must stay in BOTH files.

### The vendored libraries

`scripts/vendor-libs.py` pins every third-party file to an exact version,
downloads it, writes the upstream LICENSE beside it, and records the URL +
SHA-256 + byte size in `js/vendor/vendor-manifest.json`. `--verify` fails on
any drift. The `?v=` stamp in the URL must equal the manifest's version.

| library | why | licence |
|---|---|---|
| fflate 0.8.3 | real ZIP for "Save all" | MIT |
| jspdf 4.2.1 | real PDF export | MIT |
| heic2any 0.0.4 | HEIC decode outside Safari (asm.js, no WASM) | MIT |
| pica 10.0.3 | proper multi-step resample (WASM) | MIT |
| onnxruntime-web 1.22.0 | runs MODNet on the device | MIT |
| Xenova/modnet (quantized ONNX) | the matting model | Apache-2.0 |

**TRAP: `ort.min.js` is the JSEP build.** Its WASM backend is
`ort-wasm-simd-threaded.jsep.wasm` - **21.4 MB**. `ort.wasm.min.js` (47 KB)
is the WASM-only build and its backend is `ort-wasm-simd-threaded.wasm` -
**10.9 MB**. The site ships the second one. The runtime finds its backend
and its `.wasm` through `ort.env.wasm.wasmPaths = '/js/vendor/onnxruntime/'`,
because there is no CDN and no bundler.

**TRAP: the site is not cross-origin isolated**, so `SharedArrayBuffer` is
unavailable and the threaded build would fail. `ort.env.wasm.numThreads = 1`
is required, not optional. **This is deliberate and must stay that way:**
adding `Cross-Origin-Opener-Policy` / `Cross-Origin-Embedder-Policy` would
kill the AdSense ad frame and the Clarity collector — see "COOP/COEP is
CLOSED on this site" further down.

### MODNet: what the browser actually has to do

The model is `js/vendor/modnet/model_quantized.onnx` (6.3 MB quantized;
the full-precision one is 24.7 MB). Verified with `onnxruntime` on the CPU
AND end-to-end in Chromium under the production CSP:

* graph input name `input`, output name `output`;
* input shape `[1, 3, 512, 512]` float32, output `[1, 1, 512, 512]` in
  `[0, 1]`;
* preprocessing: resize to **512x512 WITHOUT keeping the aspect ratio**
  (this is MODNet's own reference behaviour), then
  `(x / 255 - 0.5) / 0.5` into NCHW;
* the matte becomes the alpha channel via
  `globalCompositeOperation = 'destination-in'`.

Total first-run download: ~11 MB runtime + 6.3 MB model = **~17 MB**, from
this origin, once, then cached by the browser. Nothing is uploaded.

The colour key stays the DEFAULT so that nobody gets a surprise 17 MB
download; AI matting is one dropdown away and says what it costs.

### The crop frame is native, and cropper.js v2 was rejected on purpose

Cropper.js v2 is a Web Components rewrite: the UI lives in shadow DOM, the
package ships NO stylesheet, and the bundle contains ZERO
aria-label / Reset / Confirm / Cancel strings. Its drag handles would have
no accessible name and could not be translated into 11 languages. The frame
is therefore a canvas + a shaded overlay + four corner handles + Pointer
Events: zero extra bytes, fully localizable, mouse/touch/pen alike.
`touch-action: none` on the canvas is REQUIRED - without it the phone
scrolls the page instead of dragging the frame.

### Verification harness: serve with the LIVE CSP, then drive the page

A tool feature that needs a browser, a WASM runtime and a 17 MB model
cannot be checked by reading the code. `scripts/verify-ai-background.py`
and `scripts/verify-crop-stage.py` serve the repository over HTTP with the
**exact Content-Security-Policy from `_headers`** (with a nonce injected
into the inline scripts, exactly like `injectScriptNonce()` does), drive the
page with Playwright, and assert that the assets were fetched from
`/js/vendor/` and that the console carries no CSP violation.

**TRAP when writing such a harness:** only the SCRIPT directive is
nonce-based. `style-src 'self' 'unsafe-inline'` must keep `unsafe-inline`
(the pages use `style=""` attributes). Replacing every `'unsafe-inline'`
in the policy invents violations the production site does not have.

**TRAP: the harness must do BOTH halves of what the middleware does.**
`injectScriptNonce()` adds the nonce attribute to every `<script>`, and the
middleware ALSO replaces the literal placeholder `__CSP_NONCE__` in the
HTML with the real nonce. A harness that only adds the attribute leaves
the literal string in the page, the browser refuses every script that
carries it, and the harness reports three CSP violations that the
production site does not have. Both halves:

```python
html = SCRIPT_RE.sub(lambda m: m.group(1) + m.group(2) + ' nonce="%s"' % NONCE + ">", html)
html = html.replace("__CSP_NONCE__", NONCE)
```

**TRAP: `page.wait_for_function("...")` with a STRING is blocked by the
live CSP.** Playwright evaluates a string expression with `eval`, and the
policy has no `'unsafe-eval'` — the browser refuses it and the harness
reports a *page error* that looks like a product bug. Pass a real
function, or use a CSS selector (`page.wait_for_selector("#btn:not([disabled])")`).
`page.evaluate(<function>)` is fine: it goes through the debugger
protocol, not `eval`.

### Small traps that cost real time

* `pathlib.Path.rglob("*.html")` walks `.git` too. On this machine that
  turned a 2-second cache-version bump into a 15-minute one (21 s of CPU in
  14 min of wall clock - blocked on directory I/O, not computing).
  `scripts/bump_cache_version.py` now uses `os.scandir` with explicit
  pruning.
* The cache stamp `?v=` is two-part on the old site assets (`3.21`) and
  three-part on the tool assets (`1.0.1`). The bump helper handles both.
* `scripts/add-tool-ui-keys.py` validates the key shape with a regex. The
  per-tool namespace IS the tool's SLUG, so it contains hyphens:
  `tools.wedding-seating-chart-maker.td_text.<name>.<hash>`. A regex that
  forbids hyphens refuses to update half the site.
* `tools.copy` values are looked up by the FULL dotted key. The alias table
  in `js/tools/common.js` is what makes `t('seatSavedPng', ...)` work.
* Machine translation does not preserve brand names either: the Hindi copy
  of the HEIC page writes "Safari" as **सफ़ारी**. Never match a
  localized page on an English word - match on the structure (ids, CSS
  classes, the `<summary>` of the right `<details>`).
* The Russian tool pages are an OLDER REVISION than the English ones
  (691 lines vs 710, five FAQ questions instead of six). A patch that
  assumes the same structure fails there; identify the blocks by ROLE, not
  by position.

## fileToImage() returns an ImageBitmap now, and that changed a CONTRACT (2026-11-09)

§2.6 / §2.7 replaced the object-URL `<img>` with
`createImageBitmap(file, { imageOrientation: 'from-image' })`. The return
value changed shape:

| field | before | now |
|---|---|---|
| `loaded.img` | `HTMLImageElement` | `ImageBitmap` |
| `loaded.url` | the object URL | **`null`** |
| `loaded.release` | did not exist | closes the bitmap / revokes the URL |

Three consequences, and **all three are silent** - the page returns 200,
the row turns green, and nothing complains:

1. **An ImageBitmap has no `.complete`.** `if (entry.img && entry.img.complete)`
   is always false, so the collage decoded every file again on every run.
2. **`URL.revokeObjectURL(null)` is a no-op.** A tool that still revokes
   `loaded.url` neither throws nor frees anything - the bitmap stays on
   the GPU until the tab dies. The single teardown call is now
   `window.weddingAITool.releaseImage(loaded)`.
3. **`img.src` no longer exists.** The three "one photo" makers stored
   `res.img._objectUrl = res.url`; with `res.url === null` that revoked
   nothing. They now store `res.img._release = res.release`.

`naturalWidth` / `naturalHeight` are MIRRORED onto the bitmap by
`fileToImage()` so the tools that read them did not have to change - but
`img.src` cannot be mirrored, and the `.complete` check had to go.

**A contract change like this needs a SMOKE TEST over every caller.**
`scripts/verify-tool-suite-smoke.py` drives all seven tools that decode a
file through `fileToImage()` and requires the row to reach `done`, the
console to stay clean, and the canvas to actually have pixels in it (a
broken `naturalWidth` draws nothing). Note the collage needs TWO photos
before its build button unlocks - that is the tool's own rule
(`runBtn.disabled = files.length < 2`), not a regression.

### The EXIF orientation is explicit, and `<img>` was already right

Measured in Chromium with a 200x100 JPEG tagged Orientation=6
(`scripts/verify-exif-orientation.py`):

| path | result |
|---|---|
| `<img>` | 100x200 (rotated) |
| `createImageBitmap(blob)` | 100x200 (rotated, in this browser) |
| `createImageBitmap(blob, {imageOrientation: 'from-image'})` | 100x200 (rotated, ALWAYS) |

The `<img>` path has applied the EXIF orientation since Chrome 81 /
Safari 13.1 / Firefox 26, so the OLD code was already correct - but
`createImageBitmap` did NOT reliably, and an early implementation would
have turned a portrait phone photo sideways. The explicit option is the
only guaranteed one, and it is why the loader changed at all.

### The pixel loop runs in a Worker, and the fallback is INVISIBLE

`js/tools/pixel-worker.js` runs the per-pixel colour-key loop off the main
thread; the pixel buffer is TRANSFERRED in both directions, and the worker
reports progress in chunks (~24 updates per image).

**TRAP: if the Worker cannot start, the tool STILL WORKS.** The fallback
runs the identical maths on the main thread - the output is byte-for-byte
the same, the row still turns green, and the tab still freezes. Nothing in
the UI says which path ran. The only evidence is the network log: a
request for `/js/tools/pixel-worker.js?v=...`.

So `scripts/verify-worker-progress.py` asserts three things SEPARATELY:
the worker's OUTPUT equals the main-thread maths (byte for byte, in both
`png` and `jpg` mode), the worker WAS fetched, and the progress bar
appeared. Asserting only the output would pass with the worker disabled.

The worker's cache stamp lives in `js/tools/common.js`
(`PIXEL_WORKER_VERSION`), **not in the HTML**: the `?v=` stamps in the HTML
do not reach a URL that is built at runtime. `bump_cache_version.py`
therefore grew a second list (`JS_ASSETS`) for stamps that live inside a
JS file. Cloudflare Pages overrides Cache-Control on static assets, so a
stale stamp serves the OLD worker forever - the same trap as the vendor
libraries, one level deeper.

### Every decoded image is released, including on the error path

`releaseImage(loaded)` is the single teardown call. The release used to
sit at the END of the `try` block, so an exception skipped it and the
decoded image stayed alive for the rest of the session - a batch of 12 MP
photos is enough to kill a tab. The release now sits in a `finally`.

Cached decodes (the collage's `entry.img`, add-text's `entry.img`, the
crop stage's `entry.stageImg`) are released when the entry is removed or
the list is cleared. `add-text` is the one tool that must NOT release its
`loaded` right after decoding: the bitmap IS the preview, and the row
reuses it.

### The progress bar is real, and it is data-driven

`common.js` renders a `.wa-tool-progress` bar ONLY while the row is in the
`working` state AND `state.percent` is a number; the tools set
`entry.percent` at each stage. A row that never sets it shows no bar at
all - so "the progress bar exists in the stylesheet" proves nothing. The
test drives a real run and watches the DOM for the bar.

heic2any reports 0..1 while it decodes, so the HEIC tool shows a real
bar; Safari's native decode is instant and shows none.

## The video tool exports a real MP4 now, and the 1080×1920 PNG was the WRONG PICTURE (2026-11-11)

Two things happened to `tools/wedding-video-invitation-maker` on 2026-11-11,
and the first one was a bug that had been shipping all along.

### The "1080×1920 frames" were the right pixel count and the wrong picture

`renderFrameAt()` lays everything out in a **540×960 DESIGN space** with
absolute pixel coordinates (`fillText(..., 360)`, `font = '18px ...'`,
`BASE_H - 60`). The PNG export set `BASE_W = 1080; BASE_H = 1920` and
re-rendered — which drew the 540×960 layout into the **top-left quarter**
of a 1080×1920 canvas. The file was 1080×1920 pixels and the design
occupied a quarter of it, in a different place than the preview the user
had just designed. The code even admitted it in a comment ("this may look
slightly blurry on text but is acceptable for v1", "Better: write a
scaled-down version of renderFrameAt()").

The fix is a `ctx.scale()` at the top of `renderFrameAt()` and a
`ctx.restore()` at the end: the design stays in 540×960 units and is
scaled to whatever canvas it is rendered into. `scripts/verify-mp4-export.py`
proves it by comparing the exported PNG against the on-screen preview —
the mean absolute difference has to stay under 12/255 (measured: **0.33**).

**The lesson: "the output has the right dimensions" is not "the output is
right".** A size assertion cannot catch a layout bug. Compare the export
against the thing the user was looking at.

### The MP4: mediabunny, ESM-only, loaded on demand

mediabunny 1.65.2 (MPL-2.0) has **no UMD/global build** — it is ESM only.
So it cannot be loaded the way the other vendored libraries are
(`<script src>` + `window.global`). It needs `<script type="module">`.

`js/tools/movie-loader.js` is that module, and it is tiny. The 706 KB
encoder sits behind a **dynamic `import()`**, so a visitor who only wants
the PNG frames never downloads it — the same "fetch it on first use" rule
the other vendored libraries follow.

`dynamic import()` is the one ES2020 feature in the repository. It lives
in that one `.js` module file, NOT in a tool page's inline script, so the
"no ES2020 syntax in the inline scripts" rule still holds where it
matters. `window.weddingAIMovie` is the public surface.

**TRAP: a module script is DEFERRED, so it runs AFTER a classic inline
script.** The inline script cannot assume `window.weddingAIMovie` exists
at load time. The loader dispatches a `weddingai-movie-ready` event and the
tool waits for it.

**TRAP: the MP4 needs an H.264 encoder, and not every browser has one.**
The button is only offered where `window.VideoEncoder` exists, and the
codec is confirmed on click with `canEncodeVideo('avc')`. **No browser
loses a feature**: a browser without an encoder keeps the PNG sequence it
has always had. That is why §9.4 (Firefox/Android) never became a
blocking question — the answer is "nobody loses anything".

**TRAP: the PNG export fires FIVE downloads in a row.** A Playwright
`expect_download()` after clicking the PNG button catches whichever
download is in flight — so a test that then clicks "Download MP4" can
capture a PNG and report "the MP4 is not an MP4". The test has to take
the MP4 FIRST.

**TRAP: the bundled Playwright Chromium has NO H.264 encoder.** Measured
2026-11-11 on a secure origin:

| browser | `VideoEncoder` | H.264 encode | VP9 |
|---|---|---|---|
| Playwright's Chromium | yes | **no** (every level) | yes |
| installed Chrome | yes | yes, **level 4.0 and up** | yes |
| installed Edge | yes | yes, **level 4.0 and up** | yes |

Two consequences:

* A test of the MP4 path has to run in the **installed Chrome**
  (`p.chromium.launch(channel="chrome")`), not the bundled Chromium.
* **H.264 level 3.1 does not fit 1080×1920.** `avc1.42001f` is rejected
  by Chrome with "not supported" even though the same browser encodes
  `avc1.420028` (level 4.0) happily. The native probe in the tool asks
  for `avc1.420028` on purpose.

The probe is `VideoEncoder.isConfigSupported()` — a NATIVE call, so
checking whether the browser can produce an MP4 costs nothing and does
not fetch the 706 KB encoder. That is what makes the feature safe to
offer: **a browser without an H.264 encoder keeps the PNG sequence it
has always had**, so §9.4 (Firefox/Android) never became a blocking
question.

### The frame interpolation

`renderFrameAt()` takes `frame` as a number, and `p = frame / 4`. The MP4
export passes a **fractional** frame — `(i / 149) * 4` for the 150 frames
of a 5-second 30 fps clip — so the motion between the five key frames is
interpolated instead of stepped. The five PNG frames stay stepped; that
is the difference between a sequence and a video.

The MP4 is read back with **mediabunny itself** (it runs in Node too) by
`scripts/verify-mp4-export.py`: the duration has to be 4–6 s and the frame
1080×1920. On Windows an absolute path is not a valid ESM specifier — it
has to be a `file://` URL (`Path.as_uri()`).

## The compressor now has a target-size mode and keeps EXIF (§2.13 / §2.14, 2026-11-11)

`tools/compress-wedding-photos` gained two controls in all 11 languages:

* `#target-size` — a number input in MB, `0 = off`. When it is set the
  quality slider is ignored and the tool searches for the **highest
  quality that still fits under the target** (binary search, LO 0.3 /
  HI 0.95, 7 rounds). When even the lowest quality is too big the canvas
  is scaled by `sqrt(target / size)` and the search runs again (max 5
  rounds). PNG does not participate — it is lossless.
* `#keep-exif` — a checkbox, on by default. The APP1 (Exif) segment of
  the ORIGINAL file is copied verbatim into the re-encoded JPEG, right
  after its SOI marker. No library is needed for this.

`scripts/verify-compress-target-exif.py` proves both promises on the
produced file, not on the code:

| scenario | input | what is asserted |
|---|---|---|
| A | 200×100 JPEG tagged **Orientation=6** | the output frame is **100×200** (upright) AND it still has an APP1 whose Orientation reads **1** |
| B | 1600×1200 noise JPEG, target 50 KB | the output is **≤ 52428 bytes** and still decodes (measured: 51964 bytes, downscaled to 524×393) |

### TRAP: `ArrayBuffer` has no `.length` — it has `.byteLength`

The EXIF splice builds the output by hand:

```js
var out = new Uint8Array(buf.length + seg.length);   // WRONG
out.set(new Uint8Array(buf), 0);
```

`buf` is an **ArrayBuffer**, so `buf.length` is `undefined`.
`undefined + seg.length` is `NaN`, `new Uint8Array(NaN)` is a
**zero-length** array, and the `set()` then throws
`RangeError: offset is out of bounds`.

The fix is `buf.byteLength`. The general rule: **a typed array has
`length`, an ArrayBuffer has `byteLength`**, and mixing them fails
silently until the `set()` blows up.

### TRAP: a caught error ends the row in `error` — which looks exactly like "still working"

The compressor catches the failure and sets `entry.status = 'error'`.
A test that waits for `.wa-tool-status-done` therefore waits the FULL
timeout on a row that already failed — and a failed run and a slow run
are indistinguishable from the outside.

**Wait for both states and then assert which one it is:**

```python
page.wait_for_selector(".wa-tool-status-done, .wa-tool-status-error", timeout=120000)
cls = page.evaluate("() => document.querySelector('#file-list .wa-tool-file-row').className")
if "wa-tool-status-done" not in cls: fail(cls)
```

### TRAP: the i18n dictionaries are FLAT, and `data-i18n-attr` prefixes must be stripped

`i18n/<lang>.json` is **not** nested. The top-level key IS the whole
dotted path:

```json
"tools.compress-wedding-photos.label_text.target_size.5x7y9z1": "Target size (MB) — optional"
```

So `data["tools"]["compress-wedding-photos"]` is `{}` (or does not
exist) and a lookup that walks the path segment by segment reports
**every** key as missing. The `tools` key that does exist is the tools
HUB page's namespace (`tools.a_text.*`, `tools.h3_text.*`,
`tools.p_text.*`) — a different thing with the same prefix.

`data-i18n-attr="title:about.a_text.couples_served_title.ddddddd3"`
carries an **attribute prefix**; the dictionary key is everything after
the first colon. Strip it before looking up, or the key looks missing.

### How to tell a NEW i18n gap from an OLD one

Compare three things, not two: the page's key set at HEAD vs now, and
the dictionary at HEAD vs now. A key is **newly broken** only when the
page now uses it AND neither the current nor the HEAD dictionary had it.
On 2026-11-11 that check found **0** newly broken keys and **11**
pre-existing gaps (2 in zh, 5 in ru, 4 in hi — all in the compressor's
comparison table), which were filled in the same pass.

Do NOT audit the union of the 11 pages against one dictionary: a key
used only by the `hi` page is reported missing in `en`, which is noise.

### Run the verification scripts with `python -u`

A verification script that hangs produces **no output at all** when
stdout is block-buffered into a pipe — a hung script and a slow script
look identical. `python -u scripts/verify-compress-target-exif.py`
flushes every line, so the last line printed tells you where it stopped.

## The browser cannot encode AVIF, and Safari cannot encode WebP (2026-11-11)

§2.12 added AVIF and lossless-WebP output to the compress tool. Getting
there required measuring what the Canvas API actually does, and two of
the answers were surprises.

### The Canvas API returns a PNG when you ask for a format it cannot make

Measured 2026-11-11 on the bundled Chromium, the installed Chrome and
the installed Edge, all on a secure origin:

| call | result |
|---|---|
| `toBlob(c, 'image/avif')` | a blob whose `.type` is **`image/png`** — PNG bytes, no error |
| `toBlob(c, 'image/webp')` (Safari/WebKit) | a blob whose `.type` is **`image/png`** — PNG bytes, no error |
| `toBlob(c, 'image/webp', 1.0)` | a real **lossless** WebP (`VP8L` chunk, pixel-exact) |

So **no browser encodes AVIF through the Canvas API**, and **WebKit
cannot write WebP at all**. In both cases the browser does not fail — it
quietly hands back PNG bytes.

Two rules follow:

* **A format probe must check `blob.type`, not "did I get a blob".**
  Asking for a blob and getting one back proves nothing.
* **The file name must match the bytes.** The compress tool used to write
  whatever `toBlob` returned under a `.webp` name, so a Safari visitor
  received **a PNG wearing a .webp extension**. The tool now probes the
  browser at startup, offers only the formats the browser can really
  produce, and every encode re-checks `blob.type` and falls back to JPG
  honestly if it ever mismatches.

### The browser's own WebP at quality 1.0 IS lossless

Chromium and Firefox switch to the lossless VP8L encoder at quality 1.
Measured on per-pixel noise (the only fixture that can tell lossless
from lossy — a smooth synthetic image can come out of a lossy encoder
pixel-identical):

| quality | size | worst channel delta |
|---|---|---|
| 1.0 | 21340 bytes | **0** (pixel-exact, `VP8L` chunk) |
| 0.8 | 5660 bytes | > 0 (lossy) |

So lossless WebP needs **no second encoder** — the first plan (a
libwebp WASM build, 320 KB) was dropped in favour of the browser's own.
The one that stayed is AVIF, because no browser can do that.

### A bare specifier needs an import map, and the nonce covers it

`@jsquash/avif`'s `encode.js` imports the **bare specifier**
`wasm-feature-detect`. A bare specifier only resolves through an import
map:

```html
<script type="importmap">{"imports":{"wasm-feature-detect":"/js/vendor/jsquash-wfd-1.2.11/index.js"}}</script>
<script type="module" src="/js/tools/image-codecs.js?v=1.0.0"></script>
```

The map has to come **before** any module script. The middleware's
`injectScriptNonce()` adds a nonce to **every** `<script>` opening tag —
`type="importmap"` included — so the inline map passes
`script-src 'self' 'nonce-…'`.

### TRAP: wasm-feature-detect 1.10.0 is a syntax error in every browser

The current `wasm-feature-detect@1.10.0` ships an `import.source(...)`
call (the import-source proposal). That is a **parse error** in every
browser that does not implement the proposal, so the whole module fails
to load and the encoder package that imports it fails with
`Unexpected identifier 'source'`.

**Pinned to 1.2.11** — the version jsquash itself declares (`^1.2.11`),
and clean. When a vendored dependency is "the latest", check that its
newest release still parses in the browsers you target.

### The vendored encoder lives in a VERSIONED directory

The emscripten glue loads its `.wasm` through a **relative** URL, and a
relative URL carries no `?v=` stamp — so only a version change in the
**path** busts the cache. The vendored packages therefore live in
`js/vendor/jsquash-avif-2.1.1/` and `js/vendor/jsquash-wfd-1.2.11/`, and
`scripts/vendor-libs.py` pins them under those names.

### The i18n dictionaries are FLAT, and `data-i18n-attr` prefixes must be stripped

`i18n/<lang>.json` is **not** nested. The top-level key IS the whole
dotted path:

```json
"tools.compress-wedding-photos.option_text.b6c7d8e9": "AVIF (smallest files — downloads a 3.4 MB encoder once)"
```

So `data["tools"]["compress-wedding-photos"]` is `{}` (or does not
exist) and a lookup that walks the path segment by segment reports
**every** key as missing. The `tools` key that does exist is the tools
HUB page's namespace (`tools.a_text.*`, `tools.h3_text.*`,
`tools.p_text.*`) — a different thing with the same prefix.

`data-i18n-attr="title:about.a_text.couples_served_title.ddddddd3"`
carries an **attribute prefix**; the dictionary key is everything after
the first colon. Strip it before looking up, or the key looks missing.

### The format control was in THREE different states across the 11 languages

Before this pass the output-format `<select>` was:

* **en / zh / pt / ru** — not bound to the dictionary at all; the
  inline `<option>` text was correct for that language but hard-coded.
* **es / fr / de / ja / ar / th / hi** — bound with `data-i18n`, but the
  **inline text was Chinese on every one of them** (the machine
  translation had rewritten the markup). The page rendered correctly
  only because the middleware replaced the Chinese with the dictionary
  value; if the shard ever failed to load, a German visitor would have
  read "输出格式".
* the `<label for="format">` was bound in seven languages and not in
  four, with the same Chinese-inline-text defect.

Now every page carries the **same English source text** plus a
`data-i18n` key, and every dictionary carries the translation. The
static fallback is the English source, the rendered page is the
visitor's language, and the two can no longer drift.

### Verified on the bytes

`scripts/verify-avif-lossless.py` proves the claims on the produced
files, not on the absence of an error:

* the browser's WebP at quality 1.0 carries a `VP8L` chunk and decodes
  back pixel-for-pixel (worst channel delta 0 on per-pixel noise);
* the browser's WebP at quality 0.8 does **not** (the contrast, so the
  first test proves something);
* the AVIF file's magic number is `ftypavif` and it decodes back to the
  right size — and it is **60 % smaller** than the browser's own JPEG at
  a comparable quality;
* asking the browser for AVIF natively returns **PNG bytes**, which is
  why the encoder exists at all;
* end to end through the tool: the AVIF run downloads a real AVIF and
  the lossless-WebP run downloads a real lossless WebP, and **the file
  name matches the bytes**.

## The album's photo order was a race, not a list (2026-11-12)

`addPhotos()` in `tools/wedding-photo-book-planner/index.html` pushed each
photo onto `state.photos` **inside `FileReader.onload`**. The readers run in
parallel, so the library ended up in **completion order, not the order the
visitor picked** - two photos could swap places depending on how fast the
disk answered.

This was found by the placement verifier itself: one run reported "slot 0
shows [40, 200, 60], expected (220, 40, 40)" and the next run passed. The
two colours were exactly swapped, which is the signature of the order race
and not of a coordinate problem.

The fix reads every file into a slot **per input index** and appends the
array once all readers have finished. The library now matches the pick
order every time.

**The rule: an async fan-out that produces a USER-VISIBLE ORDER must
collect into an indexed array, not push into the live list from the
callback.** The same shape appears in the other tools that accept multiple
files; check them before trusting their order.

## The site's fonts are self-hosted OFL files now (§2.16, 2026-11-12)

### What was wrong

`styles.css` declared `--font-heading: 'Playfair Display', Georgia, serif`
and `--font-body: 'Inter', ...`, and the three design templates named
'Great Vibes' and 'Montserrat' in their `fontStack`s. **None of them ever
loaded**: there was no `@font-face`, no font file and no Google Fonts
`<link>`, and the CSP's `font-src 'self' data:` never allowed Google Fonts
either. Every name fell through to the next entry in the stack.

So the site has been rendering Georgia + the system sans-serif since the
day it launched, and the tools that draw text onto a canvas hard-code
`Georgia, serif` for exactly that reason.

### What is there now

`/fonts/<family>-5.3.0/` holds 13 woff2 files + each family's OFL
LICENSE (the licence has to travel with the font):

| family | subsets | notes |
|---|---|---|
| Playfair Display | latin, latin-ext, cyrillic | variable, `font-weight: 400 900` |
| Inter | latin, latin-ext, cyrillic × (normal, italic) | variable; the italic is a REAL italic file, not a synthesised oblique |
| Montserrat | latin, latin-ext, cyrillic | variable |
| Great Vibes | latin | static, 400 only |

They came from the `@fontsource-variable/*` and `@fontsource/*` packages
(OFL-1.1), extracted by `scripts/vendor-web-fonts.py`, which also injects
the `@font-face` rules into BOTH `styles.css` and `styles.min.css`. The
script is idempotent - running it twice leaves the bytes unchanged.

**arab / th / hi / ja are NOT covered** - there is no OFL family for those
writing systems. Those pages fall back to the system face, and the canvas
uses the SAME stack, so the page and the paper still agree.

### The subset system works

`unicode-range` comes from fontsource's own CSS, so the browser only
downloads the subset the text needs. Measured: the English home page pulls
3 files (135 KB), the Russian tool page pulls the Cyrillic subset as well,
and the Arabic page pulls no Cyrillic file.

### TRAP: do NOT regenerate styles.min.css

`npx clean-css-cli` 5.6.3 (the version that works on this box) rewrites
77 rules and **drops `.hero-bg .hero-video`** - the rule that hides the
hero video for visitors with vestibular disorders. Regenerating the file
silently deletes an accessibility feature.

So `scripts/vendor-web-fonts.py` only INSERTS the `@font-face` block into
`styles.min.css` and leaves every other byte alone. The reason the rule
disappeared in the first place was a stray `};` in `styles.css:1498`,
which clean-css swallowed - that is fixed in the source now.

## A canvas draws with whatever font is loaded AT THAT MOMENT

The three design templates (save-the-date, invitation, video-invitation)
name real families in their `fontStack`. Before the fonts were served, the
romantic template fell back to 'Apple Chancery' (macOS only) and then to
`cursive`, which is **Comic Sans on Windows** - so the SAME template
produced a DIFFERENT PNG on every operating system, and the preview did
not match the export.

`js/tools/common.js` now exports `fontsReady(families, text)`:

```js
await window.weddingAITool.fontsReady(['Playfair Display'], 'Emma & Liam');
```

`text` is passed on purpose: `document.fonts.load(font, text)` only pulls
the subset that the text needs, so an Arabic page never downloads the
Latin subset. Each of the three tools waits for the fonts before its first
draw and again before the export path bakes the file.

### The rule

**Any tool that draws text into a canvas must await the fonts before it
draws - once for the preview and once for the export.** A missing await
does not throw; it silently bakes the fallback face into the file.

`scripts/verify-web-fonts.py` proves the whole chain in a real browser
under the live CSP: the files come back 200, the families are loaded, and
each template's stack is measured with `measureText` against the same
stack with the webfont removed. A stack that measures the SAME resolves
to the fallback - i.e. the export would be baked with it.

### TRAP: the browser only downloads a font that is really USED

`document.fonts.check('40px "Playfair Display"')` is false on a page that
never renders Playfair. A test that asserts "the font was not fetched" has
to switch to the template that uses it first. Same trap in reverse: a font
that is fetched is not a font that is *used*.

## The PDF pipeline can now mix page sizes in one document (§2.17)

`downloadPdfPages()` had ONE page size for the whole document
(`opts.pageWidth` / `opts.pageHeight`). The photo album is fine with that,
but a wedding stationery pack is not: an invitation is 5x7 in, a place
card is 3.5x2 in and a poster is 18x24 in, and they have to end up in one
file.

`js/tools/common.js` now has two functions:

* `buildPdfPages(items, opts)` → the jsPDF document, **no download**
* `downloadPdfPages(items, filename, opts)` → builds it and saves it

and a page factory may return EITHER a canvas (legacy: the page is
`opts.pageWidth × opts.pageHeight`) OR
`{ canvas: <canvas>, pageWidth: n, pageHeight: n }` (the page is THAT
size). All sizes are in the document's unit - jsPDF's unit belongs to the
DOCUMENT, not to a page.

### TRAP: jsPDF's orientation argument OVERRIDES the size array

Measured on jsPDF 4.2.1:

```
addPage([5, 7])               -> 5 x 7 in
addPage([5, 7], 'landscape')  -> 7 x 5 in     <- the array is SWAPPED
```

The constructor's `orientation` option behaves the same way. So the
orientation must always be derived from the very same two numbers that are
handed to jsPDF, and a square page is passed as portrait. Get it wrong and
the page comes out rotated.

### TRAP: the FIRST page's size comes from the constructor

`addPage()` only ever sizes the SECOND and later pages. The constructor
has to be told the first page's size - not the largest, not the smallest.
A pack whose first page is a 3.5x2 in place card and whose second page is
an 18x24 in poster gets a 3.5x2 in first page.

`scripts/verify-pdf-page-sizes.py` proves both: it builds a mixed-size
document, reads every `/MediaBox` out of the generated BYTES and compares
it with the size that was asked for, and it runs the OLD algorithm side by
side as a control - the old code can only ever produce one size, so a
control that produced mixed sizes would mean the comparison proves
nothing.

## COOP/COEP is CLOSED on this site — ffmpeg.wasm is rejected (2026-11-12)

**The rule: any proposal that needs `SharedArrayBuffer` is out. That
includes ffmpeg.wasm, and it includes every "do the video editing in the
browser" idea that leans on it.** This is a settled decision, not a
preference to be re-litigated.

### Why, in order

1. **The headers are document-wide.** Cross-origin isolation needs

   ```
   Cross-Origin-Opener-Policy: same-origin
   Cross-Origin-Embedder-Policy: require-corp
   ```

   on the HTML response. That is not a per-tool switch: all 722 pages get
   them, and every third-party frame on every page falls under the embedder
   policy.

2. **It breaks the revenue product, SILENTLY.** Measured with the real
   AdSense and the real Clarity script on a page that mirrors the site's
   loader (`internal-tools/coop-coep-probe.py`, reproducible):

   | | plain | `require-corp` | `credentialless` |
   |---|---|---|---|
   | `crossOriginIsolated` | false | **true** | **true** |
   | `SharedArrayBuffer` | absent | **present** | **present** |
   | `window.adsbygoogle` | true | true | true |
   | `window.clarity` | true | true | true |
   | AdSense ad frame (doubleclick) | 5 182 bytes | **0 bytes** | **0 bytes** |
   | Clarity resources | 8 entries | **2 entries** | 7 entries |

   The top-level scripts keep loading, so `window.adsbygoogle` and
   `window.clarity` are still truthy and **nothing looks broken** - while
   the ad frame transfers zero bytes and, under `require-corp`, Clarity's
   session script and collection frame are gone. AdSense is the revenue
   product; Clarity is the only analytics left after GA4 and Baidu Tongji
   were removed (2026-10-28). Both die quietly, and neither one throws.

3. **`credentialless` is not a way out.** It keeps Clarity alive, but the
   AdSense ad frame is still 0 bytes, and **Safari does not implement the
   directive at all** (MDN: Safari "No support"; Firefox for Android
   neither). A Safari visitor would get neither SharedArrayBuffer nor a
   working ad frame.

4. **The licence is GPL.** `@ffmpeg/core@0.12.10` on npm carries
   `"license": "GPL-2.0-or-later"`, and the ffmpeg.wasm-core repository
   ships `COPYING.GPLv2` / `COPYING.GPLv3`. A GPL core inside the site's
   own JS is a licence question for the whole site, not a detail.
   (`@ffmpeg/ffmpeg`, the thin wrapper, is MIT - the core is not.)

5. **The single-threaded core does not need SharedArrayBuffer**, so it is
   technically possible - but it is a ~31 MB download with no hardware
   encode, against **mediabunny** (MPL-2.0, already vendored, WebCodecs
   hardware encode). It loses on every axis that matters here.

### The rule

The site's video work goes through **mediabunny** (WebCodecs) or the
browser's own `MediaRecorder`. Both are $0, need no cross-origin
isolation, and keep "nothing leaves the device" true.

`Cross-Origin-Opener-Policy` / `Cross-Origin-Embedder-Policy` must never
appear in `_headers` or in `buildCsp()` (`functions/_middleware.js`). If a
tool ever needs them, it needs its own origin - and this site does not have
one. A proposal that says "just use ffmpeg.wasm" is answered with this
section.

## The new-tool build pipeline (2026-11-10)

A new tool page is NOT hand-written. It is five scripts, in this order.
Each one exists because the step before it silently produced something
wrong.

```
scripts/assemble-tool-page.py        # sibling blocks + .tmp/<slug>.frag.html -> the page
scripts/add-tool-i18n-bindings.py    # data-i18n on every text element + the key map
scripts/translate-tool-page.py       # 11 languages -> .tmp/<slug>-patch.json + -head.json
scripts/apply-hand-curation.py       # hand-written strings over the machine translation
scripts/make-tool-lang-copies.py     # the 10 static language copies
scripts/add-tool-ui-keys.py          # the patch -> i18n/<lang>.json (11 files)
scripts/add-shards-for-keys.py       # the shard rebuild (FATAL if skipped)
scripts/verify-i18n-shards.py        # the freshness gate (FATAL)
```

`scripts/` is gitignored, so a new script there needs `git add -f`.

### TRAP: the draw functions need the PIECE and the STYLE, and the style has no size

`paint()` hands one object to the draw functions. If it is the STYLE, then
`s.w` is `undefined`, so `cx = s.w / 2` is `NaN`, and **a NaN coordinate
makes `fillText` draw nothing** (per the HTML spec). The result is a
correctly sized but completely BLANK canvas: the page still shows
"1500 x 2100 px", the buttons work, the PDF still has six pages of the
right dimensions, and only the artwork is missing.

The symptom is invisible everywhere except in the exported bytes. The fix
is to hand the draw functions both:

```js
var spec = { w: piece.w, h: piece.h, dpi: piece.dpi,
             ink: style.ink, accent: style.accent, rule: style.rule,
             head: style.head, body: style.body, ornament: style.ornament };
DRAW[piece.id](c, spec, scale);
```

### TRAP: `js/tools/common.js` is DEFERRED, so `window.weddingAITool` is undefined in an inline script

A classic inline `<script>` in the body runs while the document is being
parsed. The deferred `common.js` runs AFTER parsing. So at the top of an
inline tool script:

```js
if (window.weddingAITool && window.weddingAITool.fontsReady) { ... }   // always false
```

The font gate never fires, and the exported file bakes whatever fallback
face happened to be installed (Georgia on one machine, Comic Sans on
another) - the exact problem §2.16 fixed.

**The rule**: a tool page's inline script is wrapped in
`document.addEventListener('DOMContentLoaded', function () { ... })`, and
BOTH the preview and the export wait on the SAME promise. An export that
does not await the fonts is still broken even when the preview waits.

`tools/wedding-invitation-maker` and `tools/wedding-video-invitation-maker`
do this. `tools/save-the-date-maker` uses `fontsReady` WITHOUT the guard -
it is the same latent bug, still open.

### TRAP: the assembler left TWO `<style>` tags in the page

`head_mid` was sliced with an INCLUSIVE end marker, so it kept the
sibling's opening `<style>`; the style block was then rebuilt with another
`<style>`. The second tag is swallowed as CSS text, so the FIRST rule
(`.page-hero-mini`) is dropped - the hero loses its gradient, its white
text and its centering, and the page looks different from every other
tool page. Nothing in the source shows it; only the computed style does.

**The rule**: when a script copies a block out of another file, one of the
two slices must be EXCLUSIVE of the boundary. `slice_upto()` exists for
that.

### TRAP: masking with `\x00<index>\x00` collides with the token being replaced

The tool count lives in "13" - and the mask placeholder for attribute #13
is `\x0013\x00`, which CONTAINS "13". The count replacement rewrote the
placeholder, so the unmask put attribute #14's key into attribute #13's
slot and dropped #13 entirely. One attribute in twenty changed; the page
still rendered.

**The rule**: a "protect then replace then restore" pipeline must split
the text into segments and substitute only OUTSIDE the protected ones.
No placeholder, no collision.

### The i18n binding rules for a new tool page

* The middleware's `applyDataI18n()` replaces an element's **whole inner
  HTML**. So an element with nested tags loses them. Bind only elements
  whose content is PURE TEXT.
* For mixed content (`<p>text <a>link</a></p>`), wrap the loose text in
  `<span data-i18n="...">` and leave the `<a>` alone. The dictionary then
  holds plain text, which a machine translator can be trusted with, and
  the link survives in every language.
* The key is `tools.<slug>.<tag>_text.<snippet>.<hash8>`; the hash is
  md5 of the text, so the same text always gets the same key.
* `data-i18n` on a static element is the right way to translate it. The
  `t('alias', 'fallback')` path is for strings JS creates AFTER load.

### Runtime strings live in `tools.copy` + the COPY alias table

`js/tools/common.js` has a `COPY` table mapping `t('alias', ...)` to a
`tools.copy.<key>`; the middleware injects that namespace as
`window.__WA_I18N__`. **A new alias needs BOTH the COPY entry AND the key
in all 11 dictionaries** - `t()` falls back to `COPY[alias] || alias`, so
a missing alias looks up a key that does not exist and silently returns
English.

### The FAQPage schema of a tool page is NOT translated by the middleware

`replaceFaqJsonLd()` only knows two scopes: `homepage_faq` (10 questions)
and `pricing_faq` (6). A tool page's FAQPage block is therefore served
with ENGLISH questions and answers on every language page unless the
language COPY carries a translated schema. The language copies are
therefore built with the schema rewritten
(`scripts/make-tool-lang-copies.py` -> `localize_schema()`), and the
schema strings are translated from the SAME map as the visible FAQ, so
the structured data and the copy cannot drift apart.

### Google Translate: the free endpoint is the bottleneck

* It answers **429** after a few thousand calls, and a retry storm turns
  a two-minute cooldown into a twenty-minute one. The script now backs
  off hard on 429 and writes its output after EVERY language, so a run
  that gives up still leaves the work it did on disk.
* **One request can carry many strings**: the endpoint accepts `q` more
  than once and answers with one segment per `q`. That is the difference
  between 1900 requests and 190.
* The brand is masked with `ZXQPROT0ZXQ` - measured: it survives all ten
  target languages, while a mask made of control characters (`\x00`) is
  dropped by all ten.
* Numbers are NOT masked: "5 x 7 in" comes back as "5 x 7 pulgadas", and
  a digit check catches the case where a digit is dropped.
* **Reuse what the site already has**: the dictionaries hold 44k-70k keys
  per language, and phrases like "Home", "Free Tools" or "Frequently asked
  questions" are already translated somewhere. `build_reuse_map()` finds
  them by English value and spends no endpoint calls on them.
* Machine translation gets the SHAPE right and some WORDS wrong. On the
  stationery page it turned "The names of the hosts, if your families are
  hosting" into "the landlords' names (if your family is renting out)".
  The title, the H1, the section headings and the buttons are therefore
  written by hand (`scripts/apply-hand-curation.py`).

### `scripts/verify-tool-export.py` exports the file and reads the bytes

A tool page can look perfect and still produce a broken file, so the
check exports for real: it decodes the PNG and counts the distinct
colours, it parses the PDF's `/MediaBox` and converts to inches, and it
records every `document.fonts.load` call.

**It has a negative control**: `--negative-control` puts the NaN bug back
into the served HTML and requires the checker to FAIL. A checker that
cannot fail on the bug it was written for proves nothing.





## The translation backend was writing garbage, and NO gate could see it (2026-11-10)

This is the most expensive finding of the five-tool batch, and it is
worth reading before trusting any machine translation this project has
ever produced.

### `thinking: disabled` is what made the model copy English

The MiniMax gateway (`https://agent.minimax.cn/mavis/api/v1/llm/v1/messages`)
was called with `thinking: {"type": "disabled"}` because a 20-item batch
then took 4.5 s instead of 76 s.

Measured, same 4 items, 4 repeats, Japanese:

| configuration | untranslated English spans | seconds per batch |
|---|---|---|
| MiniMax-M3, thinking disabled | **8 / 12 answers** | ~2 |
| MiniMax-M3, thinking enabled | 0 / 16 answers | ~28 |
| MiniMax-M3.1-Flash, thinking enabled | 0 / 16 answers | ~29 |
| MiniMax-M3.1-Flash, plain | 0 / 16 answers | ~45 |

With the thinking off, the model stops translating partway and copies the
English source into the middle of the sentence:

* `地元での結婚式なら6〜8週間前、infuseの結婚式は…` (Japanese with German)
* `重厚な heavier feel 出す` (Japanese with English)
* `Both ask for picture numbers, and both would rather have a numbered` (English)
* `無料的Pete worldwide造的Pete wedding photos to GIF converter` (Chinese + English)
* ` marrying a 和 bacteria` - and 112 of the 311 values the two shipped
  tools had in the dictionaries were defective this way.

**Speed was bought with a defect that nobody could see.** The length gate
cannot see it (the string has a plausible length), the number gate cannot
see it (the digits are all still there), the "same as English" check
cannot see it (the string as a whole IS translated), and the FAQ parity
check cannot see it (the schema and the visible copy agree - they are
both garbage).

The rule: **thinking stays ON**. `LLM_THINKING = "enabled"`.

### TRAP: `budget_tokens` is not honoured, so `max_tokens` must leave room

With `max_tokens=8000` and `budget_tokens=2000`, one 12-item batch
answered with `output_tokens=6927` of which `thinking_tokens=6607` - the
model ignored the budget, spent the whole allowance thinking, and the
answer came back EMPTY. The run then sat in a retry loop.

The batch calls now use `max_tokens=24000` and the single-item retries
`max_tokens=12000`. The gateway's `usage.output_tokens_details` is the
number to watch, not the budget you asked for.

### The untranslated-span gate (`foreign_spans` + `english_ngram_leak`)

The only thing that notices a half-English sentence is the WORDS. So the
translation script now carries a second, deterministic gate:

* `foreign_spans(text, lang)` - for a non-Latin target, every maximal
  Latin run inside the sentence must be a format name, a brand, a unit, a
  paper size, a domain, or nothing but numbers and unit words.
* `english_ngram_leak(source, target)` - a translation may not contain
  five consecutive English words from its own source. This is what
  catches the wholesale copy in the four Latin-script targets, where
  every word is already a Latin word.
* `script_ok(value, lang)` - the reuse map copies a value out of another
  language's dictionary, and this site's own Japanese dictionary hands
  out the CHINESE `常见问题` for "Frequently asked questions". Both
  languages use kanji, so only the script tells them apart.

Both gates are wired into `llm_verify()` (a fresh translation), into
`verify_stored()` (a reused one) and into `build_reuse_map()` (a value
copied from another tool). A flagged item is re-done with the strict
prompt, and if it still fails it is REPORTED rather than shipped in
English.

**The gate has a negative control in both directions**:
`.tmp/test-foreign-gate.py` holds 35 cases - known garbage that MUST be
flagged and known-good translations that MUST pass - and exits non-zero
if any case lands on the wrong side. A gate that never fires proves
nothing, and a gate that fires on "1 PDF" or on the German "Drag-Drop"
costs a retry or an English fallback.

### TRAP: `write_outputs()` must never fall back to English

The patch writer used to write `per_lang[lang].get(en, en)` - so a
string this run did not translate became the English source. One
consistency pass over the video editor's patch therefore replaced **110
finished Chinese translations with English**, silently, because a
language that was translated in an EARLIER run looks exactly like a
language that was never translated.

The rule now: the previous value wins over English, and only a previous
value that IS the English gets replaced.

### TRAP: a rotated gateway token answers 401, and the run dies quietly

The desktop runtime rewrites `~/.minimax/auth/*/*/*/auth.json` when it
refreshes the token. A run that started a second earlier holds the token
that just died, and every request answers `401 Unauthorized` - which the
old retry loop treated as a normal back-off and then gave up on.

`llm_post()` now catches `HTTPError` with code 401, re-reads the
credential (`resolve_llm_token(force=True)`) and tries again.

### TRAP: a video with no duration header is a video the tool cannot open

The wedding video editor read the duration ONCE, in the `loadedmetadata`
handler:

```js
state.duration = isFinite(videoEl.duration) ? videoEl.duration : 0;
```

A container that carries no duration header - a screen recording,
anything `MediaRecorder` wrote, some MKV files - reports **Infinity**
when the metadata arrives, and the browser only works the real duration
out later. `isFinite(Infinity)` is false, so the duration became 0, the
export button never enabled, and the tool was dead for exactly the files
a couple records on a laptop.

Measured: a one second WebM gave `duration=Infinity` at
`loadedmetadata` and the button stayed disabled forever.

The fix (`applyDuration()` + `probeDuration()`): apply the duration
wherever it becomes known (`durationchange` as well), and when it is not
finite, ask the browser for it by seeking past the end.

`scripts/verify-tool-smoke.py` now has a `--file-type webm` mode that
records a real clip with `MediaRecorder` and feeds it to the page,
because a PNG is not a video and the page is right to ignore it.

### TRAP: the tool count is not the only number on the hub page

`scripts/sync-tool-count.py --count 18 --old 14` replaced every
standalone `14` with `18`. Six of those were NOT the number of tools:

* `"position": 14` - the 14th entry of the ItemList. The rebuild gives
  positions 1..18, so the replacement left TWO items at position 18 and
  none at 14.
* `14 fonts` / `14 wedding fonts` - the add-text tool ships 14 fonts.
* `14 categories` / `14 categories by region` - the budget calculator
  splits a budget into 14 categories.
* `14+ competitors` - a claim about other products.

The script now masks those phrases before the replacement. The mask
carries no DIGIT, because a placeholder containing "14" would be
rewritten by the very replacement it is hiding from.

The same sentence holds two counts: `✓ 14 tools, 3 categories` - the
number of tools AND the number of sections. The hub grew a fourth
section (Document tools) on 2026-11-10, so the section count is computed
from the grids, like the section headings are.

### The new gates

* `scripts/build-hub-copy-patch.py` - translates the four new tool cards
  and the four section headings. The section heading carries its own
  count ("Photo editors (6)"), and the count is NOT translated: it is
  stripped, the words are translated, the count is put back.
* `scripts/publish-new-tools.py` - merges every patch into ONE file (the
  dictionaries are 6-17 MB, so five writes become one), writes them,
  syncs the count, writes the 10 language copies of every tool page,
  propagates the English inline JS into them, rebuilds the shards and
  verifies them.

### The section headings were wrong in a way that changed the meaning

"Makers and generators" came back as `制造商和发电机` in Chinese (a
manufacturer and an electrical GENERATOR) and `ผู้ผลิตและเครื่องปั่นไฟ`
in Thai (a producer and a BLENDER). A reader in those languages was
told the site makes appliances. "Photo editors" came back as `写真編集者`
in Japanese - a photo EDITOR, a person - and "Planners and calculators"
as `プランナーと計算機`, a calculating MACHINE.

### The hub's new cards are 14 to 18, not 15 to 18

`scripts/build-hub-copy-patch.py` listed the cards to re-translate as
`["15", "16", "17", "18"]`. The hub numbers its cards by POSITION, and
the five new ones are **14, 15, 16, 17 and 18**:

```
11 save-the-date        14 stationery set   16 photo-to-gif
12 invitation           15 contact sheet     17 video editor
13 video invitation     18 pdf editor  (the only card in the docs section)
```

So the card that was left out was the stationery set maker - and it
looked fine, because a missing card is not an error, it is a card whose
name stays English in ten languages.

The card number is the number in the i18n KEY (`tools.card.name.gen.14`),
so the key namespace is a position, not a stable id. A card that is
inserted in the middle renumbers every card after it.

### The English of a page is the HTML, not en.json

The middleware returns `null` for the default language, so for an
English visitor **the static HTML is the English**. `i18n/en.json` is a
copy of it, and the copy had drifted:

| key | HTML | en.json |
|---|---|---|
| `tools.section.title.gen` | `Makers and generators (3)` | `Makers and generators (5)` |
| `tools.section.desc.gen` | no stationery set | mentions the stationery set |
| `tools.section.title.docs` | `Document tools (0)` | key absent |
| `tools.card.{badge,name,tag}.gen.16/17` | present | key absent |
| `tools.card.{badge,name,tag}.docs.18` | present | key absent |
| `tools.card.cta.try_free.16/17/18` | present | key absent |

The patch builder read its English from `en.json`, so it skipped the
docs section (no key) and could not translate cards 16-18. It now reads
the English from the HTML, which fixes the drift and makes the missing
keys translatable in the same pass.

The heading itself was wrong for the new grid: seven cards, of which
three are converters (contact sheet, GIF, video editor). "Makers and
generators" is now "Makers, generators and converters".

### A key can be missing from nine of the eleven dictionaries

`tools.card.badge.edit.02` ("HEIC") existed in **Russian only**. The
middleware falls back to the static English, so the page renders and
the dictionary looks complete - but a Russian reader got a Russian
badge and everyone else got the English one.

`.tmp/audit-page-keys.py` lists every `data-i18n` key a page uses, and
for every language that does not have it. Run it over a page after any
hub change.

## The gateway has a request-rate ceiling, and it is a WALL (2026-11-11)

Two runners of six workers each - twelve parallel requests - ran for
two hours and then the gateway answered **429 to everything, for the
rest of the run**: 1385 retry lines, no output, no recovery. The
retries were not the problem; the account was already over the line
and the backoff never got back in.

Measured with a serial probe (10 heavy requests, one every 6 s, the
same shape the translator uses - thinking on, 12 strings, 24000 max
tokens): **0 failures**. So the budget is comfortable when the requests
are spaced out.

`scripts/translate-tool-page.py` now has a **global request gate**: one
interval shared by every thread, so no two requests start less than
5 s apart whatever the worker count is. A 429 makes the interval grow
by half (up to 60 s), a success lets it shrink again by 2% per call.

**The gate is per PROCESS.** Two runners are two gates and therefore
twice the rate. The 429 wall is what made "run the five tools in two
parallel groups" attractive in the first place, and it is exactly what
made it fail. One runner, one gate.

The gate sits in `llm_post()`, before the request, and the penalty is
raised in the `HTTPError` branch on `exc.code == 429` - a rate limit
has to slow down **everybody**, not just the thread that hit it.

The token is also rotated by the desktop runtime under the running
process: a 401 means the credential file changed, not that the
credential is wrong. `resolve_llm_token(force=True)` re-reads it.

### An empty answer is a BUDGET problem, not a bad prompt

The gateway does not honour `budget_tokens`: the model thinks for as
long as it likes and the thinking tokens come out of `max_tokens`. A
15-string batch that came back with no text at all spent all 24000
tokens thinking. The same batch with 48000 comes back with the answer.

So `llm_post()` DOUBLES `max_tokens` on an empty answer (24000 → 48000
→ 96000, capped) instead of just waiting and repeating the same
request. The request body is built inside the retry loop for exactly
that reason.

## The hub held 32 tools, and every commit said a different number (2026-11-11)

Found while fixing the count for the five new tools.

### The truth

| where | what it said | what the page held |
|---|---|---|
| the hub's `<title>` | "13 Free Wedding Photo Tools" | 32 cards |
| the hub's H1 | "13 Free Wedding Photo Tools in One Catalog" | 32 cards |
| the home page's H2 | "14 Free Wedding Tools for 2026" | 32 cards |
| the ItemList's `name` | "27 Free Wedding Planning & Photo Tools" | 32 cards |
| the hero badge | "27 free tools, 4 categories" | 32 cards, 5 sections |
| the dictionaries | a fifth number | 32 cards |

The hub grew three times in two days — the planning-tools batch added
14 cards on 2026-11-11 04:18, and this session added 5 — and each
commit touched only its own copy of the count. The section headings had
drifted three ways at once as well: the HTML said "Makers and generators
(3)" over a grid of seven cards, `en.json` said "(5)", and the hero
badge said "3 categories" over four sections.

### THE PAGE IS THE TRUTH

`scripts/fix-hub-count.py` (2026-11-11) replaces
`scripts/sync-tool-count.py` for this. The old script took the count as
an ARGUMENT (`--count 18 --old 14`) — which is the wrong shape: a
number typed in by hand goes stale the moment a card is added. The new
one counts the `<a class="tool-card">` elements and the
`<section class="tool-section">` blocks and rewrites every number from
them.

It also rewrites the WORDING, because the hub stopped being a photo
tool catalogue: "13 Free Wedding Photo Tools" became "32 Free Wedding
Planning & Photo Tools", the name the ItemList already used.

### The hero badge holds TWO numbers

`✓ 32 free tools, 5 categories` - the tool count and the CATEGORY
count, in one sentence. A regex for the English word "categories"
fixed the English and left the other ten languages saying three
(`✓ 32 个工具，3 个类别`). The rule that works in every language: **the
first number is the tool count, the second is the category count**.

### The badge had no binding at all

`tools.hero_badge.thirteen_tools.7a8b9c0d` was in the dictionaries but
NOT on the element in the HTML, so the badge showed the English
"27 free tools, 4 categories" in every language - and the dictionary's
translation was dead. The binding is now on the element.

### A working tree can be a REGRESSION against HEAD

The planning-tools batch committed a newer hub at 04:18. A script that
ran afterwards overwrote `tools/index.html` with an older copy, so the
working tree had 32 cards but an 18-entry ItemList and a count of 14 —
the opposite direction from the commit.

The rule: **before editing a file another session has touched, compare
it with HEAD.** `git diff HEAD -- <file>` shows whether the working copy
is ahead or behind. Here it was behind, and the fix was to restore
from HEAD and re-apply only the five cards.

### The planning batch is English-only on purpose

The 14 planning cards have NO i18n binding and their tool pages have
NO language copies (0 of 10). So they show in English in the other ten
languages on purpose — `scripts/check-hub.py` reports them as a note,
not a failure. A card with SOME bindings and a missing field is still
a failure.

### The card numbers are positions, and the planning cards have none

`tools.card.name.gen.14` — the number is the position in the grid. The
planning cards are unbound, so they do not take a number and do not
shift the numbering: the five new cards are 14-18 whether the planning
cards sit before or after them. `scripts/check-hub.py` checks that the
ItemList positions are 1..N with no gap and no duplicate, and that
every card href and every ItemList url is a page that exists.

## A print statement threw away three translation runs (2026-11-11)

### What happened

The timing line added to `scripts/translate-tool-page.py` was

```python
print("    [%s] %d strings, %d batches, %d repairs, translate %.0fs, "
      "verify %.0fs" % (target, len(masked), len(groups), repairs,
                        t_translate, time.time() - t0),
      file=sys.stderr)
```

Six conversions, five arguments. `TypeError: not enough arguments for
format string`.

The exception fires **after** the language has been translated, so the
work was already done — and then it was thrown away. The runner printed
`wedding-stationery-set-maker finished in 2.3 min (exit 1)` and moved
on to the next tool. Three tools in a row died the same way, and the
log said "failed" without ever saying "the translations you just paid
for are gone".

### Why a static check is the right tool for it

A "%"-format call with the wrong argument count is a pure static
property. It does not need the gateway, the page, or the browser to
prove.

`scripts/check-py-format-strings.py` walks the AST of every python file
and resolves the argument side through the enclosing scopes:

| right-hand side | verdict |
|---|---|
| a tuple literal | its length must EQUAL the conversion count |
| a name bound to a tuple | same rule |
| a name bound to a scalar | exactly one conversion |
| anything else | UNKNOWN — counted, never failed |

Two rules, not one. **Too few** values is `not enough arguments`; **too
many** values is `not all arguments converted`. Both raise, both kill a
run, and the second one is the easier mistake to miss.

An attribute is UNKNOWN, not "one value": `"%sx%s" % im.size` looks like
one argument, but `im.size` is a `(width, height)` tuple at runtime and
Python consumes two. Calling that a defect would have been wrong — the
checker had to be corrected, not the code.

### A gate that fires on 170-odd known-fine lines is a gate nobody reads

The first version reported every call it could not prove, and found 172
of them. All 172 were fine. The rule: **report a defect only when it is
PROVEN, report an unknown as a count.** The checker now reports 438
files, 0 defects, 293 unprovable calls — and the 293 are noise-free
because they are not failures.

### The negative control has to be checked too

`--negative-control` writes a known-bad file and asserts the checker
reports it. It caught a mistake in the control itself: the second case
was `"%sx%s" % (100, 200)`, which is **correct** Python. The real
"not all arguments converted" needs one conversion and two values. A
control that does not fail proves nothing — including the control.

The check is wired into `internal-tools/pre-deploy-check.ps1` as step
**9h** and is FATAL.

### The patch file is written after EVERY language

`scripts/translate-tool-page.py` calls `write_outputs()` after each
language, not once at the end. So a run that is killed mid-way keeps the
languages it already finished, and the next run picks them up with
`--skip-existing` (which reads the patch file, NOT the dictionary).

Both writes were plain `write_text`, which is not atomic: a kill during
the write leaves a truncated JSON file, and the next run then dies on
`json.loads()` before it can repair anything. They now use the house
pattern (temp file + fsync + `os.replace`), the same one
`scripts/add-tool-ui-keys.py` and `scripts/fix-hub-count.py` use.

### The dictionary already holds a tool's translations, and they can be GARBAGE

`--skip-existing` reads the patch file, not the dictionary. The reuse map
(`build_reuse_map`) reads the dictionary, but the runner excludes the five
new tools' namespaces from it (`--reuse-exclude`). **That exclusion is
load-bearing**, and it was measured, not guessed:

Running the translator's own gates over the values the dictionaries
already held for the new tools:

| tool | zh | es | fr | de | pt | ja | ru | ar | th | hi |
|---|---|---|---|---|---|---|---|---|---|---|
| contact sheet | 7 | 1 | 0 | 2 | 0 | **48** | 0 | 12 | 7 | 3 |
| stationery set | 2 | 0 | 0 | 1 | 1 | **40** | 0 | 15 | 1 | 2 |

142 bad values in total. The failures are the `thinking: disabled`
signature — English left in the middle of a translated sentence:

```
ja   Folder内の_numeric_photos_を        (a photo folder)
ja   tricked                            (wedding website)
ar   .code Dress                         (dress code)
ar   أدوات-stationery                    (a wedding stationery set)
ar   موقعedding                          (the wedding website)
ar   هناك طريقتان لل doing ذلك           (there are two ways to do this)
ar   ... bacterium ...                    (memory, in the 150 DPI paragraph)
th   แผ่น proof sheet                    (a proof sheet)
zh   请按 100 percent 打印                 (print at 100 percent)
```

So the dictionary is NOT a safe source of translations for a tool that
is about to go live: it holds machine-translation garbage that a reader
would see on the page. The pipeline re-translates from scratch, and the
run's own output replaces the stored value
(`add-tool-ui-keys.py` overwrites, and re-reads the file to confirm).

Note that the gate also has FALSE POSITIVES on short technical strings:
`家` (home), `1列` (1 column) and `A4（210 × 297 mm）` are all correct
Japanese and Chinese, and the `script_ok` check flags them because they
carry no kana / mix scripts. A false positive costs a re-translation, not
a wrong page, which is the right way round for this gate.


### One runner, one gate — including when the other runner is "finishing"

On 2026-11-11 two runners were alive at the same time: the new one
(started 08:42) and the old one (started 08:29) that had already been
restarted once. They were working the **same five tools in the same
order**, and they wrote to the **same log files**, so each one overwrote
the other's progress report. Two runners are two request gates, which is
exactly the configuration that built the 429 wall.

Kill the old one before starting the new one. A `task_stop` on the
runner does not always take the child `python.exe` with it — check
`Get-CimInstance Win32_Process -Filter "Name='python.exe'"` and make
sure exactly one `translate-tool-page.py` is left.

### A background task has a 1-hour limit, and it takes the child with it

The translation runner was started as a background task at 08:42 and was
killed at exactly 3600 s, in the middle of the Russian pass. The work
was not lost (the patch file is written after every language) but the
process died with it, and with it the other four tools.

**Start the long runner DETACHED**, not as a task:

```powershell
Start-Process python -ArgumentList "-u", ".tmp\run-retranslate-forever.py" \
    -WorkingDirectory "<repo>" -WindowStyle Hidden
```

The wrapper loops: it restarts the runner whenever it stops, and it ends
when every tool's patch holds a real translation for all ten languages.
A detached process is not tied to a task's lifetime.

### TRAP: the i18n MAP deduped by TEXT, so half the keys never existed

`scripts/add-tool-i18n-bindings.py` builds the key -> English map the
translator works from. It used to keep **one key per English text**:

```python
for key, text in keys:
    if text in seen:
        continue          # <- dropped the second key for the same text
```

That is wrong, because the same visible string is often bound under two
element types:

```
h2_text.what_to_put_on_a_wedding_invitation.c45a79e9   (the section)
h4_text.what_to_put_on_a_wedding_invitation.c45a79e9   (the related card)
td_text.3_columns.7f6ed182                            (a table cell)
option_text.3_columns.7f6ed182                        (a dropdown option)
```

The hash is derived from the TEXT, so both keys share it, and the
text-dedup kept only one. The other one had no key in any dictionary and
showed English in all ten languages. 22 keys were affected across the
five new tools.

The map now dedups by KEY. The translator already dedups by text on its
own (`all_texts`), so the same string is still translated only once.

**The convention, measured**: the thirteen existing tools keep BOTH keys
in `en.json` - 13/13, 7/7, 13/13 collisions, all with both keys
present. A tool that keeps one is the odd one out.

### TRAP: `data-i18n-attr` carries "attr:key", and a checker that keeps the whole string fails on every page

The two binding spellings carry different things:

```
data-i18n="blog.foo.p_text.bar"          -> the key IS the value
data-i18n-attr="content:blog.foo.meta"   -> "attr:key", several pairs
                                            separated by "|"
```

The middleware splits an attr pair on ":" and uses the part AFTER the
colon (`functions/_middleware.js`, `applyDataI18nAttr`). A checker that
keeps the whole `"title:about.a_text.couples_served_title.ddddddd3"`
string looks for a key that exists in NO dictionary — and reports a
defect on every page that binds an attribute, while the binding is in
fact perfectly fine.

`scripts/check-page-i18n-keys.py` now mirrors the middleware (split on
"|", then on the first ":") and has a negative control that proves both
binding forms are read correctly.

**The general rule**: a checker that reads a binding must read it the
way the RUNTIME reads it. The runtime is the specification.


