#!/usr/bin/env python3
"""
Make the canvas tools wait for the web fonts before they draw (§2.16).

THE DEFECT
----------
The three design tools name web fonts in their templates:

    'Playfair Display', Georgia, serif
    'Great Vibes', 'Apple Chancery', cursive
    'Montserrat', -apple-system, BlinkMacSystemFont, sans-serif

None of them had ever loaded (no @font-face, no font file, no Google
Fonts <link>, and the CSP's `font-src 'self' data:` never allowed Google
Fonts either). So every one of those names fell through to the next entry
in the stack - and for the romantic template that meant 'Apple Chancery',
which exists on macOS and nowhere else, and then the `cursive` keyword,
which is Comic Sans on Windows.

A canvas draws with whatever font is loaded AT THAT MOMENT. So the draw
happened in the fallback face and **the exported PNG was baked with it**:
the same template produced a different file on every operating system.

THE FIX
-------
`common.js` gains `fontsReady()`, which asks the browser for the families
and resolves when they have arrived. Each tool:

  * waits for them before its FIRST draw, so the preview is right; and
  * waits for them before the file is baked, so the export is right even
    if the visitor clicks Download in the first second.

The text that is about to be drawn is passed to `document.fonts.load()`,
so the browser only downloads the subset that text needs: an Arabic page
never pulls the Latin subset, and falls back exactly like the page does.

Usage:
    python scripts/patch-font-gate.py [--dry-run]

Afterwards ALWAYS run:
    python scripts/propagate-tool-js.py --tools save-the-date-maker,wedding-invitation-maker,wedding-video-invitation-maker
    python scripts/check-tool-script-syntax.py
"""

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMMON = ROOT / "js" / "tools" / "common.js"

# ===========================================================================
# common.js - the shared helper
# ===========================================================================

OLD_COMMON_ANCHOR = """  // ---------- HEIC decoding --------------------------------------------------
"""

NEW_COMMON_ANCHOR = """  // ---------- web fonts ------------------------------------------------------
  //
  // The design templates name web fonts: 'Playfair Display', 'Great Vibes'
  // and 'Montserrat'. A canvas draws with whatever font is loaded AT THAT
  // MOMENT, so a draw that happens before the font arrives bakes the
  // FALLBACK into the file - and the fallback is not the same on every
  // operating system: the romantic template fell back to 'Apple Chancery'
  // on macOS and to Comic Sans on Windows, which meant the same template
  // produced a different PNG on every machine.
  //
  // fontsReady() resolves once the families are loaded. `text` is passed on
  // so the browser only fetches the subset that text needs: an Arabic page
  // never pulls the Latin subset and falls back exactly like the page does.
  var CANVAS_FONT_FAMILIES = ['Playfair Display', 'Great Vibes', 'Montserrat', 'Inter'];

  function fontsReady(families, text) {
    if (!document.fonts || !document.fonts.load) return Promise.resolve(false);
    var list = families || CANVAS_FONT_FAMILIES;
    var jobs = [];
    list.forEach(function (name) {
      try {
        jobs.push(text
          ? document.fonts.load('16px "' + name + '"', text)
          : document.fonts.load('16px "' + name + '"'));
      } catch (e) {
        // An unknown family is not an error - the fallback is still valid.
      }
    });
    if (!jobs.length) return Promise.resolve(false);
    return Promise.all(jobs).then(function () { return true; })
      .catch(function () { return false; });
  }

  // ---------- HEIC decoding --------------------------------------------------
"""

OLD_COMMON_EXPORT = """    downloadPdfPages: downloadPdfPages,
"""

NEW_COMMON_EXPORT = """    downloadPdfPages: downloadPdfPages,
    fontsReady: fontsReady,
"""

# ===========================================================================
# the three design tools
# ===========================================================================

