"""Remove the async-print-media-onload stylesheet trick from all 73 HTMLs.

Why: Chrome's strict-CSP mode hides the nonce attribute from element.nonce
/ getAttribute('nonce') on every element, including <link>. The CSP spec
rejects the inline onload handler when element.nonce is empty, even though
the parser recorded the real nonce at parse time. The 'unsafe-inline' escape
hatch is ignored as soon as any nonce/hash is present in the source list.

Fix: replace `media="print" onload="this.media='all'"` with nothing, leaving
the link as a plain blocking stylesheet. Critical CSS stays inline in
<style id="critical-css"> for first-paint, so FCP/LCP impact is minimal.

Also strip the now-redundant nonce="__CSP_NONCE__" we added in an earlier
attempt — without onload there is no inline event handler for it to unlock.
"""
import re
import shutil
from pathlib import Path

ROOT = Path('.')
EXCLUDE = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n',
           'js', 'styles', 'scripts', 'docs', 'private', 'internal-tools',
           'tools', 'config', 'node_modules'}

# Match: nonce="__CSP_NONCE__" rel="stylesheet" href="X" media="print" onload="this.media='all'"
# Replace with: rel="stylesheet" href="X"
LINK_RE = re.compile(
    r'<link\s+nonce="__CSP_NONCE__"\s+rel="stylesheet"\s+href="([^"]+)"\s+media="print"\s+onload="this\.media=\'all\'"\s*>'
)

files = [p for p in ROOT.rglob('*.html')
         if not (set(str(x) for x in p.parts) & EXCLUDE)]

backup = ROOT / 'tmp' / 'onload-removed-backup'
backup.mkdir(parents=True, exist_ok=True)

count_files = 0
count_links = 0
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    orig = text

    new, n = LINK_RE.subn(r'<link rel="stylesheet" href="\1">', text)
    if new != orig:
        bp = backup / f'{f.relative_to(ROOT)}.bak'
        bp.parent.mkdir(parents=True, exist_ok=True)
        if not bp.exists():
            shutil.copy2(f, bp)
        f.write_text(new, encoding='utf-8')
        count_files += 1
        count_links += n

print(f'Stripped onload=async from {count_links} <link> tags in {count_files} files')
print(f'Backup: {backup}')

# Verify
print('\n=== Post-edit verification ===')
remaining = 0
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    n = len(re.findall(r'media="print".*?onload="this\.media=\'all\'"', text))
    remaining += n
print(f'Remaining onload=async links: {remaining} (expected 0)')

# Also check link rel="preload" still there
preload_count = 0
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    preload_count += len(re.findall(r'<link rel="preload" href="/styles\.min\.css', text))
print(f'Preload links preserved: {preload_count} (expected ~73)')
