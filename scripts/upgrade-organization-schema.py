#!/usr/bin/env python3
"""
Upgrade every Organization JSON-LD block across the site to fill in the
E-E-A-T + multilingual fields Google cares about:

  @id, foundingDate, email, description, alternateName,
  founder (Person), knowsLanguage (10 langs), sameAs (social),
  logo (string URL → ImageObject)

Also covers LocalBusiness blocks that share the @id `#organization`
(they refer to the same entity and should stay consistent).

Idempotent: each field is only added if missing or in the wrong shape.
Existing values are preserved (the script never overwrites user-edited
data).

Skips internal/recon directories: tmp/ private/ scripts/ tests/ qa/.

Run:
    python scripts/upgrade-organization-schema.py         # dry-run
    python scripts/upgrade-organization-schema.py --apply # write
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://weddingai.video"

SCRIPT_RE = re.compile(
    r'(<script type="application/ld\+json"[^>]*>)(.*?)(</script>)',
    re.DOTALL,
)
HAS_ORG = re.compile(r'"@type"\s*:\s*"Organization"')
HAS_LOCALBUSINESS = re.compile(r'"@type"\s*:\s*"LocalBusiness"')

# 10 languages we support (mirrors ContactPoint.availableLanguage in
# about/index.html and the 9 i18n mirrors + en).
KNOWS_LANGUAGE = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th"]

# Social profiles — TODO: replace with real profiles once they exist.
# Empty by design: schema.org accepts sameAs=[]; this signals to crawlers
# that the org is open to being associated with a public profile.
SAME_AS = [
    # "https://www.linkedin.com/company/weddingai-video",
    # "https://twitter.com/weddingai_video",
    # "https://www.youtube.com/@weddingai-video",
    # "https://www.instagram.com/weddingai.video",
]

FOUNDER = {
    "@type": "Person",
    "name": "Alex Chen",
    "jobTitle": "Founder & Creative Director",
    "worksFor": {"@id": f"{SITE}/#organization"},
}

# Logo dimensions — measured from images/logo-full.jpeg on 2026-08-10.
# Google recommends explicit width/height in logo ImageObject so the
# knowledge-panel renderer doesn't have to refetch to size it.
LOGO_WIDTH = "712"
LOGO_HEIGHT = "251"

# Default fields that should be present on every Organization block.
DEFAULTS = {
    "@id":          f"{SITE}/#organization",
    "name":         "WeddingAI.video",
    "alternateName": "WeddingAI",
    "url":          SITE,
    "description":  "AI-powered wedding video services for couples worldwide.",
    "email":        "order@weddingai.video",
    "foundingDate": "2024",
}


def is_node_with_org(node) -> bool:
    if not isinstance(node, dict):
        return False
    t = node.get("@type")
    if t == "Organization":
        return True
    if isinstance(t, list) and "Organization" in t:
        return True
    return False


def is_localbusiness_with_org_id(node) -> bool:
    """LocalBusiness blocks that share the #organization @id — same entity
    as the Organization node, so the logo should stay consistent. We only
    upgrade `logo` for these (other fields are LocalBusiness-specific and
    not the responsibility of this script)."""
    if not isinstance(node, dict):
        return False
    t = node.get("@type")
    if t != "LocalBusiness" and not (isinstance(t, list) and "LocalBusiness" in t):
        return False
    return node.get("@id") == f"{SITE}/#organization"


def upgrade_logo(org: dict) -> bool:
    """Upgrade `logo` from a string URL to an ImageObject object, in place.

    Idempotent: if `logo` is already an ImageObject (dict) with @type,
    leave it alone. If it's a string URL, wrap it.

    Returns True if a change was made.
    """
    logo = org.get("logo")
    # Already an object — respect user edits.
    if isinstance(logo, dict):
        if logo.get("@type") == "ImageObject":
            return False
        # Some legacy entries might be a bare dict without @type; if it has
        # a `url`, fill in @type. Otherwise leave alone.
        if "url" in logo and "@type" not in logo:
            logo["@type"] = "ImageObject"
            return True
        return False
    # String URL — wrap it.
    if isinstance(logo, str) and logo.startswith("http"):
        org["logo"] = {
            "@type": "ImageObject",
            "url": logo,
            "width": LOGO_WIDTH,
            "height": LOGO_HEIGHT,
        }
        return True
    # Anything else (missing, null, weird shape) — leave alone.
    return False


def upgrade_org(org: dict) -> int:
    """Mutate an Organization dict in place. Returns number of new fields added.
    Logo upgrade is handled separately by the caller so we can report it
    distinctly from "new field" additions."""
    added = 0
    for k, v in DEFAULTS.items():
        if k not in org:
            org[k] = v
            added += 1

    # founder — only add if missing AND a Person value (so we never overwrite
    # a real founder the user already set).
    if "founder" not in org:
        org["founder"] = dict(FOUNDER)
        added += 1

    # knowsLanguage — list of language codes we currently support
    if "knowsLanguage" not in org:
        org["knowsLanguage"] = list(KNOWS_LANGUAGE)
        added += 1

    # sameAs — only add if absent and we have social URLs. Empty list is
    # omitted to avoid sending "no social profiles" as a signal.
    if "sameAs" not in org and SAME_AS:
        org["sameAs"] = list(SAME_AS)
        added += 1

    return added


def process_file(path: Path, dry_run: bool) -> tuple[int, int]:
    """Returns (num_blocks_touched, num_fields_added)."""
    text = path.read_text(encoding="utf-8")
    blocks_touched = fields_added = 0

    def replace(match: re.Match) -> str:
        nonlocal blocks_touched, fields_added
        open_tag, body, close_tag = match.group(1), match.group(2), match.group(3)
        # Skip blocks that have neither Organization nor LocalBusiness
        # @type at the top level (nested appearances are picked up by the
        # node loop below).
        if not (HAS_ORG.search(body) or HAS_LOCALBUSINESS.search(body)):
            return match.group(0)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return match.group(0)

        nodes = data.get("@graph", [data]) if isinstance(data, dict) else data
        changed_this_block = False
        for node in nodes:
            if is_node_with_org(node):
                n = upgrade_org(node)
                if n:
                    fields_added += n
                    changed_this_block = True
                if upgrade_logo(node):
                    changed_this_block = True
            elif is_localbusiness_with_org_id(node):
                # Only upgrade logo; other LocalBusiness fields are out of
                # scope for this script.
                if upgrade_logo(node):
                    changed_this_block = True

        if not changed_this_block:
            return match.group(0)

        blocks_touched += 1
        new_body = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        return f"{open_tag}{new_body}{close_tag}"

    new_text = SCRIPT_RE.sub(replace, text)
    if dry_run or new_text == text:
        return blocks_touched, fields_added
    path.write_text(new_text, encoding="utf-8")
    return blocks_touched, fields_added


def main():
    dry_run = "--apply" not in sys.argv
    if dry_run:
        print("DRY-RUN mode. Pass --apply to write changes.\n")

    SKIP_DIRS = ("tmp", "private", "scripts", "tests", "qa", "internal-tools", "tools")
    candidates = []
    for p in ROOT.rglob("*.html"):
        if not p.is_file():
            continue
        if any(seg in p.relative_to(ROOT).parts for seg in SKIP_DIRS):
            continue
        if HAS_ORG.search(p.read_text(encoding="utf-8", errors="ignore")):
            candidates.append(p)
    candidates.sort()

    total_files = total_blocks = total_fields = 0
    for p in candidates:
        blocks, n = process_file(p, dry_run)
        if blocks == 0:
            continue
        rel = p.relative_to(ROOT)
        verb = "DRY  " if dry_run else "WROTE"
        print(f"  {verb}: {rel}  ({blocks} blocks, {n} new fields)")
        total_files += 1
        total_blocks += blocks
        total_fields += n

    print(f"\nDone. {total_files} files, {total_blocks} Organization blocks, "
          f"{total_fields} fields {'would be ' if dry_run else ''}added.")


if __name__ == "__main__":
    main()
