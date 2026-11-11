# -*- coding: utf-8 -*-
"""Add the three things the US SERP says the stationery page was missing.

WHAT THE SERP SAYS
------------------
Three gaps, all of them repeated on four or more of the top ten results
(see internal-tools/serp-research-stationery.md):

1. "Print at 100% / Actual Size, never Fit to Page." It is on
   placecard.us, apollostemplates.com, printablepress.com and
   eathealthy365.com - and it is one of the #1 result's own FAQ
   questions. Our page had the printer QUALITY ("High" or "Best") but
   never the printer SCALE, which is the setting that decides whether
   the 5 x 7 invitation comes out 5 x 7.
2. The piece table had no ENVELOPE column. Every guide gives the size
   together with the envelope it fits - that is how the reader knows
   what to buy, and the invitation is 5 x 7 BECAUSE of A7.
3. The send window was "six to eight weeks", which is the absolute
   minimum. The SERP consensus is 8-10 weeks, with 6 weeks as the floor
   (paperlust, bridalbybentley, roomblocks).

WHAT IT DOES
------------
Inserts the envelope column into the piece table, adds the 100% bullet
to the printing list, adds the FAQ entry, and rewrites the two timing
sentences. Every new or changed element gets its data-i18n key from the
SAME function the binder uses, so the key is the one the binder would
have produced.

Idempotent: a second run changes nothing and says so.

Usage
-----
    python scripts/patch-stationery-serp.py
    python scripts/patch-stationery-serp.py --dry-run
"""
import argparse
import importlib.util
import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLUG = "wedding-stationery-set-maker"
PAGE = ROOT / "tools" / SLUG / "index.html"

spec = importlib.util.spec_from_file_location(
    "bind", ROOT / "scripts" / "add-tool-i18n-bindings.py")
bind = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bind)


def key(tag, text):
    return bind.make_key(SLUG, tag, text)


# ---------------------------------------------------------------- the table
# piece -> the envelope it fits. The two "stands on the table" pieces
# share one text, so they share one key.
ENVELOPES = [
    ("invitation", "A7 (5.25 × 7.25 in)"),
    ("rsvp_card", "4-bar (A1)"),
    ("place_card", "None - it stands on the table"),
    ("table_card", "None - it stands on the table"),
    ("menu_card", "A2"),
    ("poster", "None - it is a sign"),
]

PRINT_STRONG = "Print at 100% or \"Actual Size\", never \"Fit to Page\""
PRINT_SPAN = ("A scaled sheet turns a 5 × 7 invitation into a different "
              "size, the trim guides no longer match the paper, and a 4 × 6 "
              "card comes out of a 5 × 7 envelope.")

FAQ_Q = "Should I print at 100% or fit to page?"
FAQ_A = ("At 100%, or on the setting your printer calls \"Actual size\". "
         "\"Fit to page\" rescales the sheet to whatever paper is in the "
         "tray, so the invitation comes out the wrong size and the crop "
         "marks no longer match the cut.")

TIMING_BODY = ("Eight to ten weeks before the wedding for a local wedding - "
               "six weeks is the absolute minimum, long enough for guests to "
               "book a hotel, short enough that it does not feel like an "
               "announcement. For a destination wedding, three months ahead, "
               "because people need to arrange travel and accommodation. "
               "Save the dates go out separately, six to eight months ahead.")

TIMING_FAQ = ("Eight to ten weeks before a local wedding - six weeks is the "
              "absolute minimum - and three months ahead for a destination "
              "wedding so guests can book travel. Save the dates go out on "
              "their own, six to eight months ahead.")

LIMITS = ("The limits, up front: one set is one PDF of six pages, the poster "
          "prints at 150 DPI rather than 300, and the largest page is limited "
          "by the memory of your own device - a canvas of 5400 × 7200 pixels "
          "is more than a phone wants to hold. There is no upload and no file "
          "size to worry about.")


def patch_table(html):
    """Insert the Envelope column: one th and one td per row."""
    if "th_text.envelope" in html:
        return html, 0
    n = 0
    # The header
    m = re.search(r'(<th data-i18n="[^"]*">Finished size</th>)', html)
    if not m:
        raise SystemExit("[FAIL] the Finished size header was not found")
    th = ('<th data-i18n="%s">Envelope</th>'
          % key("th", "Envelope"))
    html = html[:m.end(1)] + th + html[m.end(1):]
    n += 1
    # The rows. The piece is found by its KEY SEGMENT, because two rows
    # share a size cell (the place card and the table card are both
    # 3.5 x 2 in) and matching on the text would hit the wrong row.
    for piece, envelope in ENVELOPES:
        row = re.search(r'<tr>(?:(?!</tr>).)*?td_text\.%s\.(?:(?!</tr>).)*?</tr>'
                        % re.escape(piece), html, re.S)
        if not row:
            raise SystemExit("[FAIL] the row for %s was not found" % piece)
        cells = list(re.finditer(r'<td\b[^>]*>.*?</td>', row.group(0), re.S))
        if len(cells) < 2:
            raise SystemExit("[FAIL] the row for %s has %d cells"
                             % (piece, len(cells)))
        at = cells[1].end()          # right after the size cell
        td = '<td data-i18n="%s">%s</td>' % (key("td", envelope), envelope)
        abs_at = row.start() + at
        html = html[:abs_at] + td + html[abs_at:]
        n += 1
    return html, n


