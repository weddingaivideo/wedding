"""Print a single batch (hero or inline) in a format the assistant can use
to compose image_synthesize invocations."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "scripts" / "blog-image-gen-batches.json").read_text(encoding="utf-8"))

which = sys.argv[1] if len(sys.argv) > 1 else "hero-1"
kind, idx_s = which.split("-")
idx = int(idx_s) - 1
if kind == "hero":
    batch = data["heroes"][idx]
else:
    batch = data["inline"][idx]

print(f"# {kind} batch {idx+1} ({len(batch)} requests)")
for r in batch:
    print(f"  - {r['output_file_path']}")
