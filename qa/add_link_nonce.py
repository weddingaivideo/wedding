"""P3-3 step 2: Add nonce="__CSP_NONCE__" placeholder to all <link> tags that
have an inline event handler (currently just `onload="this.media='all'"` on
the async-stylesheet loader). Without a nonce, CSP blocks the inline event
handler and styles.min.css never switches from media="print" to media="all"
→ subpage layout collapses to browser defaults.

After this edit, _middleware.js will:
  1. Generate a per-request nonce
  2. Replace all __CSP_NONCE__ with the real nonce (already covers <script>);
     this script additionally puts the placeholder on the <link> tag itself
  3. CSP allows the onload handler to fire → stylesheet loads → layout works

Re-run safety: skips <link> tags that already have a nonce.
"""
import re
import shutil
from pathlib import Path

ROOT = Path('.')
EXCLUDE = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n',
           'js', 'styles', 'scripts', 'docs', 'private', 'internal-tools',
           'tools', 'config', 'node_modules'}
NONCE = '__CSP_NONCE__'

# Match a <link ...> tag that has an on* event handler but no nonce=
LINK_RE = re.compile(
    r'(<link\b[^>]*?\bon(?:load|error|click|focus|blur|change|submit|'
    r'mouseover|mouseout|input|keydown|keyup)\s*=[^>]*?)(/?>)',
    re.IGNORECASE,
)

files = [p for p in ROOT.rglob('*.html')
         if not (set(str(x) for x in p.parts) & EXCLUDE)]

backup = ROOT / 'tmp' / 'link-nonce-backup'
backup.mkdir(parents=True, exist_ok=True)

count_files = 0
count_links = 0
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    orig = text

    def add_nonce(m):
        opening = m.group(1)
        closing = m.group(2)
        if 'nonce=' in opening:
            return m.group(0)  # already has nonce, leave alone
        # Insert nonce right after the tag name "link" so it's grouped with
        # other core attributes (rel/href), not at the end where some HTML
        # serializers drop unknown void-element attributes.
        new_opening = re.sub(
            r'^<link\b',
            f'<link nonce="{NONCE}"',
            opening,
            count=1,
        )
        return new_opening + closing

    new = LINK_RE.sub(add_nonce, text)

    if new != orig:
        bp = backup / f'{f.relative_to(ROOT)}.bak'
        bp.parent.mkdir(parents=True, exist_ok=True)
        if not bp.exists():
            shutil.copy2(f, bp)
        f.write_text(new, encoding='utf-8')
        count_files += 1
        # Count how many links we touched in this file
        count_links += len(LINK_RE.findall(orig)) - len(
            [m for m in LINK_RE.finditer(new) if 'nonce=' not in m.group(1)]
        )

print(f'Added link nonce to {count_links} <link> tags in {count_files} files')
print(f'Backup: {backup}')

# Verify
print('\n=== Post-edit verification ===')
total = 0
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    n = len(re.findall(rf'<link[^>]*?\bnonce="{NONCE}"', text))
    total += n
print(f'Total <link nonce="{NONCE}">: {total} (expected ~73)')

# Sanity: any link with on*= still missing nonce?
missing = 0
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    for m in re.finditer(r'<link\b[^>]*?>', text):
        tag = m.group(0)
        if re.search(r'\bon(?:load|error|click|focus|blur|change|submit|'
                     r'mouseover|mouseout|input|keydown|keyup)\s*=',
                     tag, re.IGNORECASE) and 'nonce=' not in tag:
            missing += 1
            print(f'  MISSING: {f.relative_to(ROOT)} → {tag[:100]}')
print(f'Links with on*= but no nonce: {missing} (expected 0)')
