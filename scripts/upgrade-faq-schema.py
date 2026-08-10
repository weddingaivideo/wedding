#!/usr/bin/env python3
"""
Upgrade every FAQPage JSON-LD block to add, per Question:
  - author: Organization (WeddingAI.video)
  - dateCreated
  - upvoteCount

And per Answer:
  - upvoteCount
  - url: <page>#faq-N

Idempotent. Detects FAQPage scripts via the @type marker and re-parses JSON
in place. Leaves non-FAQ JSON-LD blocks untouched.

Run:
    python scripts/upgrade-faq-schema.py         # dry-run
    python scripts/upgrade-faq-schema.py --apply # write
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://weddingai.video"
ORG = {
    "@type": "Organization",
    "@id": f"{SITE}/#organization",
    "name": "WeddingAI.video",
    "url": SITE,
}
DATE_CREATED = "2026-08-10"  # WeddingAI project's structured-data rollout date

# match <script type="application/ld+json" ...>...FAQPage...</script>
# Some pages append a CSP nonce (e.g. nonce="__CSP_NONCE__") so we allow attrs.
SCRIPT_RE = re.compile(
    r'(<script type="application/ld\+json"[^>]*>)(.*?)(</script>)',
    re.DOTALL,
)
HAS_FAQ = re.compile(r'"@type"\s*:\s*"FAQPage"')


def page_url_for(path: Path) -> str:
    """Compute the canonical URL for an HTML file under ROOT.

    e.g. ROOT/blog/weddingai-video-guide/index.html -> https://weddingai.video/blog/weddingai-video-guide/
         ROOT/zh/services/.../index.html            -> https://weddingai.video/zh/services/.../
    """
    rel = path.relative_to(ROOT).with_suffix("").as_posix()
    if rel.endswith("/index"):
        rel = rel[:-len("index")]
    elif rel == "index":
        rel = ""
    if rel and not rel.endswith("/"):
        rel += "/"
    return f"{SITE}/{rel}" if rel else SITE


def upgrade_faq(faq: dict, page_url: str) -> int:
    """Mutate a FAQPage dict in place. Returns the number of Question entries touched."""
    if faq.get("@type") != "FAQPage":
        return 0
    main = faq.get("mainEntity", [])
    if not isinstance(main, list):
        return 0

    touched = 0
    for idx, q in enumerate(main, start=1):
        if q.get("@type") != "Question":
            continue
        # add Question-level fields (only if not already set)
        if "author" not in q:
            q["author"] = dict(ORG)
        if "dateCreated" not in q:
            q["dateCreated"] = DATE_CREATED
        if "upvoteCount" not in q:
            q["upvoteCount"] = 0

        ans = q.get("acceptedAnswer")
        if isinstance(ans, dict) and ans.get("@type") == "Answer":
            if "upvoteCount" not in ans:
                ans["upvoteCount"] = 0
            if "url" not in ans:
                ans["url"] = f"{page_url}#faq-{idx}"
        touched += 1
    return touched


def process_file(path: Path, dry_run: bool) -> tuple[int, int]:
    """Returns (num_blocks, num_questions_touched)."""
    text = path.read_text(encoding="utf-8")
    blocks = 0
    questions = 0

    def replace(match: re.Match) -> str:
        nonlocal blocks, questions
        open_tag, body, close_tag = match.group(1), match.group(2), match.group(3)
        if not HAS_FAQ.search(body):
            return match.group(0)
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            print(f"  WARN  : {path.name} JSON parse error: {e}")
            return match.group(0)

        page_url = page_url_for(path)
        n = upgrade_faq(data, page_url)
        if n == 0:
            return match.group(0)

        blocks += 1
        questions += n
        new_body = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        return f"{open_tag}{new_body}{close_tag}"

    new_text = SCRIPT_RE.sub(replace, text)
    if dry_run or new_text == text:
        return blocks, questions

    path.write_text(new_text, encoding="utf-8")
    return blocks, questions


def main():
    dry_run = "--apply" not in sys.argv
    if dry_run:
        print("DRY-RUN mode. Pass --apply to write changes.\n")

    # only HTML files that already contain an FAQPage block.
    # Skip internal/recon directories: their content is Disallow: in robots.txt
    # and 301'd to 404 in _redirects, so any schema we add is dead weight.
    SKIP_DIRS = ("tmp", "private", "scripts", "tests", "qa", "internal-tools", "tools")
    candidates = []
    for p in ROOT.rglob("*.html"):
        if not p.is_file():
            continue
        if any(seg in p.relative_to(ROOT).parts for seg in SKIP_DIRS):
            continue
        if HAS_FAQ.search(p.read_text(encoding="utf-8", errors="ignore")):
            candidates.append(p)
    candidates.sort()

    total_files = total_blocks = total_questions = 0
    for p in candidates:
        blocks, n = process_file(p, dry_run)
        if blocks == 0:
            continue
        rel = p.relative_to(ROOT)
        verb = "DRY  " if dry_run else "WROTE"
        print(f"  {verb}: {rel}  ({blocks} FAQ block, {n} questions)")
        total_files += 1
        total_blocks += blocks
        total_questions += n

    print(f"\nDone. {total_files} files, {total_blocks} FAQ blocks, {total_questions} questions "
          f"{'would be ' if dry_run else ''}upgraded.")


if __name__ == "__main__":
    main()
