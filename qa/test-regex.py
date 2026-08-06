"""Quick regex smoke test for gen_llms.py's extract_meta regex."""
import re

# Same regex from gen_llms.py extract_meta
TITLE_PAT = re.compile(r"<title(?:\s[^>]*)?>([^<]+)</title>", re.IGNORECASE)

samples = [
    '<title>Plain Title</title>',
    '<title data-i18n="foo">With Attr</title>',
    '<title  data-i18n="bar">With Spaces</title>',
    '<title data-i18n="x">AI-Powered Wedding Video Services | WeddingAI.video</title>',
    '<title  data-i18n="x">About Us | Filmmakers + AI Engineers | WeddingAI.video</title>',
]
for s in samples:
    m = TITLE_PAT.search(s)
    print(f"  {s[:60]}... -> {m.group(1)!r}" if m else f"  {s[:60]}... -> NO MATCH")
