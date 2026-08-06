"""
Inject width / height / loading / fetchpriority into <img> tags.

For every <img> in every HTML page:
  - If no width / height: look up the real dimensions of the referenced image
    (Pillow) and inject them. CLS win.
  - If no loading="lazy": add loading="lazy" (except for LCP candidate: the first
    image on the home page hero gets loading="eager" + fetchpriority="high").

Idempotent.
"""
import re
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).parent
IMG_DIR = ROOT / "images"

# Image dimension cache (avoid re-opening same file)
_dim_cache = {}

def get_dim(local_path: Path):
    if local_path in _dim_cache:
        return _dim_cache[local_path]
    if not local_path.exists():
        return None, None
    try:
        with Image.open(local_path) as im:
            im.load()
            _dim_cache[local_path] = (im.size[0], im.size[1])
            return im.size
    except Exception:
        return None, None

def resolve_img_path(src: str, html_file: Path):
    """Resolve a src like 'images/foo.png' or '../../images/foo.png' to a real local file."""
    if src.startswith(("http://", "https://", "data:", "//")):
        return None
    # Strip leading slashes and query
    src = src.split("?")[0].lstrip("/")
    # html_file parent is the page; src is relative to that
    return (html_file.parent / src).resolve()

def patch_img(match, html_file, first_in_doc):
    full = match.group(0)
    # Don't double-process (idempotency)
    attrs = full
    has_width  = re.search(r'\bwidth\s*=',  attrs)
    has_height = re.search(r'\bheight\s*=', attrs)
    has_loading = re.search(r'\bloading\s*=', attrs)
    has_fetch = re.search(r'\bfetchpriority\s*=', attrs)
    src_m = re.search(r'src\s*=\s*"([^"]+)"', attrs)
    if not src_m:
        return full
    src = src_m.group(1)

    inserts = []
    # Dimensions
    if not has_width or not has_height:
        img_path = resolve_img_path(src, html_file)
        w, h = get_dim(img_path) if img_path else (None, None)
        if w and h:
            if not has_width:
                inserts.append(f' width="{w}"')
            if not has_height:
                inserts.append(f' height="{h}"')
    # Lazy loading (default)
    if not has_loading:
        inserts.append(' loading="lazy"')
    # Fetchpriority (mark LCP candidate)
    if not has_fetch:
        # Heuristic: first <img> in any HTML is the LCP candidate
        if first_in_doc:
            inserts.append(' fetchpriority="high"')
            # And don't lazy-load the LCP image
            inserts = [x for x in inserts if 'loading="lazy"' not in x]
            inserts.append(' loading="eager"')
    if not inserts:
        return full
    # Insert before the closing > (or />)
    if full.rstrip().endswith('/>'):
        new = full.rstrip()[:-1].rstrip() + ''.join(inserts) + ' />'
    else:
        new = full.rstrip()[:-1].rstrip() + ''.join(inserts) + '>'
    return new

def process(html_path: Path):
    text = html_path.read_text(encoding='utf-8')
    original = text

    # Find all <img> tags
    pattern = re.compile(r'<img\b[^>]*?>', re.DOTALL)
    out_chunks = []
    last = 0
    first = True
    for m in pattern.finditer(text):
        out_chunks.append(text[last:m.start()])
        # Wrap match with metadata
        out_chunks.append(patch_img(m, html_path, first))
        last = m.end()
        first = False
    out_chunks.append(text[last:])
    new_text = ''.join(out_chunks)

    if new_text != original:
        html_path.write_text(new_text, encoding='utf-8')
        return True
    return False

def main():
    html_files = [p for p in ROOT.rglob("*.html") if p.name != "google-site-verification.html"]
    n = 0
    for p in sorted(html_files):
        if process(p):
            n += 1
            print(f"[+] {p.relative_to(ROOT)}")
    print(f"\nDone. patched {n} file(s)")

if __name__ == "__main__":
    main()
