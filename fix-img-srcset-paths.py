"""
Fix all <img srcset="..."> that have bare filenames but the corresponding
<img src="..."> has a path prefix.

Pattern: for every <img src="path/to/foo.png" srcset="foo-360.png 360w, ...">
the srcset URLs need to be prefixed with "path/to/" so they resolve correctly.

Also fix double-prefix bug introduced earlier: "images/images/foo.png"
should be "images/foo.png".

Idempotent.
"""
import re
from pathlib import Path

ROOT = Path('.')
files = list(ROOT.rglob('*.html'))
files = [p for p in files if p.name != 'google-site-verification.html']

# Find an <img ...> tag and extract src + srcset
IMG_TAG_PAT = re.compile(r'<img\s+([^>]*?)/?>', re.DOTALL)
SRC_PAT = re.compile(r'src="([^"]+)"')
SRCSET_PAT = re.compile(r'srcset="([^"]+)"')

# Detect bare filename (no path separator)
BARE_URL_PAT = re.compile(r'(?<!/)(\b[a-z][a-z0-9_\-]+\.(jpg|jpeg|png|webp|avif))\s+(\d+w)', re.IGNORECASE)

def get_prefix_from_src(src: str) -> str:
    """Extract the directory prefix from an src attribute, e.g. 'images/'."""
    p = Path(src)
    parent = str(p.parent).replace('\\', '/')
    if parent == '.':
        return ''
    return parent + '/'

def get_prefix_from_srcset_url(url: str) -> str:
    """If URL starts with images/ or ../../images/, return the prefix."""
    if '/' in url:
        return ''
    return None  # bare

def fix_img_srcset(content: str) -> str:
    """For every <img> tag, fix its srcset to use the correct path prefix."""
    def replace_img(m):
        attrs = m.group(1)
        src_m = SRC_PAT.search(attrs)
        srcset_m = SRCSET_PAT.search(attrs)
        if not src_m or not srcset_m:
            return m.group(0)
        src = src_m.group(1)
        srcset = srcset_m.group(1)
        # Get the correct prefix from src
        correct_prefix = get_prefix_from_src(src)
        if not correct_prefix:
            return m.group(0)  # src has no path, no fix needed
        # Split srcset entries
        new_entries = []
        for entry in srcset.split(','):
            entry = entry.strip()
            if not entry:
                continue
            # Split URL and width descriptor
            parts = entry.rsplit(' ', 1)
            if len(parts) != 2:
                new_entries.append(entry)
                continue
            url, w = parts
            # Check if URL has a path or is bare
            if '/' in url:
                # Check for double-prefix bug: "images/images/..." or "../../images/images/..."
                # Strip the redundant "images/" inside
                if 'images/images/' in url:
                    url = url.replace('images/images/', 'images/', 1)
                new_entries.append(f'{url} {w}')
            else:
                # Bare URL — add the correct prefix
                new_entries.append(f'{correct_prefix}{url} {w}')
        new_srcset = ', '.join(new_entries)
        new_attrs = re.sub(r'srcset="[^"]+"', f'srcset="{new_srcset}"', attrs, count=1)
        # Preserve self-closing slash
        return f'<img {new_attrs}>'
    return IMG_TAG_PAT.sub(replace_img, content)

# Also fix <source srcset="images/images/..."> double-prefix
SOURCE_SRCSET_PAT = re.compile(r'(<source\s+[^>]*?srcset=")([^"]+)("[^>]*>)')
def fix_source_srcset(content: str) -> str:
    def replace_src(m):
        prefix = m.group(1)
        srcset = m.group(2)
        suffix = m.group(3)
        new_srcset = srcset.replace('images/images/', 'images/')
        return prefix + new_srcset + suffix
    return SOURCE_SRCSET_PAT.sub(replace_src, content)

n = 0
for f in sorted(files):
    text = f.read_text(encoding='utf-8')
    new = fix_img_srcset(text)
    new = fix_source_srcset(new)
    if new != text:
        f.write_text(new, encoding='utf-8')
        n += 1

print(f"Done. {n} file(s) fixed")
