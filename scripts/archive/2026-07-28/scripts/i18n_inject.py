"""
Inject data-i18n placeholders into all HTML files, plus the <script> tag for
js/i18n.js, plus the language-switcher markup in the header.

Idempotent: elements that already have data-i18n are left alone.
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(".").resolve()
I18N_DIR = ROOT / "i18n"
EN_FILE = I18N_DIR / "en.json"

TAGS = {
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "a", "button", "label", "li", "span", "td", "th",
    "option", "strong", "em", "b", "i",
    "summary", "figcaption", "title",
    "small", "blockquote",
}
ATTRS = ("placeholder", "title", "alt", "aria-label")
SKIP_TAGS_PARENT = {"script", "style", "noscript", "svg", "code", "pre"}

en = json.loads(EN_FILE.read_text(encoding="utf-8"))
text_to_key = {text: key for key, text in en.items()}
SKIP_RE = re.compile(r"^[\W_0-9]+$|^\s*$")


def maybe_translate(text):
    t = re.sub(r"\s+", " ", text).strip()
    if not t or len(t) < 2 or SKIP_RE.match(t):
        return None
    return text_to_key.get(t)


class Injector(HTMLParser):
    """Walk HTML, rewrite text nodes whose inner text matches en.json."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip_depth = 0
        self.cur_tag = None
        self.cur_open_html = None  # exact original start tag string
        self.cur_buf = []
        self.skip_outer = False

    def handle_starttag(self, tag, attrs):
        attrs_d = dict(attrs)
        if tag in SKIP_TAGS_PARENT:
            self.skip_depth += 1
            self.out.append(self.get_starttag_text() or f"<{tag}>")
            return
        if self.skip_depth > 0:
            self.out.append(self.get_starttag_text() or f"<{tag}>")
            return
        if "data-no-i18n" in attrs_d.get("class", ""):
            self.skip_outer = True
            self.out.append(self.get_starttag_text() or f"<{tag}>")
            return
        if tag in TAGS:
            self.cur_tag = tag
            self.cur_open_html = self.get_starttag_text() or f"<{tag}>"
            self.cur_buf = []
            return
        if tag in {"input", "textarea"}:
            new_attrs = list(attrs)
            existing = ""
            for k, v in attrs:
                if k == "data-i18n-attr" and v:
                    existing = v
            for a in ATTRS:
                val = attrs_d.get(a)
                if val and val.strip():
                    key = maybe_translate(val)
                    if key:
                        existing = (existing + "|" + f"{a}:{key}").lstrip("|")
            if existing:
                # Rebuild tag with updated data-i18n-attr
                rebuilt = "<" + tag
                for k, v in attrs:
                    if k == "data-i18n-attr":
                        continue
                    rebuilt += f' {k}="{v}"'
                rebuilt += f' data-i18n-attr="{existing}"'
                if tag in {"input"}:
                    rebuilt += " />"
                else:
                    rebuilt += ">"
                self.out.append(rebuilt)
            else:
                self.out.append(self.get_starttag_text() or f"<{tag}>")
            return
        if tag == "meta" and attrs_d.get("name") == "description" and "content" in attrs_d:
            key = maybe_translate(attrs_d["content"])
            if key:
                rebuilt = f'<meta name="description" data-i18n-attr="content:{key}" content="{attrs_d["content"]}" />'
                self.out.append(rebuilt)
                return
        self.out.append(self.get_starttag_text() or f"<{tag}>")

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS_PARENT:
            self.skip_depth = max(0, self.skip_depth - 1)
            self.out.append(f"</{tag}>")
            return
        if self.skip_outer and self.cur_tag is None:
            self.skip_outer = False
            self.out.append(f"</{tag}>")
            return
        if self.cur_tag == tag:
            text = "".join(self.cur_buf).strip()
            key = None
            if text and "data-i18n" not in (self.cur_open_html or ""):
                key = maybe_translate(text)
            if key:
                # Inject data-i18n into the original open tag
                open_html = self.cur_open_html
                # Handle self-closing form <tag ... /> -> <tag ... data-i18n="..." />
                if open_html.endswith("/>"):
                    new_open = open_html[:-2].rstrip() + f' data-i18n="{key}" />'
                else:
                    new_open = open_html[:-1].rstrip() + f' data-i18n="{key}">'
                self.out.append(new_open)
                # Emit the raw text (unescaped isn't strictly correct for HTML, but
                # the source already had the text rendered as-is, so trust it).
                # We re-emit by NOT escaping — the original would have had it in there
                # already. To be safe, use the raw text we collected.
                self.out.append(text)
            else:
                # Emit original open + collected text + close
                self.out.append(self.cur_open_html)
                self.out.append("".join(self.cur_buf))
            self.out.append(f"</{tag}>")
            self.cur_tag = None
            self.cur_open_html = None
            self.cur_buf = []
            return
        self.out.append(f"</{tag}>")

    def handle_startendtag(self, tag, attrs):
        self.out.append(self.get_starttag_text() or f"<{tag} />")

    def handle_data(self, data):
        if self.skip_depth > 0:
            self.out.append(data)
            return
        if self.skip_outer:
            self.out.append(data)
            return
        if self.cur_tag:
            self.cur_buf.append(data)
        else:
            self.out.append(data)

    def handle_entityref(self, name):
        if self.cur_tag:
            self.cur_buf.append("&" + name + ";")
        else:
            self.out.append("&" + name + ";")

    def handle_charref(self, name):
        if self.cur_tag:
            self.cur_buf.append("&#" + name + ";")
        else:
            self.out.append("&#" + name + ";")

    def handle_comment(self, data):
        self.out.append("<!--" + data + "-->")

    def handle_decl(self, decl):
        self.out.append("<!" + decl + ">")

    def handle_pi(self, data):
        self.out.append("<?" + data + ">")


