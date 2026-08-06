"""
Extract user-facing strings from all HTML files and generate i18n/en.json.

Strategy:
- Parse each HTML file with html.parser.
- For each <h1>..<h6>, <p>, <a>, <button>, <label>, <li>, <span>, <td>, <th>, <title>, <meta description>,
  <option>, <input placeholder>, capture the text content (and relevant attributes).
- Skip: scripts, styles, noindex, hidden, [data-no-i18n].
- Generate a key from the file path + tag + a short text hash.
- Write i18n/en.json with { "<key>": "<source text>" }.
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(".").resolve()
I18N_DIR = ROOT / "i18n"
I18N_DIR.mkdir(exist_ok=True)

# Tags whose innerText we want to translate
TAGS = {
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "a", "button", "label", "li", "span", "td", "th",
    "option", "strong", "em", "b", "i",
    "summary", "figcaption", "title",
    "small", "blockquote",
}
# Attributes whose value we want to translate
ATTRS = ("placeholder", "title", "alt", "aria-label")

SKIP_TAGS_PARENT = {"script", "style", "noscript", "svg", "code", "pre"}

# Find all HTML files (skip google-site-verification.html, admin pages, _redirects, _headers)
html_files = []
for p in sorted(ROOT.rglob("*.html")):
    rel = p.relative_to(ROOT).as_posix()
    if rel.startswith("admin/"):
        continue
    if p.name == "google-site-verification.html":
        continue
    if rel.startswith("scripts/") or rel.startswith("functions/"):
        continue
    if rel.startswith("node_modules/") or "/__pycache__/" in rel:
        continue
    html_files.append(p)

print(f"Scanning {len(html_files)} HTML files…", file=sys.stderr)

# We use a state machine. For each <tag> we either record an entry (text-only) or skip
# (text inside a non-translatable parent). We don't recurse into children of <a>/<button>
# if the text has no whitespace — we just want the leaf string.

entries = {}  # key -> {"text": str, "files": set(), "tag": str, "path": str}
key_index = {}  # text -> key (deduplicate identical strings across files)


def make_key(rel_path, tag, text):
    """Stable key from path + tag + text. Dedupe text across all files."""
    if text in key_index:
        return key_index[text]
    # Strip path noise: /services/personalization/slow-motion/ -> "services.personalization.slow-motion"
    base = rel_path.removesuffix("/index.html").removesuffix(".html")
    base = base.replace("/", ".").strip(".")
    # Use text snippet + first 8 chars of hash for uniqueness
    snippet = re.sub(r"[^a-z0-9]+", "_", text.lower())[:40].strip("_") or "x"
    h = abs(hash(text)) % (10**8)
    key = f"{base}.{tag}.{snippet}.{h:08d}"
    key_index[text] = key
    return key


class TextExtractor(HTMLParser):
    def __init__(self, rel_path):
        super().__init__(convert_charrefs=True)
        self.rel_path = rel_path
        self.skip_depth = 0  # how deep we are inside a skip tag
        self.text_depth = 0  # depth of current TAGS element
        self.cur_tag = None
        self.cur_attrs = {}
        self.cur_buf = []
        self.cur_skip_outer = False  # true if current TAGS element is inside a skip ancestor

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in SKIP_TAGS_PARENT:
            self.skip_depth += 1
            return
        if self.skip_depth > 0:
            return
        # Skip data-no-i18n
        if "data-no-i18n" in attrs.get("class", ""):
            self.cur_skip_outer = True
            return
        # Translate attributes standalone (placeholder, title, alt, aria-label)
        if tag in {"input", "textarea"}:
            for a in ATTRS:
                if a in attrs and attrs[a].strip():
                    self._record(tag, a, attrs[a])
            return
        if tag == "meta" and "name" in attrs and attrs["name"] == "description" and "content" in attrs:
            self._record("meta", "description", attrs["content"])
            return
        if tag in TAGS:
            self.cur_tag = tag
            self.cur_attrs = attrs
            self.cur_buf = []

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS_PARENT:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.cur_tag == tag:
            text = "".join(self.cur_buf).strip()
            if text and len(text) > 1 and not re.match(r"^[\W_]+$", text) and "<" not in text:
                self._record(tag, "text", text)
            self.cur_tag = None
            self.cur_attrs = {}
            self.cur_buf = []

    def handle_data(self, data):
        if self.skip_depth > 0:
            return
        if self.cur_skip_outer:
            return
        if self.cur_tag and data.strip():
            self.cur_buf.append(data)

    def handle_entityref(self, name):
        if self.cur_tag:
            self.cur_buf.append("&" + name + ";")

    def handle_charref(self, name):
        if self.cur_tag:
            self.cur_buf.append("&#" + name + ";")

    def _record(self, tag, kind, text):
        text = re.sub(r"\s+", " ", text).strip()
        if not text or len(text) < 2:
            return
        if re.match(r"^[\W_]+$", text):
            return
        if text.startswith("<!--"):
            return
        key = make_key(self.rel_path, tag + "_" + kind, text)
        if key not in entries:
            entries[key] = {"text": text, "tag": tag, "kind": kind, "path": self.rel_path}
        return key


total = 0
for path in html_files:
    rel = path.relative_to(ROOT).as_posix()
    parser = TextExtractor(rel)
    try:
        parser.feed(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  ! {rel}: {e}", file=sys.stderr)
    total += 1

# Build flat en.json: key -> text
en = {k: v["text"] for k, v in entries.items()}
out = I18N_DIR / "en.json"
out.write_text(json.dumps(en, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
print(f"Wrote {out} with {len(en)} unique strings from {total} files.", file=sys.stderr)
