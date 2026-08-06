"""
P2-1: Clean up scripts/ and qa/ directories.

Strategy:
  1) Delete .txt / .log / .pyc (debug output, 0 value, no history)
  2) Archive (move, not delete) historical one-off fix / debug / test / audit
     scripts to scripts/archive/2026-07-28/. Kept for 6 months in case a
     future regression needs the inverse-fix (cf. AGENTS.md "history
     of past scripts" convention).
  3) Keep active scripts: anything referenced by CI / pre-deploy-check.ps1
     / AGENTS.md / deploy.ps1 itself.

After this, .assetsignore already excludes scripts/, qa/, *.txt, *.pyc, and
__pycache__/ so deploy is unaffected. The archive directory itself must
also be .assetsignore'd to prevent accidental deployment.
"""
import os
import shutil
from pathlib import Path

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
SCRIPTS = ROOT / "scripts"
QA = ROOT / "qa"
ARCHIVE = SCRIPTS / "archive" / "2026-07-28"
ARCHIVE_SCRIPTS = ARCHIVE / "scripts"
ARCHIVE_QA = ARCHIVE / "qa"
ARCHIVE_PYC = ARCHIVE / "__pycache__"

# ---- Active (keep) ----
ACTIVE_SCRIPTS = {
    "deploy.ps1",                # main deploy entry
    "check_langs_sync.py",       # CI step
    "check-seo-lengths.py",      # pre-deploy-check.ps1 step
    "standardize-ga4.ps1",       # referenced by AGENTS.md
    "set-cloudflare-secrets.ps1", # operational tool
    "submit-indexnow.ps1",       # called by deploy.ps1
    "bump_cache_version.py",     # referenced by AGENTS.md
    "sync_langs_redirects.py",   # referenced by AGENTS.md
    "inject_langs_preload.py",   # active infra script
    "inject_sw_register.py",     # active infra script
    "generate-blog.py",          # blog content generator
    "fix_p0_4_i18n_keys.py",     # P0-4 fix (this session), kept for re-run
    "INDEX.md",                  # navigation index for active scripts
    "README.md",                 # scripts directory docs
}

ACTIVE_QA = {
    "full_qa.py",                # CI + pre-deploy
    "gen_sitemap.py",            # CI + pre-deploy
    "verify_sitemap.py",         # CI
    "test_accept_lang.py",       # historical reports
    "bump_i18n_version.py",      # historical CI / version bump
    "list_broken.py",            # P0-2 helper
    "fix_p0_2_crosslinks.py",    # P0-2 fix
    "verify_p1_1.py",            # P1-1 verification
    "bump_cache_to_3_22.py",     # P1-2 cache-buster bump
    "cleanup_scripts_2026_07_28.py",  # this script — keep so it can be re-run
    "REPORT_2026-07-27.md",              # historical report
    "REPORT_ACCEPT_LANG_2026-07-27.md",  # historical report
    "REPORT_I18N_URLS_2026-07-27.md",    # historical report
}

# ---- Step 1: delete debug output (.txt / .log / .pyc / __pycache__/) ----
deleted = []
for d in (SCRIPTS, QA, ROOT):
    for p in d.rglob("*"):
        if not p.is_file():
            continue
        # Don't touch README.md / INDEX.md even if their content looks like a log
        if p.name in {"README.md", "INDEX.md", "REPORT_2026-07-27.md",
                      "REPORT_ACCEPT_LANG_2026-07-27.md", "REPORT_I18N_URLS_2026-07-27.md"}:
            continue
        if p.suffix in {".txt", ".log", ".pyc"}:
            deleted.append(p)
            p.unlink()

# Also delete the top-level __pycache__ directory if it became empty
for d in (ROOT, SCRIPTS, QA):
    pc = d / "__pycache__"
    if pc.exists() and pc.is_dir() and not any(pc.iterdir()):
        pc.rmdir()
        deleted.append(pc)

print(f"Step 1: deleted {len(deleted)} debug-output files / dirs")
for p in deleted:
    print(f"  {p.relative_to(ROOT)}")

# ---- Step 2: archive historical scripts ----
moved = []
for f in SCRIPTS.iterdir():
    if not f.is_file():
        continue
    if f.name in ACTIVE_SCRIPTS:
        continue
    # Don't move the archive itself
    if f.name == "archive":
        continue
    dest = ARCHIVE_SCRIPTS / f.name
    shutil.move(str(f), str(dest))
    moved.append(dest)

for f in QA.iterdir():
    if not f.is_file():
        continue
    if f.name in ACTIVE_QA:
        continue
    dest = ARCHIVE_QA / f.name
    shutil.move(str(f), str(dest))
    moved.append(dest)

print(f"\nStep 2: archived {len(moved)} historical scripts")
for p in moved:
    print(f"  {p.relative_to(ROOT)}")

# ---- Step 3: write a README at the archive root so future readers know ----
readme = """# Archive 2026-07-28

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
  - __pycache__/: compiled bytecode snapshots (regenerated on import)

For active scripts, see:
  - scripts/ (deploy, i18n sync, cache buster bump, etc.)
  - qa/ (full_qa, gen_sitemap, verify_sitemap, test_accept_lang, etc.)
"""
(ARCHIVE / "README.md").write_text(readme, encoding="utf-8")
print(f"\nWrote {ARCHIVE / 'README.md'}")

print(f"\nDone. Archive at: {ARCHIVE.relative_to(ROOT)}")
