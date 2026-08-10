"""
Round 4: final cleanup pass for /services/absence-compensation/celebrity-message/.

What's left after r1+r2+r3:
  1. HTML elements whose `data-i18n` attribute references a key whose NAME
     contains "celebrity" (English-language keys). r1's block-shape regex
     didn't match <p data-i18n="blog.X.p_text.celebrity_slug.[hex]"> ... </p>
     because the slug in the key name doesn't contain a hyphen, and the
     block was a single inline <p>, not a multi-line block.
  2. Non-English HTML elements whose data-i18n key was already deleted by
     r1/r2 (e.g. `blog.weddingai-video-guide.p_text.mensaje_de_celebridad...`)
     but whose element body still contains the English fallback text
     "Celebrity Message" / "Celebrity-Style" / "celebrity-style" / etc.
     We catch these by the body text rather than the key name (key names
     use locale-specific slug like "celebridad", "promi", "clbrit").
  3. The Home breadcrumb key `services.absence-compensation.celebrity-message.
     a_text.home.90820803` is INTENTIONALLY preserved by r1. We skip it.
  4. Homepage AI-safety FAQ <p> ends with "and our Celebrity Style service
     uses AI archetypes inspired by style, not impersonation." — same
     wording lives in llms-full.txt. We trim the trailing clause.
  5. services/index.html "2. What's the final use?" decision-tree paragraph
     ends with "Surprise at the rehearsal dinner → Celebrity Message or
     Pet Wedding." — change to "Pet Wedding.".
  6. README.md service table row "Absence Compensation | Family Tribute,
     Family Message, Celebrity Message" — drop the third cell.
  7. Root-level old scripts generate-llms-full.py / inject-srcset.py /
     generate-responsive.py have hardcoded "celebrity-message" tuples and
     "celebrity-message-screen" image-asset names. Clean these so the next
     re-run of these tools doesn't re-introduce stale references.

Safe to re-run (idempotent).
"""

import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\qiaoshan\.openclaw\workspace\weddingai")

# ---------------------------------------------------------------------------
# 1) HTML element deletion. Two complementary rules:
#
#   a) data-i18n KEY name contains "celebrity" (catches English-blog keys like
#      `blog.X.p_text.celebrity_message_with_subtitles.3c1b5c10`).
#   b) Element BODY contains the English term "Celebrity Message" (with
#      capital C, exact phrase), or "Celebrity-Style", or "celebrity-style".
#      Catches non-English blog elements whose i18n key was deleted by r2
#      (e.g. `mensaje_de_celebridad`) but whose body still has the English
#      fallback text.
#
#  PRESERVE_KEYS: a few keys that LEGITIMATELY mention "celebrity" in their
#  name but the body is unrelated (e.g. the breadcrumb Home key).
# ---------------------------------------------------------------------------

PRESERVE_KEYS = {
    "services.absence-compensation.celebrity-message.a_text.home.90820803",
}

# Body-text patterns that uniquely identify a celebrity-MESSAGE element (as
# opposed to a generic "celebrate" or "celebratorio" or "celebridades" list).
# Using case-sensitive "Celebrity Message" / "Celebrity-Style" because these
# are exact English product names. Lowercase "celebrity message" / "celebrity-
# style" are matched too.
BODY_PATTERNS = [
    re.compile(r"\bCelebrity Message\b"),
    re.compile(r"\bCelebrity-Style\b"),
    re.compile(r"\bcelebrity-style\b"),
    re.compile(r"\bcelebrity message\b"),
]


def body_matches(text: str) -> bool:
    return any(rx.search(text) for rx in BODY_PATTERNS)


# Match one HTML element whose opening tag has a `data-i18n="..."` attribute.
# We need the full element including any inner HTML, so re.DOTALL.
HTML_ELEMENT_RE = re.compile(
    r'^[ \t]*<(?P<tag>p|h2|h3|h4|li|div|span)(?P<attrs>(?:\s+[^>]*?)?)>'
    r'(?P<body>.*?)</(?P=tag)>[ \t]*\r?\n',
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)

