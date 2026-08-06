"""
Fix: Add missing <!DOCTYPE html> to HTML files that lost it.

Without DOCTYPE, browsers render in Quirks Mode (IE5 box model),
which breaks ALL layout (box-sizing, flexbox, grid, margins, etc.).

67 files were affected. This script adds DOCTYPE back without
changing any other content.
"""
from pathlib import Path

ROOT = Path(__file__).parent.parent
EXCLUDE = {'tmp', 'qa', 'scripts', '__pycache__', 'i18n', 'js', 'styles',
           'functions', 'admin', 'internal-tools', 'tools', 'node_modules',
           '.github', 'docs', '100 blog'}

DOCTYPE = '<!DOCTYPE html>\n'

files = [p for p in ROOT.rglob('*.html')
         if not (set(str(x) for x in p.parts) & EXCLUDE)]

count = 0
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    if text.startswith('<!DOCTYPE'):
        continue
    # Check if maybe there's a BOM or whitespace before
    stripped = text.lstrip('\ufeff \t\r\n')
    if stripped.startswith('<!DOCTYPE'):
        continue
    # Add DOCTYPE
    # If file starts with BOM, keep it
    if text.startswith('\ufeff'):
        new_text = '\ufeff' + DOCTYPE + text.lstrip('\ufeff')
    else:
        new_text = DOCTYPE + text.lstrip('\r\n')
    f.write_text(new_text, encoding='utf-8')
    rel = f.relative_to(ROOT)
    print(f'  [FIXED] {rel}')
    count += 1

print(f'\nTotal fixed: {count} files')

# Verify
missing = 0
for f in files:
    text = f.read_text(encoding='utf-8', errors='ignore')
    if not text.lstrip('\ufeff \t\r\n').startswith('<!DOCTYPE'):
        missing += 1
        print(f'  [STILL MISSING] {f.relative_to(ROOT)}')

if missing:
    print(f'\n[WARN] {missing} files still missing DOCTYPE')
else:
    print(f'\n[OK] All {len(files)} HTML files have DOCTYPE')
