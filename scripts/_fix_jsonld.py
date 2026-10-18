"""Fix nested-escaped JSON-LD strings.

Bug: JSON-LD scripts have `name` field that is double-escaped:
   "name": "\"name\": \"Wedding Budget Calculator\""
This should be: "name": "Wedding Budget Calculator"

Caused by i18n injection template that wraps i18n values in extra quotes.

Detection: extract the JSON-LD content, parse with json.loads, fail if "name"
contains a literal `\"name\"` pattern.
"""
import os
import re
import json
import shutil
from pathlib import Path

REPO = Path("C:/Users/qiaoshan/.openclaw/workspace/weddingai")
SKIP = ('.git', '.en-backup', '.tmp', '.wrangler', 'node_modules', '__pycache__',
        '.cowork-temp', '.well-known', '.github', 'tests', 'internal-tools', 'qa',
        'private/.archive', 'private/.reverse-progress', 'private/.translate-progress')

# JSON-LD block regex
LD_RE = re.compile(r'<script type="application/ld\+json">(.+?)</script>', re.DOTALL)

# Bug pattern: `"name": "\"name\": \"...\""` etc
BUG_NAME_RE = re.compile(r'"name"\s*:\s*"\\"name\\"\s*:\s*\\"([^"\\]+)\\""')
BUG_HEADLINE_RE = re.compile(r'"headline"\s*:\s*"\\"headline\\"\s*:\s*\\"([^"\\]+)\\""')

def is_ld_buggy(text: str) -> bool:
    """Try to parse JSON-LD and detect the nested-string bug."""
    m = LD_RE.search(text)
    if not m:
        return False, None
    raw = m.group(1)
    try:
        json.loads(raw)
        return False, None  # parses fine
    except json.JSONDecodeError:
        return True, raw

def fix_ld_text(raw: str) -> tuple[str, int]:
    """Replace nested-escaped patterns in raw JSON-LD."""
    fixes = 0
    # Match `"name": "NAME"` and similar with embedded JSON
    # The pattern is: "key": "\"key\": \"value\""
    new = re.sub(
        r'"([a-zA-Z_]+)"\s*:\s*"\\"\1\\"\s*:\s*\\"([^"\\]+)\\""',
        r'"\1": "\2"',
        raw
    )
    if new != raw:
        # count occurrences by counting captures
        fixes = len(re.findall(r'\\"\1\\"', raw))
    return new, fixes

def main():
    fixed_files = 0
    total_fixes = 0
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP and not any(s in os.path.join(root, d) for s in SKIP)]
        for f in files:
            if not f.endswith(".html"):
                continue
            p = Path(root) / f
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            buggy, raw = is_ld_buggy(text)
            if not buggy:
                continue
            # Apply fix
            new_raw, fixes = fix_ld_text(raw)
            if new_raw == raw:
                print(f"  NO AUTOMATIC FIX for {p.relative_to(REPO)}")
                continue
            # Re-parse to confirm
            try:
                json.loads(new_raw)
            except json.JSONDecodeError as e:
                print(f"  STILL BROKEN after fix: {p.relative_to(REPO)}: {e}")
                continue
            # Substitute
            new_text = text.replace(raw, new_raw, 1)
            if new_text == text:
                print(f"  NO SUBSTITUTION for {p.relative_to(REPO)}")
                continue
            tmp = p.with_suffix(p.suffix + ".tmp")
            tmp.write_text(new_text, encoding="utf-8", newline="")
            v = tmp.read_text(encoding="utf-8")
            if v != new_text:
                tmp.unlink()
                raise RuntimeError(f"tmp write mismatch for {p}")
            shutil.move(str(tmp), str(p))
            fixed_files += 1
            total_fixes += fixes
            print(f"FIXED {p.relative_to(REPO)} ({fixes} keys cleaned)")
    print(f"\nSummary: {total_fixes} JSON-LD field fixes in {fixed_files} files")


if __name__ == "__main__":
    main()
