"""Print a range of inline batches in compact form (one line per request)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "scripts" / "blog-image-gen-batches.json").read_text(encoding="utf-8"))
start, end = [int(x) for x in sys.argv[1].split("-")]
for batch_num in range(start, end + 1):
    print(f"# batch {batch_num}")
    for r in data["inline"][batch_num - 1]:
        print(f"{r['output_file_path']}|{r['prompt']}")
    print()
