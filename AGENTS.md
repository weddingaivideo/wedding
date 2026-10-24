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
  `AggregateOffer` `lowPrice: 9.90`), and the `index.p_text.based_on_9_400_*`
  market-average paragraph. Those are real, purchasable products.
- "free" is NOT a price — "13 Free Wedding Photo Tools", "100% free",
  "Try free →" are the product promise and must survive any price sweep.

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

