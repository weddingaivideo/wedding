"""
P0-2: Fix 28 broken local hrefs across services.

The 5 paths pointing to /services/video-enhancement/<X>/ are wrong — those X
actually live under /services/personalization/. This is leftover from an
earlier i18n injection pass.

Replace:
  /services/video-enhancement/pet-wedding/        -> /services/personalization/pet-wedding/
  /services/video-enhancement/wedding-trailer/    -> /services/personalization/wedding-trailer/
  /services/video-enhancement/meme-generator/     -> /services/personalization/meme-generator/
  /services/video-enhancement/multilingual/       -> /services/personalization/multilingual/
  /services/video-enhancement/ai-video-generator/ -> /services/personalization/ai-video-generator/
  /services/video-enhancement/cartoon-style/      -> /services/personalization/cartoon-style/

Note: /services/video-enhancement/slow-motion/ is a REAL path and must stay.
"""
import re
from pathlib import Path
ROOT = Path(r'C:\Users\qiaoshan\.openclaw\workspace\weddingai')

# Service slugs that actually live under /services/personalization/
PERSONALIZATION_SLUGS = {
    'pet-wedding', 'wedding-trailer', 'meme-generator', 'multilingual',
    'ai-video-generator', 'cartoon-style',
}

# Build regex matching all the wrong hrefs
slug_alt = '|'.join(re.escape(s) for s in PERSONALIZATION_SLUGS)
WRONG_RE = re.compile(
    rf'href="(/services/video-enhancement/)({slug_alt})(/[a-z0-9_-]*\.html)?/"'
)

def fix_html_file(p: Path) -> int:
    text = p.read_text(encoding='utf-8', errors='ignore')
    new_text, n = WRONG_RE.subn(r'href="/services/personalization/\2/"', text)
    # Also handle .html form
    new_text, n2 = WRONG_RE.subn(r'href="/services/personalization/\2\3/"', new_text)
    n = n + n2 if n2 else n
    if new_text != text:
        p.write_text(new_text, encoding='utf-8')
    return n

# Note: the WRONG_RE above only catches the no-suffix /personalization/<slug>/ form.
# The .html form is handled by separate re-do because the pattern has variable trailing.
# Actually the regex `(/[a-z0-9_-]*\.html)?` makes it ambiguous. Simpler approach: do
# 2 separate replaces.

REPLACEMENTS = [
    ('/services/video-enhancement/pet-wedding/', '/services/personalization/pet-wedding/'),
    ('/services/video-enhancement/wedding-trailer/', '/services/personalization/wedding-trailer/'),
    ('/services/video-enhancement/meme-generator/', '/services/personalization/meme-generator/'),
    ('/services/video-enhancement/multilingual/', '/services/personalization/multilingual/'),
    ('/services/video-enhancement/ai-video-generator/', '/services/personalization/ai-video-generator/'),
    ('/services/video-enhancement/cartoon-style/', '/services/personalization/cartoon-style/'),
    # .html forms
    ('/services/video-enhancement/pet-wedding.html', '/services/personalization/pet-wedding/'),
    ('/services/video-enhancement/wedding-trailer.html', '/services/personalization/wedding-trailer/'),
    ('/services/video-enhancement/meme-generator.html', '/services/personalization/meme-generator/'),
    ('/services/video-enhancement/multilingual.html', '/services/personalization/multilingual/'),
    ('/services/video-enhancement/ai-video-generator.html', '/services/personalization/ai-video-generator/'),
    ('/services/video-enhancement/cartoon-style.html', '/services/personalization/cartoon-style/'),
]

def fix_file(p: Path) -> int:
    text = p.read_text(encoding='utf-8', errors='ignore')
    n = 0
    for old, new in REPLACEMENTS:
        if old in text:
            count = text.count(old)
            text = text.replace(old, new)
            n += count
    if n:
        p.write_text(text, encoding='utf-8')
    return n

# Skip /search/ because /${item.url} is a JS template literal
SKIP_DIRS = {'admin', 'functions', 'tmp', '__pycache__', 'qa', 'i18n', 'js', 'styles', 'scripts', 'docs', 'search'}

total_files = 0
total_changes = 0
for f in ROOT.rglob('*.html'):
    parts = {str(p) for p in f.parts}
    if parts & SKIP_DIRS:
        continue
    n = fix_file(f)
    if n:
        total_files += 1
        total_changes += n
        rel = f.relative_to(ROOT)
        print(f'  {rel}: {n} replacements')
print(f'\nTotal: {total_changes} hrefs fixed in {total_files} files')
