#!/usr/bin/env python3
"""
Apply lazy-video loading pattern to <video> tags in HTML files.

What it does (per <video ...> tag):
  1. Replaces preload="metadata" with preload="none" (browser fetches zero bytes
     initially).
  2. Adds data-lazy-video attribute (signal for lazy-videos.js to control it).
  3. Adds controls attribute on case-study videos (so user can pause/replay).
     Hero video is detected by class="hero-video" — left alone on controls.

Idempotent: re-running on already-converted files is a no-op.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
# Match a full <video ...> opening tag (no newlines inside, multi-line OK).
VIDEO_TAG = re.compile(r'<video\b[^>]*>', re.IGNORECASE | re.DOTALL)

# Files to process. Each value is a Path.
TARGETS = [
    ROOT / "index.html",
    ROOT / "gallery" / "index.html",
]


def transform_video_tag(tag_html: str) -> str:
    """Mutate one <video ...> opening tag in-place."""
    # Skip if already has the data-lazy-video marker (idempotency).
    if "data-lazy-video" in tag_html:
        return tag_html

    # 1. preload="metadata" → preload="none"
    tag_html = re.sub(
        r'preload="metadata"',
        'preload="none"',
        tag_html,
        flags=re.IGNORECASE,
    )

    # 2. Add data-lazy-video attribute right before the closing >.
    #    Use leading space (HTML spec allows whitespace between attributes).
    tag_html = tag_html.rstrip(">") + ' data-lazy-video>'

    # 3. Add controls on case-study videos.
    #    Hero video has class="hero-video" — leave it alone.
    #    Detect case-study: has width="..." AND poster="..." AND no class="hero-video"
    is_hero = 'class="hero-video"' in tag_html
    if not is_hero and ' controls' not in tag_html and 'controls ' not in tag_html:
        # Insert controls right after <video
        tag_html = re.sub(
            r'<video\b',
            '<video controls',
            tag_html,
            count=1,
            flags=re.IGNORECASE,
        )

    return tag_html


def process_file(path: Path) -> tuple[int, int]:
    """Return (total_videos, modified_videos) for the file."""
    src = path.read_text(encoding="utf-8")
    matches = list(VIDEO_TAG.finditer(src))
    if not matches:
        return 0, 0

    out = []
    last = 0
    modified = 0
    for m in matches:
        out.append(src[last:m.start()])
        original = m.group(0)
        transformed = transform_video_tag(original)
        if transformed != original:
            modified += 1
        out.append(transformed)
        last = m.end()
    out.append(src[last:])

    if modified > 0:
        path.write_text("".join(out), encoding="utf-8")

    return len(matches), modified


def main() -> int:
    total_videos = 0
    total_modified = 0
    for path in TARGETS:
        if not path.exists():
            print(f"[skip] {path} not found")
            continue
        n, m = process_file(path)
        print(f"[ok]   {path.relative_to(ROOT)}: {n} videos, {m} modified")
        total_videos += n
        total_modified += m
    print(f"\nTotal: {total_videos} videos, {total_modified} modified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
