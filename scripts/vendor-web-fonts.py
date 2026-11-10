#!/usr/bin/env python3
"""
Vendor the web fonts the site already names but has never loaded.

WHAT THIS DOES
--------------
`styles.css` declares

    --font-heading: 'Playfair Display', Georgia, serif;
    --font-body:    'Inter', -apple-system, BlinkMacSystemFont, sans-serif;

and the three design tools name three more families in their templates:

    'Playfair Display', Georgia, serif
    'Great Vibes', 'Apple Chancery', cursive
    'Montserrat', -apple-system, BlinkMacSystemFont, sans-serif

None of them ever loaded: the repository had no @font-face, no font file
and no Google Fonts <link>, and the CSP says `font-src 'self' data:`, so
Google Fonts was never allowed either. Every one of those names fell
through to the next entry in the stack - and for the romantic template
that meant 'Apple Chancery' (macOS only) and then `cursive`, which is
Comic Sans on Windows. **The same template produced a different PNG on
every machine.** For the site itself the effect was that the whole site
rendered in Georgia while its stylesheet claimed Playfair Display.

This copies the fonts out of the @fontsource packages into /fonts/,
writes the @font-face rules into styles.css, and puts the same rules
into styles.min.css.

WHY VARIABLE
------------
The static @fontsource build ships one file per (subset, weight). The
variable build ships one file per subset covering every weight, so
Montserrat is three files instead of twelve.

WHY THESE SUBSETS
-----------------
The site serves 11 languages. These families cover Latin, Latin-Extended
and Cyrillic - en, es, fr, de, pt (Latin + Latin Ext, for the French oe),
ru (Cyrillic) and the Latin-based languages. Arabic, Thai, Devanagari and
Japanese are NOT covered by any of them, so those pages keep the system
fallback - which is what the canvas uses too, so the page and the printed
file still agree.

Because every rule carries a unicode-range, a visitor only downloads the
subsets their page actually needs. A text page costs Playfair latin
(37 KB) + Inter latin (47 KB) + Inter latin italic (51 KB) = 135 KB; a
design tool page adds Great Vibes (42 KB) and Montserrat (37 KB).

THE LICENCE MUST TRAVEL WITH THE FILES
---------------------------------------
All three families are SIL Open Font License 1.1, which requires the
licence to be distributed with the font. Each family gets its own
directory with the LICENSE file next to the woff2 files. The version is in
the directory name (like js/vendor/face-api-0.22.2/) so a future upgrade
changes the URL and cannot be served stale from the CDN.

WHY styles.min.css IS PATCHED, NOT REGENERATED
-----------------------------------------------
styles.min.css is a committed build artefact. Regenerating it with the
clean-css on this machine (5.6.3) rewrites 77 rules and DROPS the
`.hero-bg .hero-video` rule - the one that hides the looping hero for
vestibular-sensitive users - because it chokes on a stray `};` that was
in styles.css. So the minified file is patched surgically: the @font-face
rules are inserted, everything else stays byte-identical.

Usage:
    python scripts/vendor-web-fonts.py            # fetch + install (idempotent)
    python scripts/vendor-web-fonts.py --verify   # check /fonts/ against npm
"""

import hashlib
import os
import re
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TMP = ROOT / ".tmp" / "pack"
FONTS = ROOT / "fonts"

# (package prefix, directory, family, kind, [(subset, style, file name), ...])
PACKAGES = [
    ("fontsource-variable-playfair-display-", "playfair-display-5.3.0",
     "Playfair Display", "variable", [
         ("latin", "normal", "playfair-display-latin-wght-normal.woff2"),
         ("latin-ext", "normal", "playfair-display-latin-ext-wght-normal.woff2"),
         ("cyrillic", "normal", "playfair-display-cyrillic-wght-normal.woff2"),
     ]),
    ("fontsource-variable-inter-", "inter-5.3.0", "Inter", "variable", [
        ("latin", "normal", "inter-latin-wght-normal.woff2"),
        ("latin", "italic", "inter-latin-wght-italic.woff2"),
        ("latin-ext", "normal", "inter-latin-ext-wght-normal.woff2"),
        ("latin-ext", "italic", "inter-latin-ext-wght-italic.woff2"),
        ("cyrillic", "normal", "inter-cyrillic-wght-normal.woff2"),
        ("cyrillic", "italic", "inter-cyrillic-wght-italic.woff2"),
    ]),
    # A script font with one weight. Latin only: a script face for
    # Cyrillic or Devanagari is meaningless, and the site falls back to
    # the system face for those scripts anyway.
    ("fontsource-great-vibes-", "great-vibes-5.3.0", "Great Vibes", "static", [
        ("latin", "normal", "great-vibes-latin-400-normal.woff2"),
    ]),
    ("fontsource-variable-montserrat-", "montserrat-5.3.0", "Montserrat", "variable", [
        ("latin", "normal", "montserrat-latin-wght-normal.woff2"),
        ("latin-ext", "normal", "montserrat-latin-ext-wght-normal.woff2"),
        ("cyrillic", "normal", "montserrat-cyrillic-wght-normal.woff2"),
    ]),
]

