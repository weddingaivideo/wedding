#!/usr/bin/env python3
"""Idempotent repair of tools/index.html.

Three things, all narrow and all safe to re-run:

  1. Remove the duplicated ``<h2 <h2 ...`` / ``<p <p ...`` tag fragments
     left in the `cat-gen` header by an earlier injection pass.
  2. Replace the stale "13 tools" count with the real 32. Only the exact
     phrase `13 [free] tools` is touched -- key names such as
     `tools.h1.13_free_...` and unrelated numbers are left alone.
  3. Bind the whole `cat-planning` section (the 14 tools added in the free
     -tool demand audit) to data-i18n, so the middleware actually translates
     it. Without this the non-English `/<lang>/tools/` hub renders its lower
     half in English.

Emits `.tmp/hub-planning-keys.json` with the English source strings that the
translation step needs. The CTA keys are NOT in that file: every card's
"Try free" is bound to `tools.card.cta.try_free.NN` and the apply step copies
the already-translated `...01` value into each language, so no new CTA
translations are needed.
"""
import html
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HUB = ROOT / "tools" / "index.html"
OUT = ROOT / ".tmp" / "hub-planning-keys.json"
FIRST_CARD_NO = 19  # 01..18 are already used by the first four groups


def strip_tags(text):
    return html.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.replace(tmp, str(path))
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def main():
    src = HUB.read_text(encoding="utf-8")
    s = src

    # ---- 1. broken tag fragments -------------------------------------
    s, n_h2 = re.subn(r"<h2(?: <h2)+ (?=data-i18n)", "<h2 ", s)
    s, n_p = re.subn(r"<p(?: <p)+ (?=data-i18n)", "<p ", s)

    # ---- 2. stale tool count -----------------------------------------
    s, n_count = re.subn(r"\b13(?=\s+(?:free\s+)?tools\b)", "32", s, flags=re.I)

    # ---- 3. bind the planning section --------------------------------
    start = s.find('id="cat-planning"')
    if start < 0:
        sys.exit("cat-planning section not found")
    end = s.find("<section", start + 10)
    if end < 0:
        end = len(s)
    head, body, tail = s[:start], s[start:end], s[end:]

    keys = {}

    # section header: <h2> and the descriptive <p>
    hm = re.search(r"(<header class=\"section-header\">)(.*?)(</header>)", body, re.S)
    if not hm:
        sys.exit("section header not found")
    hdr = hm.group(2)
    h2m = re.search(r"<h2(\s[^>]*)?>(.*?)</h2>", hdr, re.S)
    if not h2m:
        sys.exit("section h2 not found")
    title = strip_tags(h2m.group(2))
    keys["tools.section.title.planning"] = title
    if "data-i18n" not in (h2m.group(1) or ""):
        hdr = hdr.replace(h2m.group(0), '<h2 data-i18n="tools.section.title.planning">%s</h2>' % h2m.group(2), 1)

    pm = re.search(r"<p(\s[^>]*)?>(.*?)</p>", hdr, re.S)
    if not pm:
        sys.exit("section desc not found")
    desc = strip_tags(pm.group(2))
    keys["tools.section.desc.planning"] = desc
    if "data-i18n" not in (pm.group(1) or ""):
        hdr = hdr.replace(pm.group(0), '<p data-i18n="tools.section.desc.planning">%s</p>' % pm.group(2), 1)

    body = body[:hm.start(2)] + hdr + body[hm.end(2):]

    # cards
    counter = [FIRST_CARD_NO - 1]

    def bind_card(m):
        counter[0] += 1
        n = counter[0]
        card = m.group(0)
        specs = [
            ("span", "tool-badge", "badge"),
            ("h3", "tool-name", "name"),
            ("p", "tool-tag", "tag"),
            ("span", "tool-cta", "cta"),
        ]
        # Always collect the English source, even on a second (idempotent)
        # run where the bindings are already present.
        for tag, cls, kind in specs:
            if kind == "cta":
                continue
            key = "tools.card.%s.planning.%02d" % (kind, n)
            km = re.search(r"<%s class=\"%s\"[^>]*>(.*?)</%s>" % (tag, cls, tag), card, re.S)
            if km:
                keys[key] = strip_tags(km.group(1))
        if "data-i18n" in card:
            return card
        for tag, cls, kind in specs:
            pat = re.compile(r"<%s class=\"%s\">" % (tag, cls))
            if kind == "cta":
                key = "tools.card.cta.try_free.%02d" % n
            else:
                key = "tools.card.%s.planning.%02d" % (kind, n)
            card = pat.sub('<%s class="%s" data-i18n="%s">' % (tag, cls, key), card, count=1)
        return card

    body = re.sub(r"<a class=\"tool-card\"[^>]*>.*?</a>", bind_card, body, flags=re.S)
    s = head + body + tail

    # ---- checks -------------------------------------------------------
    a, b = s.find('id="cat-planning"'), s.find("<section", s.find('id="cat-planning"') + 10)
    sec = s[a:b if b > 0 else len(s)]
    bound = {
        "h2": len(re.findall(r'data-i18n="tools\.section\.title\.planning"', sec)),
        "desc": len(re.findall(r'data-i18n="tools\.section\.desc\.planning"', sec)),
        "name": len(re.findall(r"<h3[^>]*data-i18n", sec)),
        "badge": len(re.findall(r'class="tool-badge"[^>]*data-i18n', sec)),
        "tag": len(re.findall(r'class="tool-tag"[^>]*data-i18n', sec)),
        "cta": len(re.findall(r'class="tool-cta"[^>]*data-i18n', sec)),
    }
    expected = {"h2": 1, "desc": 1, "name": 14, "badge": 14, "tag": 14, "cta": 14}
    if bound != expected:
        sys.exit("binding mismatch: %r != %r" % (bound, expected))
    if re.search(r"<h2 <h2|<p <p", s):
        sys.exit("broken tag fragments remain")
    if re.search(r"\b13\s+(?:free\s+)?tools\b", s, re.I):
        sys.exit("stale 13 tools remains")

    if s != src:
        atomic_write(HUB, s)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(keys, ensure_ascii=False, indent=2), encoding="utf-8")

    print("fixed tag fragments: h2=%d p=%d" % (n_h2, n_p))
    print("replaced stale tool counts: %d" % n_count)
    print("bound elements: %r" % bound)
    print("English source keys written: %d -> %s" % (len(keys), OUT))


if __name__ == "__main__":
    main()
