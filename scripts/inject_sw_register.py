#!/usr/bin/env python3
"""
Inject the Service Worker registration snippet into every public HTML file.

Idempotent: skips files that already have a /sw.js reference.

Adds (right before </head>):
    <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(function(err) {
          console.warn('[SW] registration failed', err);
        });
      });
    }
    </script>
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SNIPPET = """<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(function(err) {
      console.warn('[SW] registration failed', err);
    });
  });
}
</script>"""

EXCLUDE_DIRS = {"admin", "qa", "scripts", "__pycache__", "i18n", "js", "styles"}


def should_skip(p: Path) -> bool:
    parts = set(p.parts)
    if parts & EXCLUDE_DIRS:
        return True
    if p.name in ("google-site-verification.html",):
        return True
    return False


def main():
    files = [p for p in ROOT.rglob("*.html") if not should_skip(p)]
    injected = 0
    skipped = 0
    for f in files:
        text = f.read_text(encoding="utf-8")
        if "/sw.js" in text or "serviceWorker" in text:
            skipped += 1
            continue
        new_text = text.replace("</head>", SNIPPET + "\n</head>", 1)
        if new_text == text:
            print(f"  [WARN] no </head> found in {f.relative_to(ROOT)}")
            continue
        f.write_text(new_text, encoding="utf-8")
        injected += 1
    print(f"Injected: {injected}")
    print(f"Skipped:  {skipped} (already had /sw.js or serviceWorker)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