# Reusable data-i18n attribute extractor
DATA_I18N_RE = re.compile(r'data-i18n="(?P<key>[^"]+)"')


def strip_html_elements(root: Path) -> tuple[int, list[str]]:
    files = list(root.rglob("*.html"))
    files = [p for p in files if "_trash_celebrity" not in p.parts
             and "private" not in p.parts
             and "archive" not in p.parts
             and "tmp" not in p.parts
             and "qa" not in p.parts]
    changed_files: list[str] = []
    total = 0
    for p in files:
        text = p.read_text(encoding="utf-8")
        original = text

        def sub(m: re.Match) -> str:
            attrs = m.group("attrs") or ""
            body = m.group("body")
            # Check data-i18n key
            mi = DATA_I18N_RE.search(attrs)
            key = mi.group("key") if mi else ""
            # Preserve breadcrumb Home
            if key in PRESERVE_KEYS:
                return m.group(0)
            # Drop if key contains "celebrity" or body matches the strict
            # celebrity-Message patterns
            if "celebrity" in key.lower() or body_matches(body):
                return ""
            return m.group(0)

        new = HTML_ELEMENT_RE.sub(sub, text)
        if new != original:
            p.write_text(new, encoding="utf-8")
            # Count removed
            removed = 0
            for m in HTML_ELEMENT_RE.finditer(original):
                attrs = m.group("attrs") or ""
                body = m.group("body")
                mi = DATA_I18N_RE.search(attrs)
                key = mi.group("key") if mi else ""
                if key in PRESERVE_KEYS:
                    continue
                if "celebrity" in key.lower() or body_matches(body):
                    removed += 1
            total += removed
            changed_files.append(str(p.relative_to(root)))
    return total, changed_files


# ---------------------------------------------------------------------------
# 2) Homepage AI-safety FAQ: trim the trailing "and our Celebrity Style..." clause.
# ---------------------------------------------------------------------------

AI_SAFETY_CLAUSE = (
    " We do not generate deepfakes of real people, and our Celebrity Style "
    "service uses AI archetypes inspired by style, not impersonation."
)
AI_SAFETY_REPLACEMENT = (
    " We do not generate deepfakes of real people."
)


def fix_index_ai_safety(root: Path) -> int:
    p = root / "index.html"
    text = p.read_text(encoding="utf-8")
    new = text.replace(AI_SAFETY_CLAUSE, AI_SAFETY_REPLACEMENT, 1)
    if new != text:
        p.write_text(new, encoding="utf-8")
        return 1
    return 0


# ---------------------------------------------------------------------------
# 3) llms-full.txt: same AI-safety clause.
# ---------------------------------------------------------------------------


def fix_llms_full_ai_safety(root: Path) -> int:
    p = root / "llms-full.txt"
    text = p.read_text(encoding="utf-8")
    new = text.replace(AI_SAFETY_CLAUSE, AI_SAFETY_REPLACEMENT, 1)
    if new != text:
        p.write_text(new, encoding="utf-8")
        return 1
    return 0


# ---------------------------------------------------------------------------
# 4) services/index.html decision-tree paragraph: "Celebrity Message or Pet
#    Wedding" -> "Pet Wedding".
# ---------------------------------------------------------------------------

DECISION_TREE_RE = re.compile(
    r"(Surprise at the rehearsal dinner \u2192 )Celebrity Message or Pet Wedding(\.)",
)


def fix_services_decision_tree(root: Path) -> int:
    p = root / "services" / "index.html"
    text = p.read_text(encoding="utf-8")
    new = DECISION_TREE_RE.sub(r"\1Pet Wedding\2", text)
    if new != text:
        p.write_text(new, encoding="utf-8")
        return 1
    return 0


# ---------------------------------------------------------------------------
# 5) README.md service table row: drop ", Celebrity Message" cell.
# ---------------------------------------------------------------------------

