#!/usr/bin/env python3
"""Migration: wrap the wide pricing/comparison tables in a .table-scroll
container so the table itself can stay a real <table>.

Why: styles.css sets `display:block; overflow-x:auto` on
.comparison-table / .full-pricing-table to get horizontal scrolling on
narrow screens. A display:block table shrink-wraps its inner anonymous
table box to the content width, so the table no longer fills 100% of its
column -- and the element's own background paints the leftover width as a
blank white column. Moving the scroll container to a wrapper fixes it.

Idempotent: a table already preceded by a .table-scroll wrapper is skipped.
Preserves each file's existing line endings byte-for-byte outside the
inserted wrapper lines.
"""
import re
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGET_CLASSES = {"full-pricing-table", "comparison-table"}
TABLE_START = re.compile(r"<table\b", re.I)


def find_tables(html):
    """Return (start, end) spans of the target tables, outermost first."""
    spans = []
    i = 0
    while True:
        m = TABLE_START.search(html, i)
        if not m:
            break
        tag_end = html.find(">", m.end())
        if tag_end == -1:
            break
        attrs = html[m.end():tag_end]
        cm = re.search(r"\bclass\s*=\s*\"([^\"]*)\"", attrs, re.I)
        classes = set(cm.group(1).split()) if cm else set()
        if not classes & TARGET_CLASSES:
            i = tag_end + 1
            continue
        # matching </table>, tracking nesting
        depth, j = 1, tag_end + 1
        while depth:
            nxt_open = html.find("<table", j)
            nxt_close = html.find("</table>", j)
            if nxt_close == -1:
                break
            if nxt_open != -1 and nxt_open < nxt_close:
                depth += 1
                j = nxt_open + 1
            else:
                depth -= 1
                j = nxt_close + 8
        spans.append((m.start(), j))
        i = j
    return spans


def transform(html):
    """Wrap each target table in <div class="table-scroll">.

    The table block keeps its own indentation, so the diff is exactly
    +2 lines per table and stays easy to review or revert.
    """
    spans = find_tables(html)
    if not spans:
        return html, 0
    out = []
    pos = 0
    count = 0
    for start, end in spans:
        before = html[max(0, start - 300):start]
        if "table-scroll" in before:
            continue
        block = html[start:end]
        line_start = html.rfind("\n", 0, start) + 1
        prefix = html[line_start:start]
        if prefix.strip() == "":
            ind = prefix
            out.append(html[pos:line_start])
            out.append(f'{ind}<div class="table-scroll">\n')
            out.append(f'{ind}{block}')          # keep the table's own indent
            out.append(f'\n{ind}</div>')
            pos = end
        else:
            # table not at the start of a line -- keep it inline
            out.append(html[pos:start])
            out.append('<div class="table-scroll">\n')
            out.append(block)
            out.append('\n</div>')
            pos = end
        count += 1
    out.append(html[pos:])
    return "".join(out), count


def main():
    # Only the tracked HTML files are deployed; skip tmp/, qa/, .git/ etc.
    out = subprocess.run(
        ["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    total_files = total_tables = 0
    for rel in out:
        path = ROOT / rel
        raw = path.read_bytes()
        try:
            html = raw.decode("utf-8")
        except UnicodeDecodeError:
            print("SKIP (not utf-8):", rel)
            continue
        new, n = transform(html)
        if n:
            path.write_bytes(new.encode("utf-8"))
            total_files += 1
            total_tables += n
    print(f"wrapped {total_tables} tables in {total_files} files")


if __name__ == "__main__":
    sys.exit(main())