# npm package name for each tarball prefix.
NPM_NAMES = {
    "fontsource-variable-playfair-display-": "@fontsource-variable/playfair-display",
    "fontsource-variable-inter-": "@fontsource-variable/inter",
    "fontsource-great-vibes-": "@fontsource/great-vibes",
    "fontsource-variable-montserrat-": "@fontsource-variable/montserrat",
}

COMMENT = """/* ---------- Web fonts (self-hosted) ----------
   Playfair Display, Inter, Great Vibes and Montserrat are SIL Open Font
   License 1.1. They are served from THIS origin: the CSP allows
   font-src 'self' data:, and Google Fonts is not on the allowlist, so
   before these files existed every one of these family names fell
   through to the next entry in its stack - the site rendered in Georgia
   while its stylesheet claimed Playfair Display, and the romantic
   invitation template rendered in Comic Sans on Windows.
   The variable builds carry every weight in one file per subset, and
   the unicode-ranges keep a visitor from downloading a subset their
   page does not use. The licence travels with the files in
   /fonts/*/LICENSE. */
"""


def write_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmpwrite")
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def unicode_ranges(tar) -> dict:
    """Read the unicode-range of every file straight out of the
    @fontsource CSS, so the ranges are the fonts' own and not a hand
    copy that can drift.

    The package splits its CSS: index.css carries the upright rules and
    wght-italic.css the italic ones, so every stylesheet in the package
    is read.
    """
    out = {}
    css_files = [m.name for m in tar.getmembers()
                 if m.isfile() and m.name.endswith(".css") and "/files/" not in m.name]
    for c in css_files:
        try:
            css = tar.extractfile(c).read().decode("utf-8")
        except KeyError:
            continue
        for m in re.finditer(r"/\*\s*([^*]+?)\s*\*/\s*@font-face\s*\{(.*?)\}", css, re.S):
            body = m.group(2)
            ur = re.search(r"unicode-range:\s*([^;]+);", body)
            if not ur:
                continue
            out[m.group(1).strip()] = ur.group(1).strip()
    return out


def vendor_files():
    faces = []
    total = 0
    for prefix, dirname, family, kind, wanted in PACKAGES:
        tgz = sorted(TMP.glob(prefix + "*.tgz"))[-1]
        dest_dir = FONTS / dirname
        dest_dir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(tgz) as tar:
            names = tar.getnames()
            lic = [n for n in names if re.match(r"package/LICENSE", n)]
            if not lic:
                raise SystemExit("[FAIL] no LICENSE in %s" % tgz.name)
            with tar.extractfile(lic[0]) as fh:
                (dest_dir / "LICENSE").write_bytes(fh.read())
            ranges = unicode_ranges(tar)
            for subset, style, filename in wanted:
                src = "package/files/" + filename
                if src not in names:
                    raise SystemExit("[FAIL] %s is not in %s" % (filename, tgz.name))
                with tar.extractfile(src) as fh:
                    data = fh.read()
                (dest_dir / filename).write_bytes(data)
                total += len(data)
                # the @fontsource CSS names the file in the comment above
                # the rule, e.g. "playfair-display-latin-wght-normal"
                key = filename[:-len(".woff2")]
                if key not in ranges:
                    raise SystemExit("[FAIL] no unicode-range for %s" % filename)
                faces.append({
                    "family": family, "subset": subset, "style": style,
                    "dir": dirname, "file": filename, "range": ranges[key],
                    "weight": "400 900" if kind == "variable" else "400",
                })
        print("  %-26s %d file(s) + LICENSE" % (dirname, len(wanted)))
    print()
    print("  %d font files, %.0f KB on disk" % (len(faces), total / 1024))
    return faces