README_ROW_OLD = "| Absence Compensation | Family Tribute, Family Message, Celebrity Message |"
README_ROW_NEW = "| Absence Compensation | Family Tribute, Family Message |"


def fix_readme(root: Path) -> int:
    p = root / "README.md"
    text = p.read_text(encoding="utf-8")
    new = text.replace(README_ROW_OLD, README_ROW_NEW, 1)
    if new != text:
        p.write_text(new, encoding="utf-8")
        return 1
    return 0


# ---------------------------------------------------------------------------
# 6) Root-level old scripts: hardcoded celebrity-message tuples and asset names.
# ---------------------------------------------------------------------------

# 6a) generate-llms-full.py — 3 lines to drop
GEN_LLMS_LINES = [
    re.compile(
        r'^[ \t]*\("celebrity-message", "/services/absence-compensation/celebrity-message\.html", "Celebrity Messages"\),\r?\n',
        re.MULTILINE,
    ),
    re.compile(
        r'^[ \t]*\("/services/absence-compensation/celebrity-message\.html",\s*"Celebrity Wedding Messages"\),\r?\n',
        re.MULTILINE,
    ),
    re.compile(
        r'^[ \t]*"/services/absence-compensation/celebrity-message\.html":\s*ROOT / "services" / "absence-compensation" / "celebrity-message\.html",\r?\n',
        re.MULTILINE,
    ),
]


def fix_generate_llms_full(root: Path) -> int:
    p = root / "generate-llms-full.py"
    if not p.exists():
        return 0
    text = p.read_text(encoding="utf-8")
    new = text
    for rx in GEN_LLMS_LINES:
        new = rx.sub("", new)
    if new != text:
        p.write_text(new, encoding="utf-8")
        return 1
    return 0


# 6b) inject-srcset.py / generate-responsive.py — "celebrity-message-screen" asset name
ASSET_NAME_RE = re.compile(
    r'^[ \t]*"celebrity-message-screen",\s*"meme-generator-gif-collage",\s*\r?\n',
    re.MULTILINE,
)


def fix_image_asset_names(root: Path) -> tuple[int, list[str]]:
    changed: list[str] = []
    total = 0
    for fname in ("inject-srcset.py", "generate-responsive.py"):
        p = root / fname
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        new = ASSET_NAME_RE.sub("", text)
        if new != text:
            p.write_text(new, encoding="utf-8")
            total += 1
            changed.append(str(p.relative_to(root)))
    return total, changed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    print("=== HTML elements (data-i18n key or body matches Celebrity Message) ===")
    n, files = strip_html_elements(ROOT)
    print(f"  -> {n} elements removed across {len(files)} files")
    for f in files[:10]:
        print(f"     {f}")
    if len(files) > 10:
        print(f"     ... and {len(files) - 10} more")
    print()

    print("=== Homepage AI-safety FAQ (index.html) ===")
    if fix_index_ai_safety(ROOT):
        print("  [1] index.html")
    else:
        print("  (no change)")
    print()

    print("=== llms-full.txt AI-safety clause ===")
    if fix_llms_full_ai_safety(ROOT):
        print("  [1] llms-full.txt")
    else:
        print("  (no change)")
    print()

    print("=== services/index.html decision-tree paragraph ===")
    if fix_services_decision_tree(ROOT):
        print("  [1] services/index.html")
    else:
        print("  (no change)")
    print()

    print("=== README.md service table ===")
    if fix_readme(ROOT):
        print("  [1] README.md")
    else:
        print("  (no change)")
    print()

    print("=== generate-llms-full.py hardcoded celebrity-message tuples ===")
    if fix_generate_llms_full(ROOT):
        print("  [1] generate-llms-full.py")
    else:
        print("  (no change)")
    print()

    print("=== Root-level image-asset name lists ===")
    n, files = fix_image_asset_names(ROOT)
    if n:
        print(f"  [{n}] {', '.join(files)}")
    else:
        print("  (no change)")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
