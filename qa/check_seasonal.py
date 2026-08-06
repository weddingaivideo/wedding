"""Check what date/seasonal markers exist on seasonal blog posts."""
import os
import re
from pathlib import Path

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
for slug in ['christmas-wedding-video', 'spring-wedding-video-trends', 'summer-wedding-video-tips']:
    f = ROOT / 'blog' / slug / 'index.html'
    text = f.read_text(encoding='utf-8')
    print(f"=== {slug} ===")
    # Check title and meta
    m_title = re.search(r'<title[^>]*>([^<]+)</title>', text)
    m_desc = re.search(r'<meta name="description"[^>]*content="([^"]+)"', text)
    print(f"  title: {m_title.group(1)[:100] if m_title else 'NOT FOUND'}")
    print(f"  desc: {m_desc.group(1)[:100] if m_desc else 'NOT FOUND'}")
    # Look for any date-related keywords
    for keyword in ['updated', 'published', 'last modified', '2025', '2026', 'holiday', 'season']:
        count = text.lower().count(keyword)
        if count > 0:
            print(f"  '{keyword}': {count} occurrences")
    print()
