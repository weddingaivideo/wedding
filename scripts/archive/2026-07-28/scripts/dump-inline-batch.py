"""Print one inline batch in ready-to-paste format."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "scripts" / "blog-image-gen-batches.json").read_text(encoding="utf-8"))
idx = int(sys.argv[1]) - 1
batch = data["inline"][idx]
for r in batch:
    fn = r["output_file_path"]
    p = r["prompt"]
    print(f"  file: {fn}")
    print(f"    prompt: {p}")
    print()
