"""Audit all HTML files for the 7 issue categories."""
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ISSUES = Counter()

def log(issue, detail=""):
    ISSUES[issue] += 1
    if detail:
        print(f"  - {issue}: {detail[:120]}")


def audit_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    # Use path relative to ROOT so reports distinguish index.html vs blog/index.html
    rel = path.relative_to(ROOT).as_posix()

    # 1. img width without height (or vice versa)
    for m in re.finditer(r"<img\b[^>]*>", text):
        attrs = m.group(0)
        has_w = re.search(r"\bwidth=", attrs)
        has_h = re.search(r"\bheight=", attrs)
        has_src = re.search(r"\bsrc=", attrs)
        if has_w and not has_h:
            log("img width no height", f"{rel}: {attrs[:100]}")
        if has_h and not has_w:
            log("img height no width", f"{rel}: {attrs[:100]}")

    # 2. crossorigin without src
    for m in re.finditer(r"<(?:img|source|link|script|video|audio)\b[^>]*>", text):
        attrs = m.group(0)
        if re.search(r"\bcrossorigin=", attrs) and not re.search(r"\bsrc=", attrs):
            tag = m.group(0).split(" ", 1)[0]
            log(f"{tag} crossorigin no src", f"{rel}: {attrs[:100]}")

    # 3. <picture> nesting issues — count <picture> open/close
    open_pic = len(re.findall(r"<picture[\s>]", text))
    close_pic = len(re.findall(r"</picture\s*>", text))
    if open_pic != close_pic:
        log("picture open/close mismatch",
            f"{rel}: open={open_pic}, close={close_pic}")

    # 4. span with aria-label
    for m in re.finditer(r"<span\b[^>]*aria-label[^>]*>", text):
        attrs = m.group(0)
        if re.search(r"\brole=", attrs):
            continue
        log("span aria-label", f"{rel}: {attrs[:100]}")

    # 5. U+0001 control character
    if "\x01" in text:
        log("U+0001 control char", f"{rel}")

    # 6. heading level skip (any level jump >1)
    headings = [(int(m.group(1)), m.group(2)) for m in re.finditer(r"<h([1-6])[^>]*>(.*?)</h[1-6]>", text, re.DOTALL)]
    # Strip nested tags from heading text
    def clean(s):
        return re.sub(r"<[^>]+>", "", s).strip()
    prev = 0
    for level, htext in headings:
        if prev > 0 and level > prev + 1:
            log(f"heading skip h{prev}->h{level}", f"{rel}: {clean(htext)[:50]}")
        prev = level


def main():
    for f in sorted(ROOT.rglob("*.html")):
        if "google-site-verification" in f.name:
            continue
        try:
            audit_file(f)
        except Exception as e:
            print(f"[error] {f.name}: {e}")

    print("\n=== Issue summary ===")
    for k, v in ISSUES.most_common():
        print(f"  {v:3d}  {k}")


if __name__ == "__main__":
    main()
