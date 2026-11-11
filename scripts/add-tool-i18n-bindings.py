#!/usr/bin/env python3
"""
Bind every visible text element of a tool page to a flat i18n key.

WHY THIS EXISTS
---------------
A tool page reaches its 10 non-English readers through the middleware's
`applyDataI18n()`: an element that carries `data-i18n="<key>"` gets its
inner HTML REPLACED by `i18n/<lang>.json[<key>]`. An element without a key
keeps whatever the static file says - which for a language copy means
English.

So "the page is translated" is not a property of the page, it is a property
of the BINDINGS: every element the reader can read has to carry a key, and
every key has to exist in all 11 dictionaries. A page can look perfect in
English, ship a full 11-language dictionary, and still show English to a
Hindi reader because one `<li>` was never bound.

WHAT IT DOES
------------
1. Parses the page with an offset-tracking scanner (NOT a regex - a regex
   cannot tell `<p>` from the `<p>` nested inside it, so it reports the
   outer element as "mixed" and misses every child).
2. Finds every text-bearing element inside <main>.
3. Gives each one a key `tools.<slug>.<tag>_text.<snippet>.<hash8>`.
4. Injects `data-i18n="<key>"` into the opening tag.
5. Writes the key -> English text map to a JSON file for the translator.

MIXED CONTENT
-------------
`<p>Some text <a href="/x/">a link</a></p>` cannot simply be bound: the
middleware replaces the WHOLE inner HTML, so the <a> would vanish in all
ten languages and the page would lose its internal links.

So the loose text runs are wrapped in `<span data-i18n="...">` and the <a>
keeps its own href. The dictionary then holds plain text only - no markup -
which is what a machine translator can be trusted with.

(The alternative - putting `<a href="/x/">` inside the dictionary value -
would work too, but then every language needs its own href AND the
translator has to leave the markup alone. Plain text is the safer shape.)

IDEMPOTENT
----------
Re-running it changes nothing: an element that already has a data-i18n is
left alone, and the map is rebuilt from the bindings that are really there.

Usage
-----
    python scripts/add-tool-i18n-bindings.py --slug wedding-stationery-set-maker
    python scripts/add-tool-i18n-bindings.py --slug <slug> --dry-run
"""

import argparse
import hashlib
import html as htmlmod
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Elements whose text a reader sees and a translator should handle.
TEXT_TAGS = {
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "li", "td", "th", "label", "button", "summary", "option",
    "figcaption", "blockquote", "dt", "dd", "caption", "legend",
    "a", "span", "strong", "em", "small", "b", "i", "u", "abbr",
}

# Never translate these: code, scripts, and the symbols that only separate.
SKIP_TAGS = {
    "script", "style", "code", "pre", "kbd", "samp", "var", "textarea",
    "svg", "math", "noscript", "template", "iframe",
    "input", "img", "br", "hr", "meta", "link", "source", "area", "base",
    "col", "embed", "param", "track", "wbr",
}

VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}

# Text that is only punctuation carries no meaning - leave it alone.
HAS_LETTER = re.compile(r"[0-9A-Za-z\u00c0-\u024f\u0370-\u03ff\u0400-\u04ff"
                         r"\u0590-\u05ff\u0600-\u06ff\u0e00-\u0e7f"
                         r"\u3040-\u30ff\uac00-\ud7af\U0001f000-\U0001ffff]")


def tokenize(html, lo, hi):
    """Yield (kind, name, start, end, raw) for every tag in html[lo:hi].

    kind is one of: open, close, other.
    `start`/`end` are absolute offsets into `html`.
    """
    out = []
    i = lo
    while i < hi:
        j = html.find("<", i)
        if j < 0 or j >= hi:
            break
        if html.startswith("<!--", j):
            k = html.find("-->", j)
            k = hi if k < 0 else k + 3
            out.append(("other", None, j, k, ""))
            i = k
            continue
        if html.startswith("<!", j) or html.startswith("<?", j):
            k = html.find(">", j)
            k = hi if k < 0 else k + 1
            out.append(("other", None, j, k, ""))
            i = k
            continue
        m = re.match(r"</\s*([a-zA-Z][\w:-]*)", html[j:])
        if m:
            k = html.find(">", j)
            k = hi if k < 0 else k + 1
            out.append(("close", m.group(1).lower(), j, k, ""))
            i = k
            continue
        m = re.match(r"<([a-zA-Z][\w:-]*)", html[j:])
        if m:
            name = m.group(1).lower()
            k = j + len(m.group(0))
            quote = None
            while k < hi:
                c = html[k]
                if quote:
                    if c == quote:
                        quote = None
                elif c in "\"'":
                    quote = c
                elif c == ">":
                    break
                k += 1
            k = min(k + 1, hi)
            out.append(("open", name, j, k, html[j:k]))
            i = k
            continue
        i = j + 1
    return out


