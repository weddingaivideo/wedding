#!/usr/bin/env python3
"""
The reader view: what a reader in each language ACTUALLY sees.

WHY THIS GATE EXISTS
--------------------
Deploy 2 shipped the five new tools with all eleven dictionaries
complete - every key of the five tools' namespaces had a real translation
in all ten foreign languages. The reader-view counter said ONE English
sentence was left. It was really EIGHT static strings and SEVENTY-THREE
runtime strings, and a Russian reader met every one of them.

A dictionary audit cannot see either kind, because neither has a key:

* STATIC English - markup with no `data-i18n` at all. The middleware only
  rewrites an element that carries a binding, so the element keeps the
  English of the static file in every language.
* RUNTIME English - a string the page's own JavaScript writes after the
  response was sent. No server-side pass can ever reach it; it needs the
  `tools.copy` namespace, which the middleware hands to the client as
  `window.__WA_I18N__`.

So this gate measures the page the way the middleware renders it:

1. take the static language copy,
2. apply the same two transforms the middleware applies - `data-i18n`
   replaces the element's inner HTML, `data-i18n-attr` replaces the named
   attribute,
3. take the visible text out of <main>,
4. compare every text run with the English page's runs.

A run that is identical to the English source is English the reader sees.

WHO DECIDES THAT A RUN IS "THE SAME IN EVERY LANGUAGE"
-----------------------------------------------------
Not a hand-written white list: the site's own dictionary does. A run is
by design when the key that holds it has the SAME value in the target
language as in English - a measurement ("5 x 7 in"), a paper size
("A5"), a format name ("PDF"), a brand ("Canva"), a competitor's product
name. A key the site translated to something else, and the reader still
sees in English, is a real defect.

WHAT IS DELIBERATELY NOT A DEFECT
---------------------------------
* the form's placeholders ("e.g. Emma & Liam") and the menu sample in a
  textarea: they are examples the reader replaces, and all thirteen older
  tools keep them in English in all eleven dictionaries;
* a run with no letters at all ("1-3, 4, 5-"): a syntax sample;
* the site chrome (nav, footer, language switcher): it lives outside
  <main> and is the same on all 1201 pages.

WHAT IT MUST BE ABLE TO FAIL
----------------------------
A checker that always says "clean" proves nothing. The negative control
is `--inject`: it removes one binding and one runtime alias from every
dictionary, and the report MUST then name them.

Usage
-----
    python scripts/check-reader-view.py
    python scripts/check-reader-view.py --inject     # the reverse control
"""
import argparse
import importlib.util
import io
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The translation gate owns the question "is this value a translation of
# that source?". Two gates answering the same question must answer it the
# SAME way, so this gate reuses the gate's own rule instead of inventing
# a second one. (The house rule: when two gates answer the same question,
# the one that rejects more is usually wrong.)
_spec = importlib.util.spec_from_file_location(
    "ttp", str(ROOT / "scripts" / "translate-tool-page.py"))
ttp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ttp)

