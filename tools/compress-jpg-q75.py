"""Batch-compress all jpg in a directory at Q=75 with optimize + progressive.

Replaces in place. Filenames unchanged (HTML references intact).
Uses ThreadPoolExecutor for parallel compression.

Usage:
  python batch_compress_generic.py [<target_dir>]
  Default target: images/blog/hero (relative to project root)
"""
import os
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image

# UTF-8 stdout (Windows cp1252 safe)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
TARGET_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else (ROOT / "images" / "blog" / "hero")
QUALITY = 75
WORKERS = 6  # 6 parallel compressors

# Lock for thread-safe stdout
print_lock = None
try:
    import threading
    print_lock = threading.Lock()
except Exception:
    pass


def safe_print(*args, **kwargs):
    if print_lock:
        with print_lock:
            print(*args, **kwargs, flush=True)
    else:
        print(*args, **kwargs, flush=True)


def compress_one(jpg: Path) -> tuple[str, int, int, str | None]:
    """Compress a single jpg. Returns (name, orig_size, new_size, error)."""
    try:
        orig_size = jpg.stat().st_size
        img = Image.open(jpg)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        # Save to temp then atomic move
        tmp = jpg.with_suffix(".tmp")
        img.save(tmp, format="JPEG", quality=QUALITY, optimize=True, progressive=True)
        new_size = tmp.stat().st_size
        os.replace(tmp, jpg)
        return (jpg.name, orig_size, new_size, None)
    except Exception as e:
        # Cleanup tmp if exists
        try:
            jpg.with_suffix(".tmp").unlink(missing_ok=True)
        except Exception:
            pass
        return (jpg.name, -1, -1, str(e))


def main() -> int:
    if not TARGET_DIR.is_dir():
        safe_print(f"ERROR: {INLINE_DIR} not found")
        return 1

    jpgs = sorted(sorted(TARGET_DIR.glob("*.jpg")))
    safe_print(f"目标: {TARGET_DIR}\n找到 {len(jpgs)} 张 jpg，开始压缩 (Q={QUALITY}, optimize, progressive, {WORKERS} workers)")
    start = time.time()

    results: list[tuple[str, int, int, str | None]] = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(compress_one, j): j for j in jpgs}
        done = 0
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            done += 1
            if done % 50 == 0 or done == len(jpgs):
                safe_print(f"  进度: {done}/{len(jpgs)}")

    elapsed = time.time() - start
    safe_print(f"\n用时: {elapsed:.1f}s")

    # Summary
    ok = [r for r in results if r[3] is None]
    errs = [r for r in results if r[3] is not None]
    orig_total = sum(r[1] for r in ok)
    new_total = sum(r[2] for r in ok)
    saved = orig_total - new_total
    ratio = saved / orig_total * 100 if orig_total else 0

    safe_print(f"\n=== 结果 ===")
    safe_print(f"  成功: {len(ok)}/{len(results)}")
    safe_print(f"  失败: {len(errs)}")
    safe_print(f"  原大小:   {orig_total/1024/1024:.1f} MB")
    safe_print(f"  新大小:   {new_total/1024/1024:.1f} MB")
    safe_print(f"  节省:     {saved/1024/1024:.1f} MB ({ratio:.1f}%)")

    if errs:
        safe_print(f"\n=== 失败文件 ===")
        for r in errs[:10]:
            safe_print(f"  {r[0]}: {r[3]}")
        if len(errs) > 10:
            safe_print(f"  ... 还有 {len(errs)-10} 个")

    return 0 if not errs else 2


if __name__ == "__main__":
    sys.exit(main())


# Originally generated 2026-08-06 to re-encode hero/ and inline/ blog jpg.
# Recipe: Q=75 + optimize + progressive, in-place replace.
# Result on weddingai.video: -75% to -80% file size, no visible quality loss.
# Usage:  python tools/compress-jpg-q75.py [<target_dir>]
# Default: images/blog/hero
