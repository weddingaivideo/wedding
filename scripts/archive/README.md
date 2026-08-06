# Archive — Deprecated Scripts

These PowerShell scripts were one-off patches used during the v1.0 build (2026-07-20).
They are kept here for historical reference only.

**Do NOT run these on a fresh checkout.** The bugs they were patching have been
fixed in the source files, and running them now would either be a no-op or
would re-introduce issues that have since been resolved.

## Why these exist

The v1.0 build was assembled quickly, and a series of `fix-*.ps1` scripts was
used to patch up issues that were discovered after the initial file generation
(empty hero divs, broken section IDs, wrong image paths, missing CSS, etc.).
These patches are now baked into the source files.

## What's in here

| Script | What it fixed | Status |
|--------|---------------|--------|
| `add-remaining-ids.ps1` | Added missing `id` attributes to nav/section elements | Fixed in source |
| `append-css.ps1` | Appended missing CSS rules to styles.css | Fixed in source |
| `clean-extra-ids.ps1` | Removed duplicate `id` attributes | Fixed in source |
| `fix-about.ps1` | Patched broken links in about.html | Fixed in source |
| `fix-all-trailing-slashes.ps1` | Replaced `/services/foo/` with `/services/foo.html` | Fixed in source; netlify.toml also rewritten with wildcard |
| `fix-core-links.ps1` | Repaired broken nav links | Fixed in source |
| `fix-hero-images.ps1` | Injected `<img>` into empty `<div class="page-hero-bg">` (note: used wrong relative paths — fixed later) | Fixed in source |
| `fix-index-links.ps1` | Repaired broken links in index.html | Fixed in source |
| `fix-netlify-redirects.ps1` | Added per-page 301 redirects (replaced with wildcard in netlify.toml) | Fixed in netlify.toml |
| `fix-relative-links.ps1` | Repaired relative path errors | Fixed in source |
| `fix-section-ids.ps1` | Moved misplaced `<section id="...">` from header to body | Fixed in source |
| `fix-services-index-ids.ps1` | Fixed section IDs in services/index.html | Fixed in source |
| `fix-services-nav.ps1` | Repaired service category nav links | Fixed in source |
| `fix-venue-links.ps1` | Replaced `/services/venue.html` with `/services/#venue` | Fixed in source |
| `inject-service-images.ps1` | Inserted `<img>` tags into empty hero divs (BUG: used wrong relative paths, see note below) | Fixed in source; this was the source of the 19 broken image paths |
| `missing-css.ps1` | Appended missing CSS rules | Fixed in source |
| `fix-ga4-inner-script.ps1` | Re-inserted the inner GA4 `<script>` block that was accidentally deleted during the GA4 standardization migration. No longer needed; `standardize-ga4.ps1` now does this correctly. | Historical only |
| `cleanup-contact-info.ps1` | **DANGEROUS — DO NOT RUN**. Attempted to remove WhatsApp/social links from footers, but the regex `(?s)\s*<li>.*?WhatsApp.*?</li>` was over-greedy and ate everything from the first `<li>` in the file (the nav) up to the `</li>` containing WhatsApp, destroying `<main>` and `<footer>` opening tags in 9 files. All affected files were rewritten from scratch. The contact-info cleanup that was intended is now baked into the source files. | **DO NOT RUN** — kept for historical reference only |

## The image path bug

`inject-service-images.ps1` and `fix-hero-images.ps1` both inserted
`<img src="images/foo.png">` into files located at
`services/<category>/<service>.html`. Since those pages are two directories
deep, the relative path should be `../../images/foo.png`. All 19 service
pages had this bug; the images would 404 in production. Fixed manually by
replacing `src="images/` with `src="../../images/` across all service pages.

## If you need to debug what one of these did

Open the script in a text editor — they're all self-contained and well-commented.
They don't modify the filesystem unless you run them, so reading them is safe.
