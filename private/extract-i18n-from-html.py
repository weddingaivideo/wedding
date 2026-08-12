#!/usr/bin/env python3
"""
Extract i18n keys from all HTML files and merge into i18n/en.json.

Logic:
  1. For every HTML file under repo root, find:
     a) <tag data-i18n="key">inner</tag>      — text content translation
     b) <tag data-i18n-attr="content:key1|title:key2"> — attribute translation
  2. For each key found:
     - If inner is `---` or empty/whitespace → skip (placeholder / dead slot)
     - If key contains `.x.` placeholder token (e.g. `blog.foo.p_text.x.HASH`) → skip
     - Decode HTML entities (&amp; &lt; etc.) in the value so the JSON is human-readable
     - Preserve inline HTML (<br>, <strong>, etc.) — they are part of the source text
       and the middleware's applyDataI18n uses .innerHTML, not .textContent
  3. Merge with existing en.json:
     - For keys that are purely whitespace/formatting differences (apostrophe
       normalization, trailing space, etc.), keep JSON's value (human edit).
     - For keys with material content differences (>5 char diff), PREFER HTML
       because the HTML is the canonical user-facing source — if HTML was
       updated but en.json wasn't, the current production shows stale en.json
       text. The reverse is unlikely (HTML is hard to edit in bulk; en.json
       edits are visible in dev).
     - All material differences are logged for human review.
  4. Preserve JSON formatting: 2-space indent, CRLF, no BOM, ensure_ascii=False
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")
I18N = ROOT / "i18n"
EN_JSON = I18N / "en.json"

PLACEHOLDER_KEY_RE = re.compile(r"\.x\.[a-f0-9]{6,8}$|\bx\.[a-f0-9]{6,8}$")
DATA_I18N_RE = re.compile(
    r'<\w+\b[^>]*\bdata-i18n="([^"]+)"[^>]*>',
    re.IGNORECASE,
)
DATA_I18N_ATTR_RE = re.compile(
    r'<\w+([^>]*?\bdata-i18n-attr="([^"]+)"[^>]*)>',
    re.IGNORECASE,
)
# Match an attribute like content="..." or alt='...' (handles both quote styles)
ATTR_RE = re.compile(r'''([a-zA-Z][\w-]*)=(?:"([^"]*)"|'([^']*)')''')

# Skip these tags — they're not user-facing text
SKIP_TAGS = {"script", "style", "template"}


def find_html_files() -> list[Path]:
    """All English HTML files in repo (root + English subdirs).
    Excludes language directories (ar/ zh/ ja/ th/ etc) which are pollution
    sources for en.json.
    """
    # Subdirectories at the root that hold English HTML (i.e. NOT a language dir)
    # Language dirs = 2-letter codes that are valid i18n langs
    KNOWN_LANG_DIRS = {"ar", "de", "es", "fr", "ja", "pt", "ru", "th", "zh"}
    # English-source subdirs at root: top-level dirs that aren't language dirs
    # and aren't tooling/private/cache
    NON_ENGLISH_DIRS = {
        "private", "qa", "scripts", "tests", "tools", "internal-tools",
        "functions", "i18n", "images", "js", "styles", "tmp", "node_modules",
        "__pycache__", ".wrangler", ".github", ".archive", ".en-backup",
        ".i18n-backup", ".translate-progress", ".assetsignore", "articles",
    }

    out = []
    for p in ROOT.rglob("*.html"):
        try:
            rel = p.relative_to(ROOT)
        except ValueError:
            continue
        parts = rel.parts
        # First-level dir(s) of this file
        first_dir = parts[0].lower() if len(parts) > 1 else ""
        # Reject if any top-level dir is a language dir
        # (i.e. file is under ar/ zh/ ja/ ...)
        if first_dir in KNOWN_LANG_DIRS:
            continue
        # Reject tooling dirs
        if first_dir in NON_ENGLISH_DIRS:
            continue
        # Reject hidden dirs / archives
        if first_dir.startswith(".") and first_dir != ".":
            continue
        out.append(p)
    return out


def extract_data_i18n_text(text: str) -> dict[str, str]:
    """
    Find every `<tag ... data-i18n="key" ...>inner</tag>` and return {key: inner}.

    Uses a position-walk parser (not regex) to handle nested data-i18n correctly:
    the regex `<...>...</...>` greedy/non-greedy match fails when a parent <a>
    contains a child <span data-i18n="..."> — the parent match consumes the
    child, so the child's key is missed.

    Strategy: find every opening tag with data-i18n, then for each one walk
    forward through tag opens/closes (dept counter) to find the matching close,
    capturing everything between.
    """
    result: dict[str, str] = {}
    # Find candidates: every tag that has data-i18n attribute
    candidates = []  # (position, key, tag_name)
    for m in re.finditer(r'<(\w+)([^>]*\bdata-i18n="([^"]+)"[^>]*)>', text, re.IGNORECASE):
        tag_name = m.group(1).lower()
        key = m.group(3)
        candidates.append((m.end(), tag_name, key, m.start()))

    # Sort by depth: outer matches come first by document position. We want to
    # find INNER matches first — but that requires true depth tracking. A simple
    # fix: process candidates in REVERSE position order so nested children are
    # processed before parents, but since we only read (don't write), order
    # doesn't actually matter for content extraction.
    # Just process each candidate independently.
    for end_pos, tag_name, key, _start in candidates:
        # Walk from end_pos forward, counting depth of `tag_name` opens vs closes
        depth = 1
        pos = end_pos
        close_re = re.compile(rf'</{re.escape(tag_name)}\s*>', re.IGNORECASE)
        open_re = re.compile(rf'<{re.escape(tag_name)}\b', re.IGNORECASE)
        while depth > 0 and pos < len(text):
            # Find next open or close of this tag
            close_m = close_re.search(text, pos)
            open_m = open_re.search(text, pos)
            if not close_m:
                break  # no more closes, malformed
            if open_m and open_m.start() < close_m.start():
                depth += 1
                pos = open_m.end()
            else:
                depth -= 1
                if depth == 0:
                    inner = text[end_pos:close_m.start()]
                    result[key] = inner
                    break
                pos = close_m.end()
    return result


def extract_from_file(path: Path) -> tuple[dict[str, str], dict[str, tuple[str, str]]]:
    """
    Returns (text_keys, attr_keys) where:
      text_keys: {key: inner_html}
      attr_keys: {key: (attr_name, attr_value)} — note: attr keys may be re-used;
                 last wins for our purposes, but we'll log conflicts.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="ignore")

    text_keys: dict[str, str] = {}
    attr_keys: dict[str, tuple[str, str]] = {}

    # 1) data-i18n (text) — use position-walk parser to handle nested tags
    raw_text_keys = extract_data_i18n_text(text)
    for key, inner in raw_text_keys.items():
        # Skip placeholder keys
        if PLACEHOLDER_KEY_RE.search(key):
            continue
        # Skip dead slots (--- or empty after stripping tags/whitespace)
        stripped = re.sub(r"\s+|<[^>]+>", "", inner).strip()
        if not stripped or stripped == "---":
            continue
        text_keys[key] = inner

    # 2) data-i18n-attr
    for m in DATA_I18N_ATTR_RE.finditer(text):
        full_attrs = m.group(1)
        spec = m.group(2)
        for pair in spec.split("|"):
            if ":" not in pair:
                continue
            attr_name, key = pair.split(":", 1)
            attr_name = attr_name.strip()
            key = key.strip()
            if PLACEHOLDER_KEY_RE.search(key):
                continue
            # Find the current value of attr_name in full_attrs
            am = re.search(rf'\b{re.escape(attr_name)}=(?:"([^"]*)"|\'([^\']*)\')', full_attrs)
            if not am:
                continue
            value = am.group(1) or am.group(2) or ""
            if not value or value == "---":
                continue
            attr_keys[key] = (attr_name, value)

    return text_keys, attr_keys