class Element:
    __slots__ = ("name", "open_start", "open_end", "open_raw", "attrs",
                 "children", "text_runs", "parent", "data_start", "data_end")

    def __init__(self, name, open_start, open_end, open_raw, parent):
        self.name = name
        self.open_start = open_start
        self.open_end = open_end
        self.open_raw = open_raw
        self.attrs = open_raw
        self.children = []
        self.text_runs = []          # (start, end) offsets of direct text
        self.parent = parent
        self.data_start = open_end
        self.data_end = open_end

    def text(self, html):
        return html[self.data_start:self.data_end]


def parse_region(html, lo, hi):
    """Parse html[lo:hi] into a tree of Element.

    One pass. The gaps between tags are the direct text runs of whichever
    element is open at that moment, so text and elements are collected
    together - a second pass would rebuild the tree and double every child.
    """
    toks = tokenize(html, lo, hi)
    root = Element("#root", lo, lo, "", None)
    stack = [root]
    prev_end = lo
    for kind, name, s, e, raw in toks:
        if s > prev_end:
            stack[-1].text_runs.append((prev_end, s))
        prev_end = e
        if kind == "open":
            el = Element(name, s, e, raw, stack[-1])
            stack[-1].children.append(el)
            el.data_start = e
            el.data_end = e
            if name in VOID_TAGS or raw.rstrip(">").rstrip().endswith("/"):
                continue
            stack.append(el)
        elif kind == "close":
            for idx in range(len(stack) - 1, 0, -1):
                if stack[idx].name == name:
                    stack[idx].data_end = s
                    del stack[idx:]
                    break
    if prev_end < hi:
        stack[-1].text_runs.append((prev_end, hi))
    return root


def attrs_of(raw):
    """Return the attribute string of an opening tag (without <name and >)."""
    m = re.match(r"<([a-zA-Z][\w:-]*)([\s\S]*?)/?>$", raw)
    if not m:
        return ""
    return m.group(2)


def has_attr(attrs, name):
    return re.search(r"(?:^|\s)" + re.escape(name) + r"\s*=", attrs) is not None


def get_attr(attrs, name):
    m = re.search(r"(?:^|\s)" + re.escape(name) + r'\s*=\s*"([^"]*)"', attrs)
    if m:
        return m.group(1)
    m = re.search(r"(?:^|\s)" + re.escape(name) + r"\s*=\s*'([^']*)'", attrs)
    if m:
        return m.group(1)
    return None


def snippet_of(text, limit=40):
    s = re.sub(r"[^0-9A-Za-z]+", "_", text.strip().lower()).strip("_")
    s = re.sub(r"_+", "_", s)
    return (s[:limit].rstrip("_") or "text")


def make_key(slug, tag, text):
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
    return "tools.%s.%s_text.%s.%s" % (slug, tag, snippet_of(text), digest)


def collect(root, html, slug, out_keys):
    """Walk the tree and decide what to bind. Returns a list of edits."""
    edits = []   # (kind, ...) applied later from the end of the file

    def direct_text(el):
        return html[el.data_start:el.data_end]

    def visit(el):
        for child in el.children:
            if child.name in SKIP_TAGS:
                continue
            visit(child)
        # Now decide about THIS element.
        if el.name not in TEXT_TAGS:
            return
        if el.parent is not None and el.parent.name in SKIP_TAGS:
            return
        attrs = attrs_of(el.open_raw)
        if has_attr(attrs, "data-i18n"):
            out_keys.append((get_attr(attrs, "data-i18n"), el.text(html)))
            return
        if has_attr(attrs, "aria-hidden"):
            if get_attr(attrs, "aria-hidden") == "true":
                return
        # children that are not skipped still count as children
        real_children = [c for c in el.children if c.name not in SKIP_TAGS]
        if not real_children:
            text = el.text(html)
            plain = htmlmod.unescape(text)
            plain = re.sub(r"\s+", " ", plain).strip()
            if not plain or not HAS_LETTER.search(plain):
                return
            key = make_key(slug, el.name, plain)
            out_keys.append((key, plain))
            edits.append(("attr", el.open_start, el.open_end, key))
            return
        # Mixed content: wrap each loose text run in its own span.
        for (ts, te) in el.text_runs:
            raw = html[ts:te]
            plain = htmlmod.unescape(raw)
            plain = re.sub(r"\s+", " ", plain).strip()
            if not plain or not HAS_LETTER.search(plain):
                continue
            key = make_key(slug, "span", plain)
            out_keys.append((key, plain))
            # Wrap ONLY the trimmed text. The whitespace around it stays
            # outside the span, because the middleware replaces the span's
            # content with the dictionary value - and the dictionary value
            # is stripped. Wrapping the whitespace too would leave
            # <strong>Print on cardstock</strong><span>100 lb is ...</span>
            # with no space between them, in every language.
            lead = len(raw) - len(raw.lstrip())
            trail = len(raw.rstrip())
            edits.append(("wrap", ts + lead, ts + trail, key))

    visit(root)
    return edits