def patch_print_bullet(html):
    """Add the 100% bullet after the printer-quality one."""
    if PRINT_STRONG in html:
        return html, 0
    m = re.search(r'(<li><strong[^>]*>Set the printer to its best mode</strong>'
                  r'.*?</li>)', html, re.S)
    if not m:
        raise SystemExit("[FAIL] the printer-quality bullet was not found")
    li = ('<li><strong data-i18n="%s">%s</strong> '
          '<span data-i18n="%s">%s</span></li>'
          % (key("strong", PRINT_STRONG), PRINT_STRONG,
             key("span", PRINT_SPAN), PRINT_SPAN))
    html = html[:m.end(1)] + li + html[m.end(1):]
    return html, 1


def patch_faq(html):
    """Add the 100% FAQ entry after the 'at home' one."""
    if FAQ_Q in html:
        return html, 0
    m = re.search(r'(<details>\s*<summary[^>]*>Can I print wedding invitations '
                  r'at home\?</summary>.*?</details>)', html, re.S)
    if not m:
        raise SystemExit("[FAIL] the 'at home' FAQ entry was not found")
    block = ('\n                    <details>\n'
             '                        <summary data-i18n="%s">%s</summary>\n'
             '                        <p data-i18n="%s">%s</p>\n'
             '                    </details>'
             % (key("summary", FAQ_Q), FAQ_Q,
                key("p", FAQ_A), FAQ_A))
    html = html[:m.end(1)] + block + html[m.end(1):]
    return html, 1


def patch_timing(html):
    """Rewrite the two timing sentences."""
    n = 0
    old_body = ("Six to eight weeks before the wedding for a local wedding - "
                "long enough for guests to book a hotel, short enough that "
                "it does not feel like an announcement. For a destination "
                "wedding, three months ahead, because people need to arrange "
                "travel and accommodation. Save the dates go out separately, "
                "six to eight months ahead.")
    old_faq = ("Six to eight weeks before a local wedding, and three months "
               "ahead for a destination wedding so guests can book travel. "
               "Save the dates go out on their own, six to eight months ahead.")
    for old, new, tag in ((old_body, TIMING_BODY, "p"),
                          (old_faq, TIMING_FAQ, "p")):
        pat = re.compile(r'<p data-i18n="([^"]*)">' + re.escape(old) + r'</p>')
        m = pat.search(html)
        if not m:
            continue
        html = html[:m.start()] + ('<p data-i18n="%s">%s</p>'
                                   % (key(tag, new), new)) + html[m.end():]
        n += 1
    return html, n


def patch_limits(html):
    """State the limits.

    SERP rule 3: "Every ranking tool page publishes its limits. A hidden
    limit reads as a scam in this SERP; a stated limit reads as honest."
    The page already said the poster is 150 DPI, but the ceiling was
    spread over two sentences, so the gate - and a reader scanning the
    page - could not see one stated limit anywhere.
    """
    if LIMITS in html:
        return html, 0
    m = re.search(r'<p[^>]*data-i18n="[^"]*"[^>]*>The poster is exported at 150 DPI '
                  r'rather than 300.*?</p>', html, re.S)
    if not m:
        raise SystemExit("[FAIL] the poster note was not found")
    para = ('\n                <p data-i18n="%s">%s</p>'
            % (key("p", LIMITS), LIMITS))
    html = html[:m.end()] + para + html[m.end():]
    return html, 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    html = PAGE.read_text(encoding="utf-8")
    original = html
    html, n1 = patch_table(html)
    html, n2 = patch_print_bullet(html)
    html, n3 = patch_faq(html)
    html, n4 = patch_timing(html)
    html, n5 = patch_limits(html)
    total = n1 + n2 + n3 + n4 + n5
    if html == original:
        print("no change - the page already has the SERP additions")
        return 0
    print("table cells: %d, print bullet: %d, faq: %d, timing: %d, limits: %d"
          % (n1, n2, n3, n4, n5))
    if args.dry_run:
        print("(dry run - nothing written)")
        return 0
    PAGE.write_text(html, encoding="utf-8", newline="")
    print("patched %s" % PAGE.relative_to(ROOT))
    print("Now rebuild the i18n map and re-translate the changed strings:")
    print("  python scripts/add-tool-i18n-bindings.py --slug %s" % SLUG)
    return 0


if __name__ == "__main__":
    sys.exit(main())