LANGS = ["zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
TOOLS = ["wedding-stationery-set-maker", "wedding-photo-contact-sheet",
         "wedding-pdf-editor", "wedding-photo-to-gif", "wedding-video-editor"]

# Tags whose text is NOT copy: the browser or the reader supplies it.
SKIP_TAGS = {"script", "style", "template", "svg", "noscript"}
# Tags whose text is an EXAMPLE or a SYNTAX SAMPLE, not a sentence.
SAMPLE_TAGS = {"textarea", "code", "pre", "kbd", "samp"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}

DATA_I18N = re.compile(
    r'<(\w+)\b[^>]*\bdata-i18n="([^"]+)"([^>]*)>([\s\S]*?)</\1>')
DATA_I18N_ATTR = re.compile(
    r'<([a-zA-Z][a-zA-Z0-9]*)([^>]*?\bdata-i18n-attr="([^"]+)"[^>]*)>')
TAG = re.compile(r"<(\w+)\b([^>]*)>")
T_CALL = re.compile(
    r"(?:window\.weddingAITool\.)?t\(\s*'([a-zA-Z0-9_]+)'\s*,\s*'((?:[^'\\]|\\.)*)'")
COPY_ENTRY = re.compile(
    r"^(\s{4})([a-zA-Z0-9_]+):\s*'tools\.copy\.([a-zA-Z0-9_]+)\.([a-z0-9]+)',\s*$",
    re.M)
LETTER = re.compile(r"[A-Za-z]")


def apply_data_i18n(html, dict_):
    """The middleware's applyDataI18n(), in Python."""
    def repl(m):
        tag, key = m.group(1), m.group(2)
        val = dict_.get(key)
        if val is None:
            return m.group(0)
        whole = m.group(0)
        clean = whole[:whole.index(">") + 1].replace(' data-i18n="%s"' % key, "")
        return clean + val + "</%s>" % tag
    return DATA_I18N.sub(repl, html)


def apply_data_i18n_attr(html, dict_):
    """The middleware's applyDataI18nAttr(), in Python."""
    def repl(m):
        tag, attrs, spec = m.group(1), m.group(2), m.group(3)
        new = attrs
        for pair in spec.split("|"):
            bits = pair.split(":")
            if len(bits) != 2:
                continue
            name, key = bits
            val = dict_.get(key)
            if val is None:
                continue
            rx = re.compile(r'\b%s="[^"]*"' % re.escape(name))
            new = rx.sub(
                lambda mm: '%s="%s"' % (name, val.replace('"', "&quot;")),
                new, count=1)
        new = re.sub(r'\s*data-i18n-attr="[^"]*"', "", new)
        return "<%s%s>" % (tag, new)
    return DATA_I18N_ATTR.sub(repl, html)


def visible_runs(html):
    """The text runs a reader sees inside <main>."""
    m = re.search(r"<main\b[^>]*>", html)
    if not m:
        return []
    end = html.find("</main>", m.end())
    body = html[m.end():end if end > 0 else len(html)]
    for tag in SKIP_TAGS:
        body = re.sub(r"<%s\b[\s\S]*?</%s>" % (tag, tag), " ", body)
    runs = []
    for tm in TAG.finditer(body):
        tag = tm.group(1).lower()
        if tag in VOID or tm.group(2).rstrip().endswith("/"):
            continue
        if tag in SAMPLE_TAGS:
            continue
        nxt = body.find("<", tm.end())
        if nxt < 0:
            nxt = len(body)
        chunk = body[tm.end():nxt]
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", chunk)).strip()
        if text:
            runs.append((tag, text))
    return runs


def norm(text):
    return " ".join(text.split()).strip()


def acceptable_as_translation(source, value, lang):
    """Would the translation gate accept this value as a translation?

    A runtime copy value can legitimately be byte-identical to the
    English: French says "pages", "page", "menu" and "table" exactly the
    way English does, and a format name ("PDF") reads the same in every
    language. That is not an untranslated leftover.

    The rule is the gate's own:
      * a source with no word a translation could change (a measurement, a
        format name, a brand) is its own translation;
      * for a Latin-script target, a value with no ENGLISH-ONLY word is
        accepted - "pages" is a French word, "none" is an English one;
      * for any other target the value has to be written in that
        language's script, so an English value is a defect.
    """
    if ttp.script_independent(source):
        return True
    if lang in ("es", "fr", "de", "pt"):
        return not ttp.foreign_spans(value, lang)
    return ttp.script_ok(value, lang)


def load_dicts():
    dicts = {}
    for lang in ["en"] + LANGS:
        path = ROOT / "i18n" / ("%s.json" % lang)
        with io.open(path, encoding="utf-8") as fh:
            dicts[lang] = json.load(fh)
    return dicts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inject", action="store_true",
                    help="negative control: break one binding and one alias")
    args = ap.parse_args()

    dicts = load_dicts()

    common = io.open(ROOT / "js" / "tools" / "common.js", encoding="utf-8").read()
    copy_keys = {}
    for m in COPY_ENTRY.finditer(common):
        copy_keys[m.group(2)] = "tools.copy.%s.%s" % (m.group(3), m.group(4))

    problems = []
    total_visible = 0

    for slug in TOOLS:
        en_path = ROOT / "tools" / slug / "index.html"
        if not en_path.exists():
            problems.append("%s: no English page" % slug)
            continue
        en_html = io.open(en_path, encoding="utf-8").read()
        en_runs = set(norm(t) for _, t in visible_runs(en_html))

        # The site's own decision: for every key of this tool's namespace,
        # does the target language hold the same value as English? That is
        # what "the same in every language" means here.
        by_design = {}
        for key, en_val in dicts["en"].items():
            if not key.startswith("tools.%s." % slug):
                continue
            if not isinstance(en_val, str) or not norm(en_val):
                continue
            for lang in LANGS:
                if norm(dicts[lang].get(key, "")) == norm(en_val):
                    by_design.setdefault(lang, set()).add(norm(en_val))

        if args.inject:
            # The victim must be a string the site really TRANSLATED. A
            # binding whose value is the same in every language (a
            # measurement, a brand) would be excused by the by-design rule,
            # and the control would then report nothing - a control that
            # reports nothing is not a control.
            victim = None
            for m in re.finditer(
                    r'data-i18n="(tools\.%s\.[^"]+)"' % re.escape(slug), en_html):
                key = m.group(1)
                en_val = dicts["en"].get(key)
                if not isinstance(en_val, str) or not norm(en_val):
                    continue
                if norm(en_val) in by_design.get(LANGS[0], set()):
                    continue
                if all(norm(dicts[lang].get(key, "")) == norm(en_val)
                       for lang in LANGS):
                    continue      # the same in every language: not a defect
                victim = key
                break
            if victim:
                for lang in LANGS:
                    dicts[lang].pop(victim, None)
                print("[control] removed the binding %s from every language"
                      % victim)
            alias = None
            for m in T_CALL.finditer(en_html):
                fallback = m.group(2).replace("\\'", "'")
                if len(re.findall(r"[A-Za-z]{2,}", fallback)) < 2:
                    continue      # "PDF" is not a sentence
                alias = m.group(1)
                break
            if alias:
                for lang in LANGS:
                    dicts[lang].pop(copy_keys.get(alias, "x"), None)
                print("[control] removed the runtime alias %s from every language"
                      % alias)

        for lang in LANGS:
            path = ROOT / lang / "tools" / slug / "index.html"
            if not path.exists():
                problems.append("%s %s: no language copy" % (lang, slug))
                continue
            html = io.open(path, encoding="utf-8").read()
            rendered = apply_data_i18n_attr(
                apply_data_i18n(html, dicts[lang]), dicts[lang])
            runs = visible_runs(rendered)
            total_visible += len(runs)
            design = by_design.get(lang, set())
            for tag, text in runs:
                n = norm(text)
                if len(n) < 3 or n not in en_runs:
                    continue
                if n in design:
                    continue              # the site keeps this in every language
                if not LETTER.search(n):
                    continue              # numbers and symbols
                problems.append("%s %s: <%s> %s" % (lang, slug, tag, n[:90]))

            # the runtime strings
            for m in T_CALL.finditer(html):
                alias = m.group(1)
                fallback = m.group(2).replace("\\'", "'")
                key = copy_keys.get(alias)
                if not key:
                    problems.append("%s %s: the alias %s is not in the COPY table"
                                    % (lang, slug, alias))
                    continue
                val = dicts[lang].get(key)
                if val is None:
                    problems.append("%s %s: the alias %s has no value in the "
                                    "dictionary" % (lang, slug, alias))
                elif norm(val) == norm(fallback) and not acceptable_as_translation(
                        fallback, val, lang):
                    problems.append("%s %s: the alias %s is still English: %s"
                                    % (lang, slug, alias, fallback[:70]))

    print("")
    print("=" * 74)
    print("the reader view: %d visible text run(s) over %d tools x %d languages"
          % (total_visible, len(TOOLS), len(LANGS)))
    print("=" * 74)
    if not problems:
        print("CLEAN: no English text reaches a reader in any of the ten languages.")
        return 0
    print("%d problem(s):" % len(problems))
    for p in problems[:80]:
        print("   " + p)
    if len(problems) > 80:
        print("   ... and %d more" % (len(problems) - 80))
    print("")
    print("A static string needs a data-i18n binding; a runtime string needs")
    print("t('alias', 'fallback') plus a tools.copy value in every language.")
    print("Do not truncate a machine translation - translate it properly.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
