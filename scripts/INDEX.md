# scripts/ — Index

> All scripts in this directory are local tooling only. They are excluded
> from production deploys via `.assetsignore` (see repo root). No
> script here is ever served at https://weddingai.video/.

## 🚨 Main flow (run on every deploy)

These are the only scripts that should ever be run during a normal
deploy cycle. Add to `pre-deploy-check.ps1` or the deploy script.

| Script | Purpose | When |
|---|---|---|
| `bump_cache_version.py` | Bump `?v=N` on `js/i18n.js`, `js/main.min.js`, `styles.min.css` across all HTML | Whenever JS or CSS changes |
| `check_langs_sync.py` | Verify `js/langs.js` ↔ `functions/_lib/langs.js` ↔ `_redirects` stay in sync | Every deploy (in pre-deploy-check) |
| `sync_langs_redirects.py` | Regenerate the 10-line `/xx/* → /:splat 200` block in `_redirects` from `js/langs.js` | After adding/removing a language |
| `inject_langs_preload.py` | One-time: inject `<script src="/js/langs.js" defer>` before `i18n.js` in every HTML (idempotent) | Already run 2026-07-28; rerun only if a new HTML is added without it |
| `deploy.ps1` | Full deploy pipeline (sitemap regen → pre-check → wrangler deploy → indexnow) | Every deploy |
| `submit-indexnow.ps1` | Ping IndexNow + Bing for sitemap updates | After deploy |
| `pre-deploy-check.ps1` (root) | All quality gates in one place | Every deploy |

## 🔧 Standard utilities (run as needed)

These are the routine helpers that show up in CHANGELOG. Safe to run
on demand; not part of the deploy pipeline.

| Script | Purpose |
|---|---|
| `audit-images.py` | Verify `<img>`/`<picture>` references resolve; list missing widths |
| `audit-blog-seo.py` | Blog post SEO audit (titles, meta, headings) |
| `audit-external-links.py` | Find 4xx/5xx external links |
| `audit-issues.py` | General structural issue audit (use `qa/full_qa.py` for current) |
| `check-seo-lengths.py` | Verify title ≤ 60 / description ≤ 160 chars |
| `check-contrast.py` | WCAG color contrast spot-checks |
| `check-h1.py` | Verify every page has exactly one h1 |
| `check-descs.py` | Verify meta descriptions present and non-empty |
| `standardize-ga4.ps1` | Swap GA4 measurement ID across all HTML |
| `standardize-service-names.py` | Re-run after adding/renaming a service |
| `set-cloudflare-secrets.ps1` | Helper to set CF Pages secrets (handles BOM trap) |
| `test-resend-key.ps1` | Verify Resend API key is valid without going through the form |

## 🛠 Build / content generation (rerun when content changes)

| Script | Purpose |
|---|---|
| `generate-blog.py` | Build blog HTML from `articles/*.md` source |
| `qa/gen_sitemap.py` | Build all 11 `sitemap-*.xml` files (root sitemap index + 10 per-language sitemaps). Run before every deploy. |
| `i18n_extract.py` | Extract `i18n/en.json` source of truth from all HTML |
| `i18n_translate.py` | Run Google Translate for 9 non-EN languages (writes `i18n/{lang}.json`) |
| `i18n_inject.py` | ⚠️ **DEPRECATED** — known to corrupt HTML. Use `qa/fix_structural_v2.py` to repair, never re-run inject |
| `i18n_fix_zh_round3.py` | Targeted ZH translation corrections (3 passes) |
| `minify-css.py` | Rebuild `styles.min.css` from `styles.css` |
| `batch-gen-heroes.py` | Generate hero images via image_synthesize |
| `design-blog-image-prompts.py` | Output prompts for blog hero images |
| `extract-pricing-tables.py` | Pull pricing HTML for review |
| `expand-content.py` / `expand-content-2.py` | Bulk content fill-in (used during initial build-out) |

## 🔍 Debug / ad-hoc (use sparingly, then archive)

These one-off scripts are kept for reproducibility. Most were created
for a specific bug fix during 2026-07-27's i18n migration and are
**not** part of any regular flow. If a script has `debug-`, `trace-`,
`dump-`, `fix-2-`, `fix-3-`, `fix-pass3-` etc. in its name, it's a
point-in-time fix and should not be re-run on a healthy codebase.

**Naming convention:**
- `fix_<thing>.py` — applied once, kept for history
- `fix-<thing>-<n>.py` — iterative passes on the same root issue
- `debug-<n>.py` — temporary; safe to delete if the issue is gone
- `dump-<thing>.py` — diagnostic dump; never modifies files
- `audit-<thing>.py` — read-only, safe to rerun

If you're tempted to write a `fix-` script, first ask:
1. Can this be a one-time edit in the affected HTML?
2. If multiple files, can it be a one-time `qa/full_qa.py` rule that
   prevents the bug from coming back?

## 🗑 Candidate for archival

These scripts have not been needed for ≥ 30 days. Move to
`scripts/archive/2026-07-27-i18n-migration/` if they're still there
when you next look:

- `debug-audit.py` through `debug-audit5.py`
- `fix-pass3.py`, `fix-pass4.py`
- `fix-2-descs.py`, `fix-3-files.py`
- `trace-04.py`, `test-04.py`, `test-21.py`
- `remove-2-services.py` (one-time service list change)
- `migrate-to-dir-index.py` (one-time URL restructure)
- `rename-blog-dirs.py` (one-time blog slug change)
- `css-cache-buster.py` (replaced by `bump_cache_version.py`)

The ones above that have been **replaced by a newer script** are
candidates for outright deletion (the newer script's INDEX entry
already covers the use case).

## 📦 Archived scripts (2026-07-28)

**Status (2026-07-28):** 211 historical scripts (mostly 1-shot `fix-*` /
`debug-*` / `test-*` / `audit-*` from the 2026-07-20 to 2026-07-27
i18n-migration + initial-build mass-fix passes) were moved to
`scripts/archive/2026-07-28/{scripts,qa,__pycache__}/` during the
P2-1 cleanup.

- These scripts MUST NOT be re-run. They were tied to a point-in-time
  state of the site; running them now will be a no-op or regress.
- Retained for **6 months (until 2027-01-28)** for inverse-fix
  reproducibility. After 2027-01-28 the whole `archive/2026-07-28/`
  tree can be deleted unless someone explicitly extends the retention.
- All `.txt` / `.log` / `.pyc` debug-output files in `scripts/` and
  `qa/` were deleted outright (zero historical value).
- `archive/2026-07-28/README.md` lists what was moved and why.

The original "candidate for archival" list above is now resolved
— those files are no longer in `scripts/`. New section above is the
**source of truth** going forward.

## 📋 Adding a new script

1. Name it after what it does (`audit-blog-tags.py`), not when you
   wrote it (`fix-thursday.py`).
2. Add an entry in one of the sections above.
3. If it modifies HTML across many files, make it **idempotent** —
   running it twice should be a no-op.
4. If it's a one-time fix, prefix with `fix-` and add a date stamp
   in the file's docstring.
