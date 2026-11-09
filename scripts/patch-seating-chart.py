#!/usr/bin/env python3
"""
Patch the seating-chart tool: PDF export, correct button labels, print source.

WHY
---
Three separate defects in one file family:

1. MIS-ASSIGNED BUTTON LABELS. In all 10 localized copies the four
   template-pick buttons were left in ENGLISH, and the translated template
   names were then written onto the "Export PNG" and "Print" buttons. So the
   Chinese page showed a button reading "经典招待会（8轮8场）" where it should
   have said "导出 PNG". The labels were shifted onto the wrong controls.

2. NO PDF EXPORT. The page's own comparison table claims "PNG + PDF + share
   link"; there was only an Export PNG button and a Print button.

3. ENGLISH INSIDE THE RENDERED ARTEFACT. The exported canvas drew the title
   "Wedding Seating Chart" and the toast said "Saved 1600x1200 PNG" in every
   language, so the PNG a Chinese user downloaded was half-English.

THE FIX
-------
Move all nine strings into the i18n dictionary and bind them:

  * Static button labels  -> data-i18n="tools.copy.<key>" on the element.
    The middleware (applyDataI18n) replaces the element text per language,
    so one binding fixes all 11 copies at once.
  * Runtime strings (the canvas title, the toasts) -> window.weddingAITool.t(),
    which reads the "tools.copy" namespace that the middleware injects as
    window.__WA_I18N__.

The patch is applied to all 11 copies (English + 10 localized) with the SAME
structural edit, because every copy has the same button markup and the same
function bodies - only the prose and the JSON-LD differ.

Idempotent: re-running it on an already-patched file changes nothing.

Usage:  python scripts/patch-seating-chart.py [--dry-run]
"""
import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
SLUG = "wedding-seating-chart-maker"

KEYS = {
    "classic": "tools.copy.seatTemplateClassic.zzzzzz5a01",
    "long": "tools.copy.seatTemplateLong.zzzzzz5a02",
    "intimate": "tools.copy.seatTemplateIntimate.zzzzzz5a03",
    "ushape": "tools.copy.seatTemplateUShape.zzzzzz5a04",
}

SAVE_BLOCK = """    // save
    if (window.weddingAITool && window.weddingAITool.canvasToBlob) {
      window.weddingAITool.canvasToBlob(c, 'image/png', 1.0).then(function (blob) {
        var name = 'wedding-seating-chart-' + Date.now() + '.png';
        window.weddingAITool.download(blob, name);
        if (window.weddingAITool.toast) window.weddingAITool.toast('Saved 1600\u00d71200 PNG', 'success');
      });
    } else {
      var url = c.toDataURL('image/png');
      var a = document.createElement('a');
      a.href = url; a.download = 'wedding-seating-chart.png';
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
    }
  }"""

NEW_TAIL = """    return c;
  }

  function exportPNG() {
    var c = buildChartCanvas();
    if (window.weddingAITool && window.weddingAITool.canvasToBlob) {
      window.weddingAITool.canvasToBlob(c, 'image/png', 1.0).then(function (blob) {
        var name = 'wedding-seating-chart-' + Date.now() + '.png';
        window.weddingAITool.download(blob, name);
        if (window.weddingAITool.toast) {
          window.weddingAITool.toast(
            window.weddingAITool.t ? window.weddingAITool.t('seatSavedPng', 'Saved 1600\u00d71200 PNG')
                                   : 'Saved 1600\u00d71200 PNG',
            'success');
        }
      });
    } else {
      var url = c.toDataURL('image/png');
      var a = document.createElement('a');
      a.href = url; a.download = 'wedding-seating-chart.png';
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
    }
  }

  // PDF export (added 2026-11-09). The page's own comparison table claims
  // "PNG + PDF + share link"; until now there was no PDF at all. jsPDF is
  // loaded on demand by the shared layer and the page size is exactly the
  // canvas size (1600x1200), so the PDF is a true print layout.
  function exportPDF() {
    if (!window.weddingAITool || !window.weddingAITool.downloadPdf) return;
    var c = buildChartCanvas();
    var name = 'wedding-seating-chart-' + Date.now() + '.pdf';
    window.weddingAITool.downloadPdf(c, name, { mime: 'image/jpeg', quality: 0.92 })
      .then(function () {
        if (window.weddingAITool.toast) {
          window.weddingAITool.toast(
            window.weddingAITool.t ? window.weddingAITool.t('seatSavedPdf', 'Saved PDF') : 'Saved PDF',
            'success');
        }
      })
      .catch(function () { /* downloadPdf already surfaced the error */ });
  }"""


