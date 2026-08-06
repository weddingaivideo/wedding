"""
Fix two related i18n_inject.py bugs in existing HTML files.

Bug 1 (missing <p> open + stray </p> close):
  Before: <strong>label:</strong> body text body text body.</p>
  After:  <p><strong>label:</strong> body text body text body.</p>

  Caused by: i18n_inject.Injector when it sees <p><strong>...</strong>body</p>,
  it overwrites cur_tag='p' with 'strong' on the inner tag, losing the <p> open.

Bug 2 (extra <a> + stray </a>):
  Before: <a class="logo" ...><picture>...</picture><a>
                                          </a>
  After:  <a class="logo" ...><picture>...</picture></a>

  Caused by: Injector loses the outer <a> when nested <picture> (also TAGS)
  is processed, then the original </a> close is emitted but never matched.

Scope: blog/*.html and other pages that went through i18n_inject.
"""
import re
from pathlib import Path

ROOT = Path(r"C:/Users/qiaoshan/.openclaw/workspace/weddingai")

# ----------------------------------------------------------------------------
# Bug 1: Missing <p> + stray </p>
# Pattern: a TAGS tag (strong, em, code, b, i, a, span) opens, content follows,
# a </p> closes. We want to wrap the whole thing in <p>...</p>.

# We need to detect: TAGS_OPEN + (text|child elements) + </p>  where the
# TAGS_OPEN is NOT preceded by a <p> or <li> on the same line/previous text.
#
# This is tricky to do precisely. Heuristic: find lines that start with a
# bare <strong>/<em>/<code>/<b>/<i>/<span>/<a> (with no <p> immediately
# before it within a short window) and end with </p> with no <p> opening
# earlier on that line.
# ----------------------------------------------------------------------------

# Find lines that:
#   - Contain <strong ...> or similar TAGS element opening
#   - End with </p>
#   - Do NOT have a <p> before that TAGS element
TAG_OPEN_RE = re.compile(
    r'<(strong|em|code|b|i|span|a|small)\s[^>]*data-i18n=[^>]*>'
)

def fix_missing_p(content: str) -> tuple[str, int]:
    n = 0
    lines = content.splitlines(keepends=False)
    out = []
    for line in lines:
        # Find tag opens in this line
        tag_opens = list(TAG_OPEN_RE.finditer(line))
        if not tag_opens:
            out.append(line)
            continue
        first_open = tag_opens[0]
        # Check if there's a <p> earlier in this line (before first tag_open)
        prefix = line[:first_open.start()]
        if '<p' in prefix or '<li' in prefix or '<h' in prefix:
            # Already wrapped
            out.append(line)
            continue
        # Check if line ends with </p> (allowing trailing whitespace)
        stripped = line.rstrip()
        if not stripped.endswith('</p>'):
            out.append(line)
            continue
        # Insert <p> before the first tag open
        new_line = prefix + '<p>' + line[first_open.start():]
        out.append(new_line)
        n += 1
    return '\n'.join(out), n


# ----------------------------------------------------------------------------
# Bug 2: Extra <a> after </picture> in footer logo
# Pattern: <a class="logo" title="..."><picture>...</picture><a>
#          ... </a>
# Fix:     <a class="logo" title="..."><picture>...</picture></a>
# ----------------------------------------------------------------------------

# Match the broken footer brand: a multi-line block starting with
# <a class="logo" ...><picture>...<img.../></picture><a>  and ending with </a>
# Replace the <a> after </picture> with </a>, and remove the trailing </a>
FOOTER_BRAND_RE = re.compile(
    r'(<a\s+href="/"\s+class="logo"[^>]*>'
    r'<picture>.*?</picture>)'        # picture block (non-greedy)
    r'<a>',                            # extra <a>
    re.DOTALL
)

# Also match: after fixing the inner, the trailing orphan </a>
TRAILING_ORPHAN_A_RE = re.compile(
    r'(<a\s+href="/"\s+class="logo"[^>]*>'
    r'<picture>.*?</picture></a>)'    # picture block + close
    r'\s+'                              # whitespace
    r'</a>',                            # orphan close
    re.DOTALL
)


def fix_orphan_a(content: str) -> tuple[str, int]:
    n1 = 0
    n2 = 0
    def repl1(m):
        nonlocal n1
        n1 += 1
        return m.group(1) + '</a>'
    new = FOOTER_BRAND_RE.sub(repl1, content)
    def repl2(m):
        nonlocal n2
        n2 += 1
        return m.group(1)  # drop the orphan </a>
    new = TRAILING_ORPHAN_A_RE.sub(repl2, new)
    return new, n1 + n2


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
total_p = 0
total_a = 0
total_files = 0

for html_file in sorted(ROOT.rglob("*.html")):
    rel = html_file.relative_to(ROOT)
    parts = rel.parts
    if 'qa' in parts or 'scripts' in parts or 'tmp' in parts or 'archive' in parts:
        continue
    content = html_file.read_text(encoding="utf-8")
    new_content, n_p = fix_missing_p(content)
    new_content, n_a = fix_orphan_a(new_content)
    if n_p + n_a > 0:
        html_file.write_text(new_content, encoding="utf-8")
        total_files += 1
        total_p += n_p
        total_a += n_a
        print(f"  {rel}: +{n_p} <p>, -{n_a} orphan </a>")

print(f"\nTotal: {total_p} missing <p> added, {total_a} orphan </a> removed, in {total_files} file(s)")