def apply_edits(html, edits):
    """Apply the edits from the end backwards so offsets stay valid."""
    edits = sorted(edits, key=lambda e: e[1], reverse=True)
    for kind, s, e, key in edits:
        if kind == "attr":
            tag = html[s:e]
            assert tag.endswith(">"), tag
            if tag.rstrip(">").rstrip().endswith("/"):
                raise SystemExit("[FAIL] self-closing tag cannot take data-i18n: %s" % tag)
            html = html[:e - 1] + ' data-i18n="%s"' % key + html[e - 1:]
        else:
            frag = html[s:e]
            html = html[:s] + '<span data-i18n="%s">%s</span>' % (key, frag) + html[e:]
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--page", default=None,
                    help="page to edit (default tools/<slug>/index.html)")
    ap.add_argument("--out", default=None,
                    help="where to write the key -> English text map")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    page = Path(args.page) if args.page else ROOT / "tools" / args.slug / "index.html"
    if not page.exists():
        raise SystemExit("[FAIL] no page at %s" % page)

    html = page.read_text(encoding="utf-8")

    m = re.search(r'<main\b[^>]*>', html)
    if not m:
        raise SystemExit("[FAIL] no <main> in %s" % page)
    # Find the matching </main> by counting <main ...> / </main>.
    depth = 0
    end = None
    for tok in tokenize(html, m.start(), len(html)):
        if tok[0] == "open" and tok[1] == "main":
            depth += 1
        elif tok[0] == "close" and tok[1] == "main":
            depth -= 1
            if depth == 0:
                end = tok[2]
                break
    if end is None:
        raise SystemExit("[FAIL] no closing </main> in %s" % page)

    root = parse_region(html, m.start(), end)
    keys = []
    edits = collect(root, html, args.slug, keys)

    # Same KEY -> one entry. Keep EVERY key.
    #
    # TRAP: this used to dedup by TEXT ("same text -> same key, keep the
    # first"). That silently dropped a whole set of keys: the same visible
    # string is often bound under two element types - a section heading
    # (`h2_text.what_to_put_on_a_wedding_invitation.c45a79e9`) and the
    # related-card link to it (`h4_text...c45a79e9`), a table cell
    # (`td_text.3_columns`) and a dropdown option (`option_text.3_columns`).
    # The hash is derived from the TEXT, so both keys share it, and the
    # text-dedup kept only one of them. The other one then had no key in
    # any dictionary and showed English in all ten languages.
    #
    # The thirteen existing tools keep BOTH keys in en.json - that is the
    # convention. And the translator already dedups by text on its own
    # (`all_texts`), so the same string is still translated only once.
    seen = {}
    unique = []
    for key, text in keys:
        if key in seen:
            continue
        seen[key] = text
        unique.append((key, text))

    out_html = apply_edits(html, edits)

    # The result must still parse as the same DOM shape.
    if out_html.count("<main") != html.count("<main"):
        raise SystemExit("[FAIL] the edit changed the number of <main> elements")

    if not args.dry_run:
        page.write_text(out_html, encoding="utf-8", newline="\n")

    out_path = Path(args.out) if args.out else ROOT / ".tmp" / ("%s-i18n-map.json" % args.slug)
    payload = {
        "slug": args.slug,
        "page": str(page.relative_to(ROOT)).replace("\\", "/"),
        "keys": {k: t for k, t in unique},
        "order": [k for k, _ in unique],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                        encoding="utf-8", newline="\n")

    print("bound %d elements, %d unique keys" % (len(edits), len(unique)))
    print("map: %s" % out_path.relative_to(ROOT))
    if args.dry_run:
        print("(dry run - page not written)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
