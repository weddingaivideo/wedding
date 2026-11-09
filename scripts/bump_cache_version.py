#!/usr/bin/env python3
"""
Bump the cache-bust version stamp on JS/CSS asset URLs in all HTML files.

Currently tracks:
  - js/i18n.js?v=N
  - js/main.min.js?v=N
  - styles.min.css?v=N

Reads current version from a representative HTML file, increments by 1,
rewrites all matching occurrences in every HTML file (idempotent: if the
new version is already in place, the script is a no-op).

Usage:
    python scripts/bump_cache_version.py           # bump all three assets
    python scripts/bump_cache_version.py --dry-run # show what would change
    python scripts/bump_cache_version.py --asset styles.min.css  # bump one
"""
import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (asset filename, regex pattern capturing the current version) — keep in sync
# with the actual <script>/<link> tags in the HTML.
ASSETS = [
    ("i18n.js", re.compile(r"/js/i18n\.js\?v=(\d+(?:\.\d+)*)")),
    ("main.min.js", re.compile(r"/js/main\.min\.js\?v=(\d+(?:\.\d+)*)")),
    ("styles.min.css", re.compile(r"/styles\.min\.css\?v=(\d+(?:\.\d+)*)")),
    # Added 2026-11-09: the shared tool layer. common.js gained the vendored
    # library loader (ZIP / PDF / HEIC / pica) and tools.css gained the
    # print rules, so both need a stamp bump whenever they change.
    ("common.js", re.compile(r"/js/tools/common\.js\?v=(\d+(?:\.\d+)*)")),
    ("tools.css", re.compile(r"/styles/tools\.css\?v=(\d+(?:\.\d+)*)")),
    # Added 2026-11-11: the MP4 encoder loader. It is referenced from the
    # tool page's HTML with a ?v= stamp, so the normal HTML sweep reaches
    # it - unlike the pixel worker, whose URL is built at runtime.
    ("movie-loader.js", re.compile(r"/js/tools/movie-loader\.js\?v=(\d+(?:\.\d+)*)")),
    # Added 2026-11-11: the AVIF encoder loader (§2.12). It is referenced
    # from the compress tool page's HTML with a ?v= stamp, like the MP4
    # loader. The encoder package itself lives under a versioned directory,
    # so its own cache key changes with the version.
    ("image-codecs.js", re.compile(r"/js/tools/image-codecs\.js\?v=(\d+(?:\.\d+)*)")),
]

# Assets whose stamp does NOT live in the HTML.
#
# The pixel worker (§2.5) is fetched at runtime by common.js, so its `?v=`
# is a constant inside common.js. Bumping the HTML stamps would not reach
# it, and Cloudflare Pages overrides Cache-Control on static assets - a
# stale stamp would serve the OLD worker forever. Same trap, different
# place.
#
# (name, file relative to ROOT, pattern with the version in group 2)
JS_ASSETS = [
    ("pixel-worker.js", "js/tools/common.js",
     re.compile(r"(var PIXEL_WORKER_VERSION = ')(\d+(?:\.\d+)*)(')")),
]

ALL_ASSET_NAMES = [n for n, _ in ASSETS] + [n for n, _, _ in JS_ASSETS]

EXCLUDE_DIRS = {"admin", "qa", "scripts", "__pycache__", "i18n", "js", "styles",
                ".git", ".tmp", "node_modules", "__MACOSX", ".github", "internal-docs",
                "internal-tools", "private"}


def iter_html(root: Path):
    """Yield the project's HTML files, pruning excluded directories.

    pathlib's rglob() walks EVERYTHING below the root - including .git,
    which holds tens of thousands of loose objects. On this machine that
    turned a two-second job into a fifteen-minute one (measured
    2026-11-09: 21 s of CPU in 14 min of wall clock, i.e. blocked on
    directory I/O rather than computing). os.scandir with explicit pruning
    is an order of magnitude faster and cannot wander into .git.
    """
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            entries = list(os.scandir(current))
        except (PermissionError, OSError):
            continue
        for entry in entries:
            try:
                if entry.is_dir(follow_symlinks=False):
                    if entry.name in EXCLUDE_DIRS or entry.name.startswith("."):
                        if entry.name != ".":
                            continue
                    stack.append(Path(entry.path))
                elif entry.name.endswith(".html"):
                    yield Path(entry.path)
            except OSError:
                continue


def find_current_versions() -> dict[str, str]:
    """Read version from index.html (or first HTML that has all three)."""
    candidates = sorted(iter_html(ROOT))
    versions: dict[str, str] = {}
    for p in candidates:
        text = p.read_text(encoding="utf-8", errors="ignore")
        for name, pat in ASSETS:
            if name in versions:
                continue
            m = pat.search(text)
            if m:
                versions[name] = m.group(1)
        if len(versions) == len(ASSETS):
            break
    if len(versions) < len(ASSETS):
        missing = [n for n, _ in ASSETS if n not in versions]
        raise SystemExit(f"[FAIL] Could not find version stamps for: {missing}")
    return versions


