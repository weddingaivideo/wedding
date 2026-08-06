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
]

EXCLUDE_DIRS = {"admin", "qa", "scripts", "__pycache__", "i18n", "js", "styles"}


def find_current_versions() -> dict[str, str]:
    """Read version from index.html (or first HTML that has all three)."""
    candidates = sorted(
        p for p in ROOT.rglob("*.html")
        if not (set(p.parts) & EXCLUDE_DIRS)
    )
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


def bump(version: str) -> str:
    """Bump a semver-ish version: '3.18' -> '3.19', '3.21' -> '3.22'."""
    if "." in version:
        major, minor = version.split(".", 1)
        return f"{major}.{int(minor) + 1}"
    return str(int(version) + 1)


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
        path.write_text(new_text, encoding="utf-8")
    return changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    ap.add_argument("--asset", choices=[n for n, _ in ASSETS], help="Bump only this asset (default: all)")
    args = ap.parse_args()

    versions = find_current_versions()
    print("Current versions:")
    for name, v in versions.items():
        print(f"  {name}: ?v={v}")

    targets = [args.asset] if args.asset else [n for n, _ in ASSETS]
    new_versions = {name: bump(versions[name]) for name in targets}

    print("\nTarget versions:")
    for name in targets:
        print(f"  {name}: ?v={versions[name]} -> ?v={new_versions[name]}")

    html_files = [
        p for p in ROOT.rglob("*.html")
        if not (set(p.parts) & EXCLUDE_DIRS)
    ]
    print(f"\nScanning {len(html_files)} HTML files")

    total = 0
    for asset in targets:
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

    if args.dry_run:
        print(f"\n[DRY RUN] Would have made {total} replacements. Re-run without --dry-run to apply.")
    else:
        print(f"\n[DONE] Made {total} replacements. New version stamps in place.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
