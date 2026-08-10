#!/usr/bin/env python3
"""
Upgrade every Organization JSON-LD block across the site to fill in the
E-E-A-T + multilingual fields Google cares about:

  @id, foundingDate, email, description, alternateName,
  founder (Person), knowsLanguage (10 langs), sameAs (social)

Idempotent: each field is only added if missing. Existing values are
preserved (the script never overwrites user-edited data).

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


def upgrade_org(org: dict) -> int:
    """Mutate an Organization dict in place. Returns number of new fields added."""
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
        if not HAS_ORG.search(body):
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
