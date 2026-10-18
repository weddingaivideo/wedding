"""Comprehensive JSON-LD fix.

Two bug patterns:
1. UNESCAPED: "name": ""name": "VALUE""      (raw bytes have "" with literal " characters)
2. ESCAPED:   "name": "\"name\": \"VALUE\""   (raw bytes have \" with backslash-escaped ")

Fix: detect the redundant outer key and unwrap.

Also fixes: "priceالعملة": "USD" -> "priceCurrency": "USD" (translation artifact).
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

# UNESCAPED nested pattern: "key": ""key": "value"",
# In raw HTML text: "name": ""name": "Wedding Photo Book Planner"",
NESTED_UNESC_RE = re.compile(r'"([A-Za-z_][A-Za-z0-9_]*)"\s*:\s*""\1"\s*:\s*"([^"]*)"')

# ESCAPED nested pattern: "key": "\"key\": \"value\""
# In raw HTML text: "name": "\"name\": \"Wedding Budget Calculator\""
NESTED_ESC_RE = re.compile(r'"([A-Za-z_][A-Za-z0-9_]*)"\s*:\s*"\\"\1\\"\s*:\s*\\"([^"\\]*)\\""')

# Translation artifact: "priceالعملة" should be "priceCurrency"
PRICE_FIX_RE = re.compile(r'"(price)([ا-ي]+)"\s*:')  # Arabic chars appended to "price"


def fix_ld(raw: str) -> tuple[str, list[str]]:
    fixes = []
    # 1. Unescaped nested
    new = NESTED_UNESC_RE.sub(r'"\1": "\2"', raw)
    if new != raw:
        n = len(NESTED_UNESC_RE.findall(raw))
        fixes.append(f"unescaped-nested: {n}")
        raw = new
    # 2. Escaped nested
    new = NESTED_ESC_RE.sub(r'"\1": "\2"', raw)
    if new != raw:
        n = len(NESTED_ESC_RE.findall(raw))
        fixes.append(f"escaped-nested: {n}")
        raw = new
    # 3. price+arabic -> priceCurrency
    new = PRICE_FIX_RE.sub(r'"\1Currency":', raw)
    if new != raw:
        n = len(PRICE_FIX_RE.findall(raw))
        fixes.append(f"priceArabic: {n}")
        raw = new
    return raw, fixes


def main():
    fixed_files = 0
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
            file_fixes = []
            for m in LD_RE.finditer(text):
                raw = m.group(2)
                new_raw, fixes = fix_ld(raw)
                if new_raw != raw:
                    # Verify still parses
                    try:
                        json.loads(new_raw)
                    except json.JSONDecodeError as e:
                        parse_fail_after.append((p.relative_to(REPO), str(e)))
                        continue
                    new_text = new_text.replace(raw, new_raw, 1)
                    any_change = True
                    file_fixes.extend(fixes)
            if any_change:
                tmp = p.with_suffix(p.suffix + ".tmp")
                tmp.write_text(new_text, encoding="utf-8", newline="")
                v = tmp.read_text(encoding="utf-8")
                if v != new_text:
                    tmp.unlink()
                    raise RuntimeError(f"tmp write mismatch for {p}")
                shutil.move(str(tmp), str(p))
                fixed_files += 1
                print(f"FIXED {p.relative_to(REPO)} ({', '.join(file_fixes)})")
    print(f"\nSummary: {fixed_files} files fixed")
    if parse_fail_after:
        print(f"\nStill broken ({len(parse_fail_after)}):")
        for f, e in parse_fail_after[:20]:
            print(f"  {f}: {e}")


if __name__ == "__main__":
    main()
