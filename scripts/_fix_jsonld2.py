"""Fix nested-string bug in JSON-LD scripts.

Bug pattern in raw HTML bytes:
  "name": ""name": "Wedding Photo Book Planner"",
  "description": ""description": "Free online ..."",

Fix:
  "name": "Wedding Photo Book Planner",
  "description": "Free online ...",

Detection: find '"key": ""key": "value"",' patterns and unwrap.
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

LD_RE = re.compile(r'(<script type="application/ld\+json">)(.+?)(</script>)', re.DOTALL)
# Match: "key": ""key": "value"",  where value is non-quote chars
NESTED_RE = re.compile(r'"([A-Za-z_][A-Za-z0-9_]*)"\s*:\s*""\1"\s*:\s*"([^"]*)""')


def fix_ld(raw: str) -> tuple[str, int]:
    new, n = NESTED_RE.subn(r'"\1": "\2"', raw)
    return new, n


def main():
    fixed_files = 0
    total_fixes = 0
    parse_fail_after = []
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
            if '<script type="application/ld+json">' not in text:
                continue
            any_change = False
            new_text = text
            total_n = 0
            for m in LD_RE.finditer(text):
                raw = m.group(2)
                # Detect bug
                try:
                    json.loads(raw)
                    continue  # already valid
                except json.JSONDecodeError:
                    pass
                # Fix
                new_raw, n = fix_ld(raw)
                if n == 0:
                    continue
                # Verify
                try:
                    json.loads(new_raw)
                except json.JSONDecodeError as e:
                    parse_fail_after.append((p.relative_to(REPO), str(e)))
                    continue
                # Substitute
                new_text = new_text.replace(raw, new_raw, 1)
                any_change = True
                total_n += n
            if any_change:
                tmp = p.with_suffix(p.suffix + ".tmp")
                tmp.write_text(new_text, encoding="utf-8", newline="")
                v = tmp.read_text(encoding="utf-8")
                if v != new_text:
                    tmp.unlink()
                    raise RuntimeError(f"tmp write mismatch for {p}")
                shutil.move(str(tmp), str(p))
                fixed_files += 1
                total_fixes += total_n
                print(f"FIXED {p.relative_to(REPO)} ({total_n} keys cleaned)")
    print(f"\nSummary: {total_fixes} JSON-LD field fixes in {fixed_files} files")
    if parse_fail_after:
        print(f"\nFiles still broken after fix ({len(parse_fail_after)}):")
        for f, e in parse_fail_after[:20]:
            print(f"  {f}: {e}")


if __name__ == "__main__":
    main()