GATE_HELPER = """      // §2.16 - the templates name web fonts ('Playfair Display',
      // 'Great Vibes', 'Montserrat'). A canvas draws with whatever font is
      // loaded AT THAT MOMENT, so the first draw has to wait for them: the
      // fallback face would otherwise be baked into the exported file, and
      // the fallback is not the same on every operating system - the
      // romantic template fell back to 'Apple Chancery' on macOS and to
      // Comic Sans on Windows, so the same template produced a different
      // PNG on every machine.
      //
      // fontsReady() resolves once the families are loaded; fontsLoaded
      // says whether that has happened. The first draw waits for it, and
      // every export waits before the file is baked.
      var fontsLoaded = false;
      var fontsPromise = null;
      function fontsReady() {
        if (!fontsPromise) {
          var T = window.weddingAITool;
          fontsPromise = (T && T.fontsReady) ? T.fontsReady() : Promise.resolve(false);
        }
        return fontsPromise.then(function (ok) { fontsLoaded = true; return ok; });
      }

      function render() {
        if (!fontsLoaded) {
          fontsReady().then(function () { render(); });
          return;
        }
"""

OLD_RENDER_HEAD = """      function render() {
"""

# (tool slug, [(old, new, marker)], ...)
TOOLS = {
    "save-the-date-maker": [
        (OLD_RENDER_HEAD, GATE_HELPER, "var fontsLoaded = false;"),
        ("      downloadBtn.addEventListener('click', function () {\n",
         "      downloadBtn.addEventListener('click', async function () {\n"
         "        // §2.16 - the file must not be baked with the fallback face.\n"
         "        await fontsReady();\n",
         "await fontsReady();"),
    ],
    "wedding-invitation-maker": [
        (OLD_RENDER_HEAD, GATE_HELPER, "var fontsLoaded = false;"),
        ("      function renderAtSize(targetW, targetH, filenamePrefix) {\n",
         "      async function renderAtSize(targetW, targetH, filenamePrefix) {\n"
         "        // §2.16 - the file must not be baked with the fallback face.\n"
         "        await fontsReady();\n",
         "await fontsReady();"),
    ],
    "wedding-video-invitation-maker": [
        (OLD_RENDER_HEAD, GATE_HELPER, "var fontsLoaded = false;"),
        ("      function downloadFrames() {\n",
         "      async function downloadFrames() {\n"
         "        // §2.16 - the frames must not be baked with the fallback face.\n"
         "        await fontsReady();\n",
         "await fontsReady();"),
    ],
}


def write_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmpwrite")
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def apply_blocks(text: str, blocks, what: str) -> tuple:
    changes = 0
    for old, new, marker in blocks:
        if marker in text:
            continue
        if old not in text:
            raise SystemExit("[FAIL] could not find %s in %s" % (what, old[:60]))
        text = text.replace(old, new, 1)
        changes += 1
    return text, changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    total = 0

    # --- common.js -------------------------------------------------------
    text = COMMON.read_text(encoding="utf-8")
    before = text
    text, n = apply_blocks(text, [
        (OLD_COMMON_ANCHOR, NEW_COMMON_ANCHOR, "function fontsReady(families, text) {"),
        (OLD_COMMON_EXPORT, NEW_COMMON_EXPORT, "fontsReady: fontsReady,"),
    ], "common.js")
    total += n
    if text != before and not args.dry_run:
        write_atomic(COMMON, text)
    print("  common.js %d change(s)" % n)

    # --- the three tools -------------------------------------------------
    for slug, blocks in TOOLS.items():
        p = ROOT / "tools" / slug / "index.html"
        text = p.read_text(encoding="utf-8")
        before = text
        text, n = apply_blocks(text, blocks, slug)
        total += n
        if text != before and not args.dry_run:
            write_atomic(p, text)
        print("  %-30s %d change(s)" % (slug, n))

    if args.dry_run:
        print("\n[DRY RUN] nothing was written")
    else:
        print("\nNow run:")
        print("  python scripts/propagate-tool-js.py --tools save-the-date-maker,wedding-invitation-maker,wedding-video-invitation-maker")
        print("  python scripts/check-tool-script-syntax.py")
        print("  python scripts/bump_cache_version.py --asset common.js")
    return 0


if __name__ == "__main__":
    sys.exit(main())
