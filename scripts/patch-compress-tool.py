#!/usr/bin/env python3
"""
Wire pica (high-quality resampler) into the compress tool's max-dimension
resize.

WHY
---
The compress tool downsizes a photo to the "max longest edge" the user picks
(default 2048 px) with the browser's drawImage(), whose bilinear filter
visibly softens a large downscale: a 6000 px wedding photo becomes 2048 px,
a 3x reduction, and the result is measurably mushy before the JPEG encoder
touches it.

pica (MIT, vendored under /js/vendor/pica/) does a proper multi-step
resample. It is loaded on FIRST USE only - a visitor who never resizes
never downloads it - and it needs 'wasm-unsafe-eval' in the CSP, which is
already there (functions/_middleware.js buildCsp() and _headers).

If the WASM path is unavailable for any reason, common.js's resizeCanvas()
falls back to the old drawImage() path, so the tool keeps working.

The inline JavaScript is changed in the ENGLISH SOURCE only; the localized
copies receive it through scripts/propagate-tool-js.py.

Usage:  python scripts/patch-compress-tool.py [--dry-run]
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
SLUG = "compress-wedding-photos"

JS_OLD = """          var canvas = document.createElement('canvas');
          canvas.width = tw;
          canvas.height = th;
          var ctx = canvas.getContext('2d');
          ctx.imageSmoothingEnabled = true;
          ctx.imageSmoothingQuality = 'high';
          ctx.drawImage(img, 0, 0, tw, th);
          var mime = settings.format;"""

JS_NEW = """          // pica (MIT) does a proper multi-step resample. The browser's
          // drawImage() bilinear filter visibly softens a large downscale -
          // 6000 px down to 2048 px is exactly that case. pica is loaded on
          // first use only, and common.js falls back to drawImage() when the
          // WASM path is unavailable.
          var canvas = await window.weddingAITool.resizeCanvas(img, tw, th);
          var mime = settings.format;"""


def write_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmpwrite")
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    en_path = ROOT / "tools" / SLUG / "index.html"
    text = en_path.read_text(encoding="utf-8")
    if JS_OLD not in text:
        raise SystemExit("[FAIL] the English inline script anchor did not match")
    new = text.replace(JS_OLD, JS_NEW, 1)

    scripts = re.findall(r"(?s)<script\b[^>]*>(.*?)</script>", new)
    biggest = max(scripts, key=len) if scripts else ""
    tmp = Path(os.environ.get("TEMP", ".")) / "compress_inline_check.js"
    tmp.write_text(biggest, encoding="utf-8")
    r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"[FAIL] the inline script does not parse:\n{r.stderr}")

    if not args.dry_run:
        write_atomic(en_path, new)
        print("  en: pica resize wired in")
    else:
        print("  en: would wire pica resize in")

    print("\nNow propagate to the localized copies:")
    print("  python scripts/propagate-tool-js.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
