#!/usr/bin/env python3
"""
restructure-services-nav.py

Replaces the flat 11-item Services nav dropdown with a grouped 3-category
dropdown + "View all services" link, across all index.html files.

Drives the weddingai.video site audit fix for C-4 (nav overload) and H-5
(mobile nav). Idempotent: skips files that already have the grouped structure.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Old: flat 11-item nav-dropdown. Each file has exactly one <ul class="nav-dropdown"
# role="menu">...</ul> (the Services menu in the header). The footer Services list
# uses different markup (nav-list style), so this regex only matches the header.
OLD_NAV_RE = re.compile(
    r'<ul class="nav-dropdown" role="menu">[\s\S]*?</ul>',
    re.MULTILINE,
)

# New: 3 category groups + "View all" link. Reuses existing i18n keys so
# the middleware will translate the heading text per language.
NEW_NAV = '''<ul class="nav-dropdown nav-dropdown-grouped" role="menu">
                            <li class="nav-dropdown-group" role="none">
                                <div class="nav-dropdown-heading" role="presentation" data-i18n="search.strong_text.video_enhancement.98039549">Video Enhancement</div>
                                <ul role="menu">
                                    <li role="none"><a role="menuitem" href="/services/video-enhancement/slow-motion/" data-i18n="404.a_text.slow_motion.30129340">Slow Motion</a></li>
                                    <li role="none"><a role="menuitem" href="/services/video-enhancement/vintage-restoration/" data-i18n="404.a_text.vintage_restoration.91827364">Vintage Restoration</a></li>
                                </ul>
                            </li>
                            <li class="nav-dropdown-group" role="none">
                                <div class="nav-dropdown-heading" role="presentation" data-i18n="search.strong_text.personalization.44366515">Personalization</div>
                                <ul role="menu">
                                    <li role="none"><a role="menuitem" href="/services/personalization/wedding-trailer/" data-i18n="404.a_text.wedding_trailer.04692297">Wedding Trailer</a></li>
                                    <li role="none"><a role="menuitem" href="/services/personalization/ai-video-generator/" data-i18n="404.a_text.ai_video_generator.39420322">AI Video Generator</a></li>
                                    <li role="none"><a role="menuitem" href="/services/personalization/pet-wedding/" data-i18n="404.a_text.pet_wedding.23911820">Pet Wedding</a></li>
                                    <li role="none"><a role="menuitem" href="/services/personalization/multilingual/" data-i18n="404.a_text.multilingual.74639147">Multilingual</a></li>
                                    <li role="none"><a role="menuitem" href="/services/personalization/cartoon-style/" data-i18n="404.a_text.cartoon_style.16664616">Cartoon Style</a></li>
                                    <li role="none"><a role="menuitem" href="/services/personalization/meme-generator/" data-i18n="404.a_text.wedding_memes.22951185">Wedding Memes</a></li>
                                </ul>
                            </li>
                            <li class="nav-dropdown-group" role="none">
                                <div class="nav-dropdown-heading" role="presentation" data-i18n="search.strong_text.absence_compensation.22965696">Absence Compensation</div>
                                <ul role="menu">
                                    <li role="none"><a role="menuitem" href="/services/absence-compensation/family-tribute/" data-i18n="404.a_text.family_tribute.39408322">Family Tribute</a></li>
                                    <li role="none"><a role="menuitem" href="/services/absence-compensation/family-message/" data-i18n="404.a_text.family_message.27013166">Family Message</a></li>
                                </ul>
                            </li>
                            <li class="nav-dropdown-all" role="none">
                                <a role="menuitem" href="/services/" class="nav-dropdown-all-link" data-i18n="nav.a_text.view_all_services.91827365">View all services &rarr;</a>
                            </li>
                        </ul>'''

# Files to skip (don't change anything in /admin/, /private/, /tools/, /tmp/, /qa/, etc.)
SKIP_PATH_PARTS = (
    '/admin/', '/private/', '/tools/', '/tmp/', '/qa/', '/internal-tools/',
    '/.wrangler/', '/.github/', '/scripts/archive/', '/100 blog/', '/_lib/',
)

# Also skip non-HTML files (the script targets index.html only)
def iter_targets() -> list[Path]:
    targets: list[Path] = []
    for p in ROOT.rglob('index.html'):
        rel = p.relative_to(ROOT).as_posix()
        if any(part in rel for part in SKIP_PATH_PARTS):
            continue
        targets.append(p)
    return targets


def already_grouped(content: str) -> bool:
    return 'nav-dropdown-grouped' in content


def transform_file(path: Path) -> str:
    """Return 'updated', 'skipped_already', or 'skipped_no_match'."""
    content = path.read_text(encoding='utf-8')
    if already_grouped(content):
        return 'skipped_already'
    if not OLD_NAV_RE.search(content):
        return 'skipped_no_match'
    new_content = OLD_NAV_RE.sub(NEW_NAV, content)
    if new_content == content:
        return 'skipped_no_match'
    path.write_text(new_content, encoding='utf-8')
    return 'updated'


def main() -> int:
    targets = iter_targets()
    updated = 0
    skipped_already = 0
    skipped_no_match = 0
    for p in targets:
        result = transform_file(p)
        if result == 'updated':
            updated += 1
        elif result == 'skipped_already':
            skipped_already += 1
        else:
            skipped_no_match += 1
    print(f"Scanned: {len(targets)} index.html files")
    print(f"Updated: {updated}")
    print(f"Already grouped: {skipped_already}")
    print(f"No flat nav to replace: {skipped_no_match}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