SCRIPT_TAG = '<script src="js/i18n.js?v=3.19" defer></script>'
LANG_OPTIONS = [
    ("en", "EN"), ("zh", "中文"), ("es", "ES"), ("fr", "FR"), ("de", "DE"),
    ("pt", "PT"), ("ja", "JA"), ("ru", "RU"), ("ar", "AR"), ("th", "TH"),
]
LANG_SELECT_HTML = (
    '<li class="wa-lang-switcher" data-no-i18n>'
    '<select id="wa-lang-select" aria-label="Language">'
    + "".join(f'<option value="{c}">{label}</option>' for c, label in LANG_OPTIONS)
    + "</select></li>"
)


def inject_script_tag(html):
    if "js/i18n.js" in html:
        return html
    return html.replace("</head>", SCRIPT_TAG + "\n</head>", 1)


def inject_lang_switcher(html):
    if 'id="wa-lang-select"' in html:
        return html
    m = re.search(r'(<ul class="nav-list">)', html)
    if not m:
        return html
    end = html.find("</ul>", m.end())
    if end == -1:
        return html
    return html[:end] + LANG_SELECT_HTML + html[end:]


def process_file(path):
    rel = path.relative_to(ROOT).as_posix()
    if rel.startswith("admin/"):
        return False
    if path.name == "google-site-verification.html":
        return False
    text = path.read_text(encoding="utf-8")
    parser = Injector()
    try:
        parser.feed(text)
        parser.close()
    except Exception as e:
        print(f"  ! parse error in {rel}: {e}", file=sys.stderr)
        return False
    new_text = "".join(parser.out)
    new_text = inject_script_tag(new_text)
    new_text = inject_lang_switcher(new_text)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    files = []
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith("admin/"):
            continue
        if p.name == "google-site-verification.html":
            continue
        if only and only not in rel:
            continue
        files.append(p)
    print(f"Processing {len(files)} HTML files (filter={only or 'all'})…", file=sys.stderr)
    changed = 0
    for f in files:
        if process_file(f):
            changed += 1
    print(f"Modified {changed} files.", file=sys.stderr)


if __name__ == "__main__":
    main()
