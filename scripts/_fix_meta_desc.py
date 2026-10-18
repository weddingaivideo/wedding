"""
Trim over-long <meta name="description" content="..."> entries in all HTML files.

Audit said 174 entries >200 chars. Strategy: trim to <=160 chars at word boundary.
For EN root pages the meta description is often in `<meta name="description" content="...">`
directly. For localized pages the content is in i18n dict, applied via data-i18n-attr
in the HTML head, so the literal is in i18n/<lang>.json — we touch HTML directly only.

This script:
1. Scans all .html files (excluding qa/, __pycache__, .archive etc.)
2. Finds <meta name="description" ...> tags
3. If content > 160 chars, trim to <=160 at last word boundary
4. Atomic write

Note: only trims the FALLBACK content="..." attribute. Localized values live in i18n/*.json
and are injected by i18n.js at runtime — those are a separate concern (translation
quality / conciseness).
"""
import os
import re
from pathlib import Path

REPO = Path("C:/Users/qiaoshan/.openclaw/workspace/weddingai")
SKIP_DIRS = ('.git', '.en-backup', '.tmp', '.wrangler', 'node_modules', '__pycache__',
             '.cowork-temp', '.well-known', '.github', 'tests', 'internal-tools',
             'qa', 'private/.archive', 'private/.reverse-progress', 'private/.translate-progress')

META_DESC_RE = re.compile(
    r'(<meta\s+name="description"\s+[^>]*content=")([^"]+)(")',
    re.IGNORECASE
)
MAX_LEN = 160
MIN_LEN = 70  # don't over-trim

def trim_to_word_boundary(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    # Find last space
    sp = cut.rfind(" ")
    if sp > max_len - 30:  # keep at least 30 chars of last word
        cut = cut[:sp]
    # Remove trailing punctuation
    return cut.rstrip(" ,;:-")

def process_file(path: Path) -> tuple[int, list[str]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if '<meta name="description"' not in text:
        return 0, []
    changes = []
    new_text = text
    count = 0
    for m in META_DESC_RE.finditer(text):
        content = m.group(2)
        if len(content) > MAX_LEN:
            trimmed = trim_to_word_boundary(content, MAX_LEN)
            if len(trimmed) >= MIN_LEN:
                old = m.group(0)
                new = f'{m.group(1)}{trimmed}{m.group(3)}'
                new_text = new_text.replace(old, new, 1)
                changes.append(f"  - L{m.start()}: {len(content)} -> {len(trimmed)}")
                count += 1
    if count > 0:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(new_text, encoding="utf-8", newline="")
        # Re-verify
        v = tmp.read_text(encoding="utf-8")
        if v != new_text:
            tmp.unlink()
            raise RuntimeError(f"tmp write mismatch for {path}")
        import shutil
        shutil.move(str(tmp), str(path))
    return count, changes


def main():
    print(f"Scanning {REPO} for >{MAX_LEN} char meta descriptions...")
    total_files = 0
    total_trimmed = 0
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not any(s in os.path.join(root, d) for s in SKIP_DIRS)]
        for f in files:
            if not f.endswith(".html"):
                continue
            p = Path(root) / f
            try:
                n, ch = process_file(p)
            except Exception as e:
                print(f"  ERROR on {p.relative_to(REPO)}: {e}")
                continue
            if n > 0:
                total_files += 1
                total_trimmed += n
                rel = p.relative_to(REPO)
                print(f"FIXED {rel} ({n} trimmed)")
                for c in ch[:3]:
                    print(c)
                if len(ch) > 3:
                    print(f"  ... and {len(ch) - 3} more")
    print(f"\nSummary: {total_trimmed} meta descriptions trimmed in {total_files} files")


if __name__ == "__main__":
    main()