def pretty_rule(f) -> str:
    return ("/* %s - %s%s, SIL Open Font License 1.1 */\n"
            "@font-face {\n"
            "    font-family: '%s';\n"
            "    font-style: %s;\n"
            "    font-display: swap;\n"
            "    font-weight: %s;\n"
            "    src: url('/fonts/%s/%s') format('woff2');\n"
            "    unicode-range: %s;\n"
            "}"
            % (f["file"], f["subset"], " italic" if f["style"] == "italic" else "",
               f["family"], f["style"], f["weight"], f["dir"], f["file"], f["range"]))


def minified_rule(f) -> str:
    return ("@font-face{font-family:'%s';font-style:%s;font-display:swap;"
            "font-weight:%s;src:url('/fonts/%s/%s') format('woff2');"
            "unicode-range:%s}"
            % (f["family"], f["style"], f["weight"], f["dir"], f["file"], f["range"]))


def patch_styles_css(faces) -> bool:
    path = ROOT / "styles.css"
    marker = "/* ---------- Reset & Base ---------- */"
    start = "/* ---------- Web fonts (self-hosted) ----------"
    block = "\n" + COMMENT + "\n" + "\n\n".join(pretty_rule(f) for f in faces) + "\n\n"
    text = path.read_text(encoding="utf-8")
    if start in text:
        i = text.index(start)
        j = text.index(marker, i)
        new = text[:i] + block.lstrip("\n") + "\n" + text[j:]
    else:
        if marker not in text:
            raise SystemExit("[FAIL] could not find the insertion point in styles.css")
        new = text.replace(marker, block.lstrip("\n") + "\n" + marker, 1)
    if new == text:
        return False
    write_atomic(path, new)
    return True


def patch_styles_min_css(faces) -> bool:
    """Insert the @font-face rules into the committed minified file.

    The file is NOT regenerated: the clean-css on this machine rewrites 77
    rules and drops the `.hero-bg .hero-video` rule, which is the one that
    hides the looping hero for vestibular-sensitive users. Everything
    except the new rules stays byte-identical.
    """
    path = ROOT / "styles.min.css"
    original = path.read_text(encoding="utf-8")
    text = original
    rules = "".join(minified_rule(f) for f in faces)
    # Any existing copy of OUR rules goes first - all of them, not just the
    # one that happens to contain the first file name, or a second run
    # would leave duplicates behind.
    text, n = re.subn(r"@font-face\{[^}]*?/fonts/(?:playfair-display|inter|great-vibes|montserrat)-[^}]*\}",
                      "", text)
    if n:
        print("  removed %d existing @font-face rule(s) from styles.min.css" % n)
    i = text.index("}")
    new = text[:i + 1] + rules + text[i + 1:]
    if new == original:
        return False
    write_atomic(path, new)
    return True


