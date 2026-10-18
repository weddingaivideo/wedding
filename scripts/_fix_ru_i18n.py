"""Add missing nav keys to ru.json."""
import json
import shutil
import tempfile
from pathlib import Path

p = Path("C:/Users/qiaoshan/.openclaw/workspace/weddingai/i18n/ru.json")
data = json.loads(p.read_text(encoding="utf-8"))
before = len(data)
ADD = {
    "404.a_text.free_tools.91827366": "Бесплатные инструменты",
    "404.a_text.privacy_policy.78442268": "Политика конфиденциальности",
}
for k, v in ADD.items():
    if k not in data:
        data[k] = v
        print(f"  + {k}: {v}")
    else:
        print(f"  = {k} already present, skipped")
after = len(data)
print(f"Total keys: {before} -> {after} (+{after - before})")

# Atomic write with size verify
tmp = p.with_suffix(".json.tmp")
tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="")
v = json.loads(tmp.read_text(encoding="utf-8"))
if len(v) != after:
    tmp.unlink()
    raise RuntimeError("size mismatch aborting")
shutil.move(str(tmp), str(p))
print(f"[OK] Wrote {p} ({p.stat().st_size:,} bytes)")
