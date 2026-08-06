"""
Validate <a> balance in blog/index.html using HTMLParser.
Also reports <h3> balance.
"""
from html.parser import HTMLParser
import sys
from pathlib import Path

FILE = Path(r"C:/Users/qiaoshan/.openclaw/workspace/weddingai/blog/index.html")
content = FILE.read_text(encoding="utf-8")

class TagBalanceChecker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []  # list of (tag, line_no)
        self.errors = []
        self.line = 1

    def handle_starttag(self, tag, attrs):
        if tag in ('a', 'h3', 'div', 'section', 'p', 'h2', 'h1', 'ul', 'li', 'span', 'article', 'picture', 'source', 'img', 'footer', 'header', 'nav'):
            self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if not self.stack:
            self.errors.append(f"line {self.getpos()[0]}: stray </{tag}>")
            return
        top_tag, top_pos = self.stack[-1]
        if top_tag == tag:
            self.stack.pop()
        else:
            # Pop until we find matching tag
            # Just report
            self.errors.append(f"line {self.getpos()[0]}: </{tag}> closes <{top_tag}> from line {top_pos[0]}")
            # Don't pop to keep checking

p = TagBalanceChecker()
p.feed(content)

print(f"Unclosed tags ({len(p.stack)}):")
for tag, pos in p.stack[:20]:
    print(f"  line {pos[0]}: <{tag}>")

print(f"\nMismatched closes ({len(p.errors)}):")
for e in p.errors[:20]:
    print(f"  {e}")
