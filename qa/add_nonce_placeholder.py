"""P3-3 step 1: Add nonce="__CSP_NONCE__" placeholder to all inline <script>
tags in HTML files. The middleware will replace the placeholder with a
real per-request nonce.

Rules:
  - <script>...</script> (no src, has body) → add nonce=
  - <script src="..."></script> (external) → no change
  - <script type="application/ld+json">...</script> → also add nonce=
  - <script></script> (empty) → leave alone (no need for nonce)

After this edit, _middleware.js will:
  1. Generate a per-request nonce
  2. Replace all __CSP_NONCE__ with the real nonce
  3. Send Content-Security-Policy header with 'nonce-XXX' instead of 'unsafe-inline'
"""
import re
from pathlib import Path
import shutil

ROOT = Path('.')
EXCLUDE = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}
files = [p for p in ROOT.rglob('*.html') if not (set(str(x) for x in p.parts) & EXCLUDE)]

backup = ROOT / 'tmp' / 'nonce-placeholder-backup'
backup.mkdir(parents=True, exist_ok=True)

count_files = 0
count_scripts = 0
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    orig = text

    # Find <script ...>...</script> where the opening tag has no src= and is not empty
    # Pattern: <script(attributes)>body</script>
    # We add nonce="__CSP_NONCE__" to the opening tag (or replace if exists)

    file_count = [0]

    def add_nonce(m):
        opening = m.group(1)
        body = m.group(2)
        # Skip if already has nonce
        if 'nonce=' in opening:
            return m.group(0)
        # Skip if has src= (external)
        if re.search(r'\bsrc\s*=', opening):
            return m.group(0)
        # Skip if empty body
        if not body.strip():
            return m.group(0)
        file_count[0] += 1
        # Build new opening tag with nonce
        new_opening = opening.rstrip()
        if not new_opening.endswith('>'):
            return m.group(0)
        new_opening = new_opening[:-1].rstrip() + ' nonce="__CSP_NONCE__">'
        return new_opening + body + '</script>'

    new = re.sub(
        r'(<script(?![^>]*\bsrc=)[^>]*>)([\s\S]*?)</script>',
        add_nonce,
        text
    )

    if new != orig:
        bp = backup / f'{f.relative_to(ROOT)}.bak'
        bp.parent.mkdir(parents=True, exist_ok=True)
        if not bp.exists():
            shutil.copy2(f, bp)
        f.write_text(new, encoding='utf-8')
        count_files += 1
        count_scripts += file_count[0]

print(f'Added nonce placeholder to {count_scripts} inline scripts in {count_files} files')
print(f'Backup: {backup}')

# Verify
print('\n=== Post-edit verification ===')
for f in files[:3]:
    text = f.read_text(encoding='utf-8', errors='ignore')
    n_with = len(re.findall(r'nonce="__CSP_NONCE__"', text))
    print(f'  {f.relative_to(ROOT)}: {n_with} nonce placeholders')