def download_tarballs():
    """Fetch the npm packages into .tmp/pack/.

    npm on Windows is npm.cmd, which Python's subprocess cannot execute
    directly - CreateProcess does not resolve PATHEXT - so the call goes
    through cmd.exe. The tarballs land in .tmp/ (gitignored), so this has
    to run again on a fresh clone; --verify says so explicitly when a
    package is missing instead of failing with an IndexError.
    """
    TMP.mkdir(parents=True, exist_ok=True)
    for prefix, dirname, family, kind, wanted in PACKAGES:
        if sorted(TMP.glob(prefix + "*.tgz")):
            print("  %-46s already packed" % NPM_NAMES[prefix])
            continue
        pkg = NPM_NAMES[prefix]
        print("  npm pack %s ..." % pkg)
        r = subprocess.run(
            ["cmd", "/c", "npm", "pack", pkg, "--pack-destination", str(TMP)],
            capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("[FAIL] npm pack %s failed:\n%s"
                             % (pkg, (r.stderr or r.stdout)[-800:]))
        if not sorted(TMP.glob(prefix + "*.tgz")):
            raise SystemExit("[FAIL] npm pack %s produced no tarball" % pkg)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def verify() -> int:
    """Check /fonts/ and the two stylesheets that reference it.

    Four things can go wrong and none of them raises an error on their
    own:

      1. a font file is missing, truncated or edited by hand;
      2. an @font-face rule is dropped from one of the two stylesheets -
         the site silently falls back to Georgia and NOTHING looks broken;
      3. a rule is duplicated in the minified stylesheet;
      4. the accessibility rule clean-css would drop is gone.

    The byte-level comparison against the npm packages only runs when the
    tarballs are in .tmp/pack (they are gitignored, so a fresh clone has
    none). When they are missing the provenance check is reported as
    SKIPPED, not as a pass - and the integrity checks above still run.
    """
    problems = []
    notes = []
    checked = 0

    files = []
    for _, dirname, family, kind, wanted in PACKAGES:
        for _, _, filename in wanted:
            files.append((dirname, filename))

    # 1. the files themselves
    for dirname, filename in files:
        dest = FONTS / dirname / filename
        if not dest.exists():
            problems.append("%s: missing" % dest.relative_to(ROOT))
            continue
        data = dest.read_bytes()
        checked += 1
        if not data.startswith(b"wOF2"):
            problems.append("%s: not a woff2 (the file starts with %r)"
                            % (dest.relative_to(ROOT), data[:4]))
        if len(data) < 4096:
            problems.append("%s: only %d bytes - that is truncated"
                            % (dest.relative_to(ROOT), len(data)))
        if not (FONTS / dirname / "LICENSE").exists():
            problems.append("%s: LICENSE missing - the OFL requires it to "
                            "travel with the font" % dirname)

    # 2 + 3. the stylesheets
    pretty = (ROOT / "styles.css").read_text(encoding="utf-8")
    mini = (ROOT / "styles.min.css").read_text(encoding="utf-8")
    for dirname, filename in files:
        url = "/fonts/%s/%s" % (dirname, filename)
        n_pretty = pretty.count("url('%s')" % url)
        n_mini = mini.count("url('%s')" % url)
        if n_pretty != 1:
            problems.append("styles.css references %s %d time(s), expected 1"
                            % (url, n_pretty))
        if n_mini != 1:
            problems.append("styles.min.css references %s %d time(s), expected 1"
                            % (url, n_mini))
        checked += 1
    dupes = re.findall(r"@font-face\{[^}]*?/fonts/[^}]*?\}", mini)
    if len(dupes) != len(files):
        problems.append("styles.min.css has %d @font-face rules, expected %d"
                        % (len(dupes), len(files)))

    # 4. the rule clean-css drops
    if ".hero-bg .hero-video" not in mini:
        problems.append("styles.min.css lost `.hero-bg .hero-video` - "
                        "the hero video is supposed to be hidden for "
                        "vestibular-sensitive visitors")

    # provenance, when the packages are available
    have_tarballs = True
    for prefix, dirname, family, kind, wanted in PACKAGES:
        tgzs = sorted(TMP.glob(prefix + "*.tgz"))
        if not tgzs:
            have_tarballs = False
            notes.append("%s: no npm tarball in %s" % (dirname, TMP))
            continue
        with tarfile.open(tgzs[-1]) as tar:
            names = tar.getnames()
            for _, _, filename in wanted:
                dest = FONTS / dirname / filename
                src = "package/files/" + filename
                if not dest.exists() or src not in names:
                    continue
                with tar.extractfile(src) as fh:
                    want = fh.read()
                got = dest.read_bytes()
                checked += 1
                if want != got:
                    problems.append("%s: differs from the npm package "
                                    "(%s vs %s)"
                                    % (dest.relative_to(ROOT), sha(want), sha(got)))
    if not have_tarballs:
        notes.append("provenance NOT checked - run "
                     "`python scripts/vendor-web-fonts.py` to fetch the npm "
                     "packages, then `--verify` again")

    print("checked %d font file(s) and their @font-face rules" % checked)
    for n in notes:
        print("  note: " + n)
    if problems:
        print("FONT VERIFY FAILED")
        for p in problems:
            print("  - " + p)
        return 1
    print("FONT VERIFY OK")
    return 0


def main():
    if "--verify" in sys.argv:
        return verify()
    download_tarballs()
    faces = vendor_files()
    a = patch_styles_css(faces)
    b = patch_styles_min_css(faces)
    print("  styles.css     %s" % ("updated" if a else "already up to date"))
    print("  styles.min.css %s" % ("updated" if b else "already up to date"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
