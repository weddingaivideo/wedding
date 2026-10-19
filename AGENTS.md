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
