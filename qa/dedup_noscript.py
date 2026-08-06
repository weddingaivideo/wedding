"""P1-6: dedupe <link rel="stylesheet" href="/styles/i18n.css"> inside <noscript> blocks.
Many HTML files (from i18n_inject history) have 2 consecutive identical
i18n.css link tags inside noscript. Remove the duplicate.
Also fixes the blog/* pages where styles.min.css has no ?v= (line right before).
"""
import re
from pathlib import Path
import shutil

ROOT = Path('.')
EXCLUDE = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs'}

# Backup
backup = ROOT / 'tmp' / 'dedup-noscript-backup'
backup.mkdir(parents=True, exist_ok=True)

files = [p for p in ROOT.rglob('*.html') if not (set(str(x) for x in p.parts) & EXCLUDE)]

count = 0
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    orig = text

    # Find <noscript>...</noscript> blocks
    def fix_noscript(m):
        block = m.group(1)
        # Split into lines, dedupe identical <link> tags
        lines = block.splitlines(keepends=False)
        seen_i18n_css = False
        seen_styles_min = False
        out = []
        for line in lines:
            stripped = line.strip()
            # Dedupe i18n.css
            if 'href="/styles/i18n.css"' in stripped:
                if seen_i18n_css:
                    continue
                seen_i18n_css = True
            # Dedupe styles.min.css
            if 'href="/styles.min.css' in stripped:
                if seen_styles_min:
                    continue
                seen_styles_min = True
            out.append(line)
        return '<noscript>' + '\n    '.join(out) + '</noscript>'

    new = re.sub(r'<noscript>(.*?)</noscript>', fix_noscript, text, flags=re.DOTALL)

    # Also: if styles.min.css inside noscript has no ?v=, add it
    def add_v_to_min(m):
        block = m.group(1)
        # Find styles.min.css with no ?v= and add ?v=3.21
        block = re.sub(
            r'href="/styles\.min\.css"(?!\?v=)',
            'href="/styles.min.css?v=3.21"',
            block
        )
        return '<noscript>' + block + '</noscript>'
    new = re.sub(r'<noscript>(.*?)</noscript>', add_v_to_min, new, flags=re.DOTALL)

    if new != orig:
        bp = backup / f'{f.relative_to(ROOT)}.bak'
        bp.parent.mkdir(parents=True, exist_ok=True)
        if not bp.exists():
            shutil.copy2(f, bp)
        f.write_text(new, encoding='utf-8')
        count += 1

print(f'Fixed {count} files')
print(f'Backup: {backup}')