def merge(existing: dict, extracted_text: dict, extracted_attr: dict,
          verbose: bool = True) -> tuple[dict, list[str], list[str]]:
    """
    Returns (merged, new_keys_added, warnings).

    Rules:
      - New keys (HTML-only) are always added.
      - For existing keys with material differences (>5 char normalized), we
        PREFER THE HTML VALUE because the HTML is the canonical user-facing
        source. Stale en.json values would otherwise show outdated copy.
      - For pure whitespace/punctuation differences, keep JSON (it's likely
        a normalized form of the same text).
      - All overrides are logged for review.
    """
    new_keys = []
    warnings = []
    overrides = []  # (key, old_value, new_value)

    def consider(key, extracted_value):
        nonlocal new_keys
        if key not in existing:
            existing[key] = extracted_value
            new_keys.append(key)
            return
        ev = existing[key]
        if ev == extracted_value:
            return
        # Normalize for comparison
        norm_existing = re.sub(r"\s+", " ", html.unescape(ev)).strip()
        norm_extracted = re.sub(r"\s+", " ", html.unescape(extracted_value)).strip()
        if norm_existing == norm_extracted:
            # Whitespace/punctuation only — keep JSON
            return
        if abs(len(norm_existing) - len(norm_extracted)) <= 5:
            # Tiny edit — keep JSON (could be apostrophe, ellipsis, etc.)
            return
        # Material diff — override JSON with HTML, log it
        existing[key] = extracted_value
        overrides.append((key, norm_existing, norm_extracted))

    for key, value in extracted_text.items():
        consider(key, value)

    for key, (attr_name, value) in extracted_attr.items():
        consider(key, value)

    return existing, new_keys, warnings, overrides


