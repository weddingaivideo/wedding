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
  the localized backlog. It is wired into the gate as step **9b** and is
  **report-only** (`--strict` makes it fatal), because the backlog is a
  translation job and must not block a deploy.
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

* The site still marks a suppressed send as `delivered`. Nothing polls
  Resend's event status or the suppression list, so the same silent loss can
  happen again, silently, for as long as it takes someone to notice.
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
stays at `751 OK, 0 over`. The gate's step 9b is now clean but stays
report-only.
