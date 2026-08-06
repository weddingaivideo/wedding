"""Detect malformed <picture> tags by walking the HTML and tracking open/close."""
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(".")


class PictureChecker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.picture_depth = 0
        self.problems = []  # list of (reason, position)

    def handle_starttag(self, tag, attrs):
        if tag == "picture":
            self.picture_depth += 1
            if self.picture_depth > 1:
                self.problems.append(("nested <picture>", self.getpos()))

    def handle_endtag(self, tag):
        if tag == "picture":
            self.picture_depth -= 1
            if self.picture_depth < 0:
                self.problems.append(("stray </picture>", self.getpos()))

    def handle_startendtag(self, tag, attrs):
        # self-closing tags don't affect depth
        pass


bad_total = 0
for f in sorted(ROOT.rglob("*.html")):
    if "google-site-verification" in f.name:
        continue
    try:
        text = f.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    checker = PictureChecker()
    try:
        checker.feed(text)
        checker.close()
    except Exception as e:
        print(f"[error] {f.name}: {e}")
        continue
    if checker.problems:
        bad_total += len(checker.problems)
        for reason, (line, col) in checker.problems:
            print(f"  {f.name}:{line}:{col}: {reason}")
print(f"\nTotal bad-picture issues: {bad_total}")
