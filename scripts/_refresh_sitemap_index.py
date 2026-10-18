"""Refresh sitemap.xml (index) lastmod."""
from pathlib import Path
import re, shutil
p = Path("C:/Users/qiaoshan/.openclaw/workspace/weddingai/sitemap.xml")
text = p.read_text(encoding="utf-8")
new = re.sub(r"<lastmod>\d{4}-\d{2}-\d{2}</lastmod>", "<lastmod>2026-10-17</lastmod>", text)
if new == text:
    print("no change")
else:
    tmp = p.with_suffix(".xml.tmp")
    tmp.write_text(new, encoding="utf-8", newline="")
    if tmp.read_text(encoding="utf-8") != new:
        tmp.unlink()
        raise RuntimeError("tmp mismatch")
    shutil.move(str(tmp), str(p))
    print(f"sitemap.xml lastmod refreshed")
