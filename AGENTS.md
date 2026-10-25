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