def find_js_versions() -> dict[str, str]:
    """Read the version stamps that live inside a JS file instead of the HTML."""
    out: dict[str, str] = {}
    for name, rel, pat in JS_ASSETS:
        path = ROOT / rel
        if not path.exists():
            raise SystemExit(f"[FAIL] Missing {rel} (needed for the {name} stamp)")
        text = path.read_text(encoding="utf-8", errors="ignore")
        m = pat.search(text)
        if not m:
            raise SystemExit(f"[FAIL] Could not find the {name} version stamp in {rel}")
        out[name] = m.group(2)
    return out


def bump(version: str) -> str:
    """Bump a semver-ish version.

    '3.18' -> '3.19', '3.21' -> '3.22', '1.0.0' -> '1.0.1'.

    The tool assets are stamped with a THREE-part version (common.js and
    tools.css were introduced as 1.0.0), while the older site assets use
    two parts (main.min.js 3.21). Both have to work: splitting '1.0.0' on
    the first dot and calling int() on '0.0' raises ValueError.
    """
    parts = version.split(".")
    if len(parts) >= 3:
        parts[-1] = str(int(parts[-1]) + 1)
        return ".".join(parts)
    if len(parts) == 2:
        return f"{parts[0]}.{int(parts[1]) + 1}"
    return str(int(version) + 1)


def write_atomic(path: Path, text: str) -> None:
    """Write via a temp file + os.replace.

    A plain write_text() truncates the target BEFORE the write, so an
    interrupted run leaves a 0-byte HTML file (this happened to i18n/ja.json
    on 2026-10-30). os.replace() is atomic on Windows: the destination is
    either the old content or the new content, never a half-written file.
    """
    tmp = path.with_name(path.name + ".tmpwrite")
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def apply_to_file(path: Path, asset: str, new_version: str, dry: bool) -> int:
    """Replace ?v=OLD with ?v=NEW in the given file. Returns count of replacements."""
    name, pat = next((n, p) for n, p in ASSETS if n == asset)
    text = path.read_text(encoding="utf-8", errors="ignore")
    changes = 0

    def repl(m: re.Match) -> str:
        nonlocal changes
        changes += 1
        return m.group(0).replace(f"v={m.group(1)}", f"v={new_version}")

    new_text = pat.sub(repl, text)
    if changes and not dry:
        write_atomic(path, new_text)
    return changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    ap.add_argument("--asset", choices=ALL_ASSET_NAMES, help="Bump only this asset (default: all)")
    args = ap.parse_args()

    versions = find_current_versions()
    js_versions = find_js_versions()
    print("Current versions:")
    for name, v in versions.items():
        print(f"  {name}: ?v={v}")
    for name, v in js_versions.items():
        print(f"  {name}: ?v={v}  (in {JS_ASSETS[[n for n, _, _ in JS_ASSETS].index(name)][1]})")

    targets = [args.asset] if args.asset else ALL_ASSET_NAMES
    new_versions = {}
    for name in targets:
        cur = versions.get(name) or js_versions.get(name)
        if cur is None:
            raise SystemExit(f"[FAIL] No current version for {name}")
        new_versions[name] = bump(cur)

    print("\nTarget versions:")
    for name in targets:
        cur = versions.get(name) or js_versions.get(name)
        print(f"  {name}: ?v={cur} -> ?v={new_versions[name]}")

    html_files = list(iter_html(ROOT))
    print(f"\nScanning {len(html_files)} HTML files")

    total = 0
    for asset in targets:
        if asset not in versions:
            continue
        new_v = new_versions[asset]
        n_files = 0
        n_repl = 0
        for f in html_files:
            try:
                c = apply_to_file(f, asset, new_v, args.dry_run)
                if c:
                    n_files += 1
                    n_repl += c
            except Exception as e:
                print(f"  [WARN] {f.relative_to(ROOT)}: {e}")
        flag = "[DRY] " if args.dry_run else ""
        print(f"  {flag}{asset} -> ?v={new_v}: {n_repl} replacement(s) in {n_files} file(s)")
        total += n_repl

    # The stamps that live inside a JS file.
    for name, rel, pat in JS_ASSETS:
        if name not in targets:
            continue
        path = ROOT / rel
        text = path.read_text(encoding="utf-8", errors="ignore")
        new_v = new_versions[name]

        def repl(mm, new_v=new_v):
            return mm.group(1) + new_v + mm.group(3)

        new_text, n = pat.subn(repl, text)
        flag = "[DRY] " if args.dry_run else ""
        print(f"  {flag}{name} -> ?v={new_v}: {n} replacement(s) in {rel}")
        total += n
        if n and not args.dry_run:
            write_atomic(path, new_text)

    if args.dry_run:
        print(f"\n[DRY RUN] Would have made {total} replacements. Re-run without --dry-run to apply.")
    else:
        print(f"\n[DONE] Made {total} replacements. New version stamps in place.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
