# Archive 2026-07-28

Historical one-off fix / debug / test / audit scripts moved here on
2026-07-28 during P2-1 cleanup. Kept for 6 months (until 2027-01-28)
in case a future regression needs the inverse of a fix that's been
shipped.

Scripts in here MUST NOT be re-run. They were tied to the state of the
site on the day they were written; running them now will either be a
no-op or, worse, regress the site.

If you genuinely need a historical fix (e.g. user reports the same
issue returned), copy the script out, re-validate against current
site state, and adapt. Do not blindly re-run.

Categories by origin (rough):
  - scripts/ subdir: fix-* / debug-* / test-* / audit-* from 2026-07-20
    to 2026-07-27 mass-fix passes (see qa/REPORT_2026-07-27.md for context)
  - qa/ subdir: one-off i18n / blockquote / gallery fixes from the same
    period, plus inspector / counter / sample scripts used during the
    audits

Note (2026-07-28 follow-up): the `__pycache__/` subdirectory was deleted.
The 4 .pyc bytecode snapshots inside it (regenerated on every Python
import, 0 historical value) were dropped during the cleanup pass; only
the script .py source code was retained. If you ever need the bytecode
for some reason, re-run the original .py and Python will regenerate it.

For active scripts, see:
  - scripts/ (deploy, i18n sync, cache buster bump, etc.)
  - qa/ (full_qa, gen_sitemap, verify_sitemap, test_accept_lang, etc.)
