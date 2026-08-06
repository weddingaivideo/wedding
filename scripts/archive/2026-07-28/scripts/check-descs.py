import os
ROOT = r"C:\Users\qiaoshan\.openclaw\workspace\weddingai"
import re
for p in ["about.html", "index.html"]:
    content = open(os.path.join(ROOT, p), encoding="utf-8").read()
    m = re.search(r'name="description"\s+content="([^"]+)"', content)
    if m:
        print(f"{p}: {len(m.group(1))} chars")
        print(f"  >{m.group(1)}<")
