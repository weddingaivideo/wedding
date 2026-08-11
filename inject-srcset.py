"""
Inject srcset + sizes into <img> tags AND into <source> tags inside <picture>.

For every <img src="images/foo.png"> in every HTML page, find the matching
sized variants on disk and build:
  * A webp srcset (if .webp variants exist)
  * A fallback srcset (jpg or png)
  * A sizes attribute (chosen by the image kind)

Idempotent. Skips images with no variants. Preserves width/height/alt/etc.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
IMG_DIR = ROOT / "images"

# Kind classifier — same as the generator
NAMED_KINDS = {
    "avatar-jennifer": "avatar", "avatar-mike-rachel": "avatar",
    "avatar-priya-arjun": "avatar", "avatar-sophie-david": "avatar",
    "avatar-emma": "avatar", "avatar-carolina": "avatar",
    "avatar-margaret": "avatar", "avatar-sarah-james": "avatar",
    "avatar-diego": "avatar", "avatar-aisha-karim": "avatar",
    "avatar-thomas": "avatar", "avatar-leah-josh": "avatar",
    "logo-full": "logo", "logo-icon": "icon",
    "hero-wedding-vineyard": "hero",
    "favicon": "favicon",
}
CARD_KEYWORDS = ["service", "catalog", "preset", "cartoon-", "meme-",
                 "tribute-", "familymsg-", "petwedding-", "trailer-feat-",
                 "wedding-restoration-", "wedding-trailer-",
                 "slow-motion-first-dance", "family-tribute-hologram",
                 "interactive-screen", "realtime-cut", "guide-", "avatar-",
                 "testimonial-", "order-form", "pricing-cards", "live-comments",
                 "multilingual-split", "ai-video-generator-workspace",
                 "family-tribute-frame", "family-message-videocall",
                 "cartoon-ghibli-style", "cartoon-realistic-combo",
                 "pet-wedding-golden-retrievers", "wedding-restoration-vhs-tv",
                 "gallery-collage"]
# Whitelist of all known variant sizes. Used to decide whether a `<img src>`
# that already ends in -NNN is a true variant (skip rewriting) or a
# year/slug (rewrite and add srcset). 2026-08-10.
KNOWN_SIZES = {178, 256, 360, 480, 512, 640, 720, 960, 1024, 1280, 1536, 1600, 1920, 2048, 2560}

KIND_SIZES_ATTR = {
    "avatar":       "(max-width: 600px) 48px, 48px",
    "logo":         "(max-width: 600px) 178px, 356px",
    "hero":         "(max-width: 600px) 100vw, (max-width: 1024px) 100vw, 100vw",
    "service-card": "(max-width: 600px) 100vw, (max-width: 1024px) 50vw, 33vw",
    "case-card":    "(max-width: 600px) 100vw, (max-width: 1024px) 50vw, 33vw",
    "icon":         "64px",
    "generic":      "(max-width: 600px) 100vw, (max-width: 1024px) 50vw, 33vw",
}
def classify(filename: str) -> str:
    base = Path(filename).stem
    if base in NAMED_KINDS:
        return NAMED_KINDS[base]
    for kw in CARD_KEYWORDS:
        if kw in base:
            return "service-card"
    if Path(filename).suffix.lower() == ".png":
        return "service-card"
    return "generic"

# Build a {stem: [variants]} index
# IMPORTANT: rglob, not iterdir. 2026-08-10 bug: iterdir() only indexed the
# top-level images/ directory, which silently skipped every variant living
# under images/<subdir>/ (e.g. all 600+ blog/hero/-360/-720/-1280 variants).
# find_variants() returned {} for those stems, so fix_plain bailed out and
# no srcset was injected for blog hero images. Recurse the whole tree.
VARIANT_INDEX = {}
for p in IMG_DIR.rglob("*"):
    if not p.is_file():
        continue
    # Non-greedy base + 3-4 digit size + lookbehind to prevent the "stem ends in
    # -NNNN" case (e.g. "...-2026") from being mis-parsed as base="...-202",
    # size=6. Also bound size to {3,4} digits to skip 1-2 digit tokens that
    # occasionally appear in real stems. Verified 2026-08-10 against all 3,886
    # images: 0 false matches on original (no -NNN) images.
    m = re.match(r"^(.+?)(?<!-\d)-(\d{3,4})\.(jpg|jpeg|png|webp)$", p.name, re.IGNORECASE)
    if not m:
        continue
    base, size_str, ext = m.group(1), m.group(2), m.group(3).lower()
    VARIANT_INDEX.setdefault(base.lower(), []).append((int(size_str), ext.lower(), p.name))

def find_variants(stem: str):
    """Return a dict like {'.webp': [(720, '...'), (1280, '...')], '.jpg': [...]}"""
    out = {}
    for size, ext, fname in VARIANT_INDEX.get(stem.lower(), []):
        key = "." + ext
        if key == ".jpeg":
            key = ".jpg"
        out.setdefault(key, []).append((size, fname))
    # sort each by size ascending
    for k in out:
        out[k].sort()
    return out

def build_srcset(variants):
    """Build srcset string from a list of (size, filename) pairs."""
    if not variants:
        return None
    return ", ".join(f"{fname} {w}w" for w, fname in variants)

def process_html(html_path: Path):
    text = html_path.read_text(encoding="utf-8")
    original = text

    # 1) Handle <picture><source srcset="..."><img src="..."></picture> blocks
    #    Replace single-srcset source with multi-size srcset, and add srcset/sizes to the img.
    picture_pat = re.compile(
        r'<picture>\s*<source\s+srcset="([^"]+)"\s+type="image/webp">\s*'
        r'<img\s+([^>]*?)src="([^"]+)"([^>]*?)\s*(\/?)>',
        re.DOTALL
    )
    def fix_picture(m):
        old_webp_src = m.group(1)
        before_src = m.group(2)
        img_src = m.group(3)
        after_src = m.group(4)
        self_close = m.group(5)

        # Resolve the actual image basename (from the webp src or img src)
        # old_webp_src is like "images/foo.webp" -> stem "foo"
        stem = Path(old_webp_src).stem
        variants = find_variants(stem)
        if not variants:
            return m.group(0)  # leave alone

        # Build webp srcset (if .webp variants exist)
        webp_srcset = build_srcset(variants.get(".webp", []))
        # Build fallback srcset (use original format)
        # Choose .jpg if any jpg variant exists, else .png
        fallback_ext = ".jpg" if ".jpg" in variants else (".png" if ".png" in variants else None)
        fallback_srcset = build_srcset(variants.get(fallback_ext, [])) if fallback_ext else None

        kind = classify(stem)
        sizes_attr = KIND_SIZES_ATTR.get(kind, KIND_SIZES_ATTR["generic"])

        # Rebuild the <source>
        new_source = f'<source srcset="{webp_srcset}" type="image/webp" sizes="{sizes_attr}">'

        # Rebuild the <img>:
        # - if has srcset, leave it; else inject fallback srcset
        # - inject sizes if missing
        img_attrs = (before_src + "src=\"" + img_src + "\"" + after_src).strip()
        if 'srcset=' not in img_attrs and fallback_srcset:
            img_attrs += f' srcset="{fallback_srcset}"'
        if 'sizes=' not in img_attrs:
            img_attrs += f' sizes="{sizes_attr}"'

        return f'<picture>{new_source}<img {img_attrs}{self_close}>'

    text = picture_pat.sub(fix_picture, text)

    # 2) Handle plain <img> tags NOT inside <picture> that we haven't touched
    #    (these are in pages that didn't have picture wrap, or older <img> tags)
    plain_pat = re.compile(r'<img\s+([^>]*?)src="([^"]+)"([^>]*?)\s*(\/?)>', re.DOTALL)

    def fix_plain(m):
        before_src = m.group(1)
        img_src = m.group(2)
        after_src = m.group(3)
        self_close = m.group(4)

        # Skip if this <img> is inside a <picture> we already rewrote.
        # Look back ~2 KB for an unclosed <picture>. A 300-char window was
        # too small: an avif+webp double-source <picture> with 712w/1280w
        # srcsets can be ~500-1000 chars, so the <picture> tag itself
        # landed outside the window and the inside-img got re-processed.
        # Fixed 2026-08-10.
        start = max(0, m.start() - 2000)
        prefix = text[start:m.start()]
        last_picture_open = prefix.rfind("<picture>")
        last_picture_close = prefix.rfind("</picture>")
        if last_picture_open > last_picture_close:
            return m.group(0)  # we're inside a picture, leave it alone

        # Only fix images that live in /images/ (skip remote / icons)
        if "images/" not in img_src and not img_src.startswith("images/"):
            return m.group(0)

        # Compute path relative to /images/
        src_name = Path(img_src).name
        stem = Path(src_name).stem
        # Skip favicon/logo-icon (special)
        if stem in ("favicon", "logo-icon"):
            return m.group(0)
        # If the src already points to a -NNN variant, don't double-wrap.
        # The old greedy regex `^(.+)-(\d+)$` mis-matched real stems ending
        # in -YYYY like "47-wedding-video-cost-2026" as base="...-202",
        # size=6 — so the check below would skip a bare src we DO want to
        # wrap. Use a KNOWN_SIZES whitelist instead. 2026-08-10.
        if "-" in stem:
            tail = stem.rsplit("-", 1)[1]
            if tail.isdigit() and int(tail) in KNOWN_SIZES:
                return m.group(0)
        variants = find_variants(stem)
        if not variants:
            return m.group(0)

        webp_srcset = build_srcset(variants.get(".webp", []))
        fallback_ext = ".jpg" if ".jpg" in variants else ".png"
        fallback_srcset = build_srcset(variants.get(fallback_ext, []))

        kind = classify(stem)
        sizes_attr = KIND_SIZES_ATTR.get(kind, KIND_SIZES_ATTR["generic"])

        # If both webp and fallback are available, wrap in <picture>
        if webp_srcset and fallback_srcset:
            new_source = f'<source srcset="{webp_srcset}" type="image/webp" sizes="{sizes_attr}">'
            img_attrs = (before_src + "src=\"" + img_src + "\"" + after_src).strip()
            if 'sizes=' not in img_attrs:
                img_attrs += f' sizes="{sizes_attr}"'
            return f'<picture>{new_source}<img {img_attrs}{self_close}></picture>'

        # Otherwise just add srcset + sizes to the existing img
        img_attrs = (before_src + "src=\"" + img_src + "\"" + after_src).strip()
        if 'srcset=' not in img_attrs and fallback_srcset:
            img_attrs += f' srcset="{fallback_srcset}"'
        if 'sizes=' not in img_attrs:
            img_attrs += f' sizes="{sizes_attr}"'
        return f'<img {img_attrs}{self_close}>'

    text = plain_pat.sub(fix_plain, text)

    if text != original:
        html_path.write_text(text, encoding="utf-8")
        return True
    return False

def main():
    # Skip backup/scratch directories. 2026-08-10: added after the script
    # accidentally rewrote private/.archive/_en_blog_backup/ (a pre-deploy
    # snapshot) and tmp/baseline-*.html (a manual reference copy), neither
    # of which should ever be touched by a build-time image optimizer.
    SKIP_DIRS = {"private", "tmp", "node_modules", ".git", ".github"}
    SKIP_FILE_TOKENS = (".bak.", ".pre-", "baseline-")

    def keep(p: Path) -> bool:
        if p.name == "google-site-verification.html":
            return False
        rel_parts = p.relative_to(ROOT).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            return False
        if any(tok in p.name for tok in SKIP_FILE_TOKENS):
            return False
        return True

    html_files = [p for p in ROOT.rglob("*.html") if keep(p)]
    n = 0
    for p in sorted(html_files):
        if process_html(p):
            n += 1
            print(f"[+] {p.relative_to(ROOT)}")
    print(f"\nDone. patched {n} file(s)")

if __name__ == "__main__":
    main()
