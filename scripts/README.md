# scripts/

Local tooling for the weddingai.video project. Everything in this directory
(and `qa/`) is **excluded from production deploys** via `.assetsignore` at
the repo root, so scripts here are never served at `https://weddingai.video/`.

## TL;DR — most common commands

```powershell
# Pre-deploy quality gate (run this BEFORE every deploy)
powershell -ExecutionPolicy Bypass -File pre-deploy-check.ps1

# Full deploy pipeline (sitemap regen + pre-check + wrangler + indexnow)
powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1

# Regenerate sitemap only (e.g. when adding/removing pages)
python qa/gen_sitemap.py

# Verify the deployed site
python qa/verify_sitemap.py
python qa/test_accept_lang.py
python qa/full_qa.py
```

## What's in here

See [INDEX.md](./INDEX.md) for a full categorized catalog of every active
script. Quick map:

| Need | Script |
|---|---|
| Pre-deploy gate | `pre-deploy-check.ps1` (repo root, not here) |
| Deploy | `scripts/deploy.ps1` |
| Sitemap regen | `qa/gen_sitemap.py` |
| Blog content | `scripts/generate-blog.py` |
| i18n JSON regen | `scripts/inject_langs_preload.py` + `qa/fix_p0_4_i18n_keys.py` (model) |
| Cache buster bump | `scripts/bump_cache_version.py` (auto +1) or `qa/bump_cache_to_3_22.py` (specific) |
| Lang list sync | `scripts/check_langs_sync.py` + `scripts/sync_langs_redirects.py` |
| Local SEO / audit | `scripts/check-seo-lengths.py` |
| Hardcoded secret scan | inside `pre-deploy-check.ps1` step 11 (covers `functions/`) |
| Force static asset refresh | (none — done via `?v=N` cache buster) |

## What was archived (2026-07-28)

`scripts/archive/2026-07-28/` contains **211 historical scripts** that were
active before the P2-1 cleanup. They are kept for 6 months (until
2027-01-28) in case a future regression needs the inverse-fix. **DO NOT
re-run** anything in there — they were tied to a point-in-time state of
the site.

See [archive/2026-07-28/README.md](./archive/2026-07-28/README.md) for
what was moved and why.

## Adding a new script

1. Pick a name that says what it does (`audit-blog-tags.py`), not when
   you wrote it (`fix-thursday.py`).
2. Make it **idempotent** — running it twice should be a no-op.
3. If it modifies HTML across many files, also add a one-time `qa/`
   `full_qa.py` rule that prevents the bug from coming back.
4. Update [INDEX.md](./INDEX.md) with the script's purpose and "When to
   run" hint.
5. **Do not** add it to the active list if it's a one-time fix — use
   the archive pattern instead.