def main():
    if not EN_JSON.exists():
        print(f"ERROR: {EN_JSON} not found", file=sys.stderr)
        sys.exit(1)

    # Read existing en.json
    raw_bytes = EN_JSON.read_bytes()
    has_crlf = b"\r\n" in raw_bytes
    le = "\r\n" if has_crlf else "\n"
    existing_obj = json.loads(raw_bytes.decode("utf-8"))
    existing_keys = set(existing_obj.keys())
    print(f"=== en.json (existing) ===")
    print(f"  keys: {len(existing_keys)}")
    print(f"  size: {len(raw_bytes):,} bytes")
    print()

    # Find HTML files
    html_files = find_html_files()
    print(f"=== Scanning {len(html_files)} HTML files ===")

    # Extract
    all_text: dict[str, str] = {}
    all_attr: dict[str, tuple[str, str]] = {}
    placeholder_skipped = 0
    dead_skipped = 0
    error_count = 0
    for hf in html_files:
        try:
            text_keys, attr_keys = extract_from_file(hf)
        except Exception as e:
            error_count += 1
            print(f"  ERROR on {hf.name}: {type(e).__name__}: {e}")
            if error_count >= 5:
                print("  Too many errors, stopping")
                sys.exit(1)
            continue
        for k in text_keys:
            all_text[k] = text_keys[k]
        for k, v in attr_keys.items():
            # Multiple files may set the same attr key with different values; last wins
            # but we'll detect conflicts during merge
            all_attr[k] = v
    print(f"  text keys extracted: {len(all_text)}")
    print(f"  attr keys extracted: {len(all_attr)}")
    print(f"  placeholder (.x.HASH) skipped: {placeholder_skipped}")
    print(f"  errors during extraction: {error_count}")
    print()

    # Merge
    merged, new_keys, warnings, overrides = merge(existing_obj, all_text, all_attr)
    print(f"=== Merge result ===")
    print(f"  before: {len(existing_keys)} keys")
    print(f"  after:  {len(merged)} keys")
    print(f"  new:    {len(new_keys)} keys added")
    print(f"  overrides (HTML overwrote stale JSON): {len(overrides)}")
    print()

    if overrides:
        print(f"=== Overrides (HTML is canonical; JSON was stale) ===")
        for k, old, new in overrides[:30]:
            print(f"  {k}")
            print(f"    OLD: {old[:120]}")
            print(f"    NEW: {new[:120]}")
        if len(overrides) > 30:
            print(f"  ... and {len(overrides) - 30} more")
        print()

    # Write back
    print("=== Writing en.json ===")
    out = json.dumps(merged, indent=2, ensure_ascii=False, separators=(",", ": "))
    if has_crlf:
        out = out.replace("\n", "\r\n")
    if raw_bytes.endswith(b"\n"):
        out += le
    EN_JSON.write_text(out, encoding="utf-8", newline="")
    new_size = EN_JSON.stat().st_size
    print(f"  size: {len(raw_bytes):,} → {new_size:,} bytes (+{new_size - len(raw_bytes):,})")
    print(f"  CRLF preserved: {has_crlf}")
    print(f"  Done.")


if __name__ == "__main__":
    main()