def write_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmpwrite")
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def patch(text: str) -> tuple[str, list]:
    changes = []

    # --- 1. data-i18n on the four template-pick buttons --------------------
    for tmpl, key in KEYS.items():
        pat = re.compile(r'(<button\b[^>]*\bdata-template="' + tmpl + r'"[^>]*?)(>)')
        m = pat.search(text)
        if not m:
            continue
        if "data-i18n=" in m.group(1):
            continue
        text = text[:m.start()] + m.group(1) + ' data-i18n="' + key + '"' + m.group(2) + text[m.end():]
        changes.append("data-i18n:" + tmpl)

    # --- 2. data-i18n on the Export PNG + Print buttons ---------------------
    for ident, key in (("export-png-btn", "tools.copy.seatExportPng.zzzzzz5a05"),
                       ("print-btn", "tools.copy.seatPrint.zzzzzz5a06")):
        pat = re.compile(r'(<button\b[^>]*\bid="' + ident + r'"[^>]*?)(>)')
        m = pat.search(text)
        if not m:
            raise SystemExit(f"[FAIL] button #{ident} not found")
        if "data-i18n=" not in m.group(1):
            text = text[:m.start()] + m.group(1) + ' data-i18n="' + key + '"' + m.group(2) + text[m.end():]
            changes.append("data-i18n:" + ident)

    # --- 3. add the Download PDF button next to Print ----------------------
    if 'id="export-pdf-btn"' not in text:
        pat = re.compile(r'(<button\b[^>]*\bid="print-btn"[^>]*>.*?</button>)', re.S)
        m = pat.search(text)
        if not m:
            raise SystemExit("[FAIL] print button not found for PDF insertion")
        pdf_btn = ('<button type="button" class="seating-btn" id="export-pdf-btn" '
                   'data-i18n="tools.copy.seatDownloadPdf.zzzzzz5a07">Download PDF</button>')
        text = text[:m.end()] + " " + pdf_btn + text[m.end():]
        changes.append("pdf-button")

    # --- 4. print-source line (visible only in print) ----------------------
    if 'wa-tool-print-source' not in text:
        marker = '<div class="seating-export-row">'
        if marker in text:
            src = ('<div class="wa-tool-print-source">weddingai.video &middot; '
                   '<span data-i18n="tools.copy.seatChartTitle.zzzzzz5a08">Wedding Seating Chart</span></div>')
            text = text.replace(marker, src + marker, 1)
            changes.append("print-source")

    # --- 5. split exportPNG into buildChartCanvas + exportPNG + exportPDF -
    if "function buildChartCanvas()" not in text:
        if "function exportPNG() {" not in text:
            raise SystemExit("[FAIL] exportPNG() not found")
        text = text.replace("function exportPNG() {", "function buildChartCanvas() {", 1)
        if SAVE_BLOCK not in text:
            raise SystemExit("[FAIL] the save block did not match - inspect the file by hand")
        text = text.replace(SAVE_BLOCK, NEW_TAIL, 1)
        changes.append("export-split")

    # --- 6. the canvas title is a runtime string -> t() -------------------
    old_title = "ctx.fillText('Wedding Seating Chart', W / 2, 56);"
    if old_title in text:
        new_title = ("ctx.fillText(window.weddingAITool && window.weddingAITool.t\n"
                     "      ? window.weddingAITool.t('seatChartTitle', 'Wedding Seating Chart')\n"
                     "      : 'Wedding Seating Chart', W / 2, 56);")
        text = text.replace(old_title, new_title, 1)
        changes.append("canvas-title")

    # --- 7. the export PDF button needs its listener -----------------------
    if "exportPdfBtn" not in text:
        pat = re.compile(r"(exportPngBtn\.addEventListener\('click', function \(\) \{\s*\n\s*exportPNG\(\);\s*\n\s*\}\);)")
        m = pat.search(text)
        if not m:
            raise SystemExit("[FAIL] the exportPngBtn listener did not match")
        add = ("\n  var exportPdfBtn = document.getElementById('export-pdf-btn');\n"
               "  if (exportPdfBtn) exportPdfBtn.addEventListener('click', function () { exportPDF(); });")
        text = text[:m.end()] + add + text[m.end():]
        changes.append("pdf-listener")

    return text, changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    total = 0
    for lang in LANGS:
        p = (ROOT / "tools" / SLUG / "index.html") if lang == "en" else (ROOT / lang / "tools" / SLUG / "index.html")
        if not p.exists():
            print(f"  {lang}: MISSING {p}")
            continue
        original = p.read_text(encoding="utf-8")
        new, changes = patch(original)
        if not changes:
            print(f"  {lang}: already patched")
            continue
        if new == original:
            print(f"  {lang}: no change")
            continue
        # Sanity: the inline script must still parse.
        scripts = re.findall(r"(?s)<script\b[^>]*>(.*?)</script>", new)
        biggest = max(scripts, key=len) if scripts else ""
        tmp = Path(os.environ.get("TEMP", ".")) / "seating_inline_check.js"
        tmp.write_text(biggest, encoding="utf-8")
        import subprocess
        r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"[FAIL] {lang}: inline script does not parse:\n{r.stderr}")
        if not args.dry_run:
            write_atomic(p, new)
        print(f"  {lang}: {len(changes)} change(s) -> {', '.join(changes)}")
        total += len(changes)

    print(f"\ntotal changes: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
