"""Fix es/tools/wedding-budget-calculator inner-quote-in-string bug.

Bug: JSON-LD has `"Entretenimiento musical"; 7-10%` inside a value — the inner
double-quotes around "Entretenimiento musical" terminate the JSON string prematurely,
then `; 7-10%` becomes invalid JSON.

Fix: unquote the Spanish category name.
"""
import re
import json
import shutil
from pathlib import Path

p = Path("C:/Users/qiaoshan/.openclaw/workspace/weddingai/es/tools/wedding-budget-calculator/index.html")
text = p.read_text(encoding="utf-8", errors="ignore")
LD_RE = re.compile(r'(<script type="application/ld\+json">)(.+?)(</script>)', re.DOTALL)

new_text = text
file_fixes = 0
for m in LD_RE.finditer(text):
    raw = m.group(2)
    try:
        json.loads(raw)
        continue
    except json.JSONDecodeError:
        pass
    # Fix: replace patterns of "X"; → X;
    new_raw = re.sub(r'"([^"]{3,40})";\s*(\d)', r'\1; \2', raw)
    if new_raw == raw:
        continue
    try:
        json.loads(new_raw)
    except json.JSONDecodeError as e:
        print(f"Still broken after fix: {e}")
        continue
    new_text = new_text.replace(raw, new_raw, 1)
    file_fixes += 1

if file_fixes > 0:
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(new_text, encoding="utf-8", newline="")
    v = tmp.read_text(encoding="utf-8")
    if v != new_text:
        tmp.unlink()
        raise RuntimeError("tmp mismatch")
    shutil.move(str(tmp), str(p))
    print(f"FIXED {p.name} ({file_fixes} JSON-LD blocks)")
else:
    print("No fix applied")
