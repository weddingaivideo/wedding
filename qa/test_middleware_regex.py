"""Test the middleware regex transformations in isolation.
Simulate what the middleware does, then verify the output."""
import os
import json
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
sys.path.insert(0, str(ROOT / "functions" / "_lib"))


# Import the language tables
import importlib.util
spec = importlib.util.spec_from_file_location("langs", ROOT / "functions" / "_lib" / "langs.js")
# langs.js is ESM, can't import directly. Read & eval.
src = (ROOT / "functions" / "_lib" / "langs.js").read_text(encoding="utf-8")
# Just hardcode the values for the test
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th"]
DEFAULT_LANG = "en"
RTL = {"ar": True}

LANG_TO_OG_LOCALE = {
    "en": "en_US", "zh": "zh_CN", "es": "es_ES", "fr": "fr_FR", "de": "de_DE",
    "pt": "pt_BR", "ja": "ja_JP", "ru": "ru_RU", "ar": "ar_SA", "th": "th_TH",
}
LANG_TO_INLANGUAGE = {k: v.replace("_", "-") for k, v in LANG_TO_OG_LOCALE.items()}


def applyDataI18n(html, dict):
    data_i18n_re = re.compile(r'\s*data-i18n="[^"]*"')
    def repl(m):
        tag, attrs, key, inner = m.group(1), m.group(2), m.group(3), m.group(4)
        v = dict.get(key, inner)
        new_attrs = data_i18n_re.sub("", attrs)
        return f'<{tag}{new_attrs}>{v}</{tag}>'
    return re.sub(
        r'<([a-zA-Z][a-zA-Z0-9]*)\b([^>]*\bdata-i18n="([^"]+)"[^>]*)>([\s\S]*?)<\/\1>',
        repl, html,
    )


def applyDataI18nAttr(html, dict):
    def repl(m):
        tag, attrs, spec = m.group(1), m.group(2), m.group(3)
        new_attrs = attrs
        for pair in spec.split("|"):
            parts = pair.split(":")
            if len(parts) != 2: continue
            attr_name, key = parts
            v = dict.get(key)
            if v is None: continue
            new_attrs = re.sub(rf'\b{attr_name}="[^"]*"', f'{attr_name}="{v.replace(chr(34), "&quot;")}"', new_attrs)
        new_attrs = re.sub(r'\s*data-i18n-attr="[^"]*"', "", new_attrs)
        return f'<{tag}{new_attrs}>'
    return re.sub(
        r'<([a-zA-Z][a-zA-Z0-9]*)([^>]*?\bdata-i18n-attr="([^"]+)"[^>]*)>',
        repl, html,
    )


def setOgLocale(html, lang):
    locale = LANG_TO_OG_LOCALE.get(lang, LANG_TO_OG_LOCALE[DEFAULT_LANG])
    if re.search(r'<meta\s+property="og:locale"\s+content="[^"]*"\s*>', html, re.I):
        return re.sub(
            r'<meta\s+property="og:locale"\s+content="[^"]*"\s*>',
            f'<meta property="og:locale" content="{locale}">',
            html, flags=re.I,
        )
    return re.sub(
        r'(<meta\s+property="og:url"\s+content="[^"]*"\s*>)',
        rf'\1\n    <meta property="og:locale" content="{locale}">',
        html, flags=re.I,
    )


def rewriteInLanguage(html, lang):
    target = LANG_TO_INLANGUAGE.get(lang, LANG_TO_INLANGUAGE[DEFAULT_LANG])

    def repl(m):
        body = m.group(1)
        try:
            obj = json.loads(body)
        except Exception:
            return m.group(0)
        changed = False

        def visit(node):
            nonlocal changed
            if not isinstance(node, dict): return
            if isinstance(node.get("inLanguage"), str):
                if re.match(r"^en(-[A-Z]{2})?$", node["inLanguage"]) and lang != DEFAULT_LANG:
                    node["inLanguage"] = target
                    changed = True
            for v in node.values():
                visit(v)

        visit(obj)
        if not changed: return m.group(0)
        return m.group(0).replace(body, json.dumps(obj, separators=(",", ":")))

    return re.sub(
        r'<script\s+type="application/ld\+json"[^>]*>([\s\S]*?)</script>',
        repl, html, flags=re.I,
    )


def fixOgUrlTrailingSlash(html):
    return re.sub(
        r'<meta\s+property="og:url"\s+content="(https://weddingai\.video/[^"#?]*[^/])"\s*>',
        lambda m: f'<meta property="og:url" content="{m.group(1)}/">' if "?" not in m.group(1) and "#" not in m.group(1) else m.group(0),
        html,
    )


def addNoindexIfSuccess(html, rest):
    rest_norm = rest.rstrip("/")
    if rest_norm != "/success":
        return html
    if re.search(r'<meta\s+name="robots"\s+content="noindex', html, re.I):
        return html
    if re.search(r'<title>[\s\S]*?</title>', html, re.I):
        return re.sub(r'(</title>)', r'\1\n    <meta name="robots" content="noindex, follow">', html, count=1, flags=re.I)
    return re.sub(r'(<meta\s+charset="?[^>]*>?)', r'\1\n    <meta name="robots" content="noindex, follow">', html, count=1, flags=re.I)


# --- Tests ---
print("===== Test 1: applyDataI18n (leaf element) =====")
src = '<h1 data-i18n="hello.key" class="x">Hello World</h1>'
zh = {"hello.key": "你好世界"}
out = applyDataI18n(src, zh)
expected = '<h1 class="x">你好世界</h1>'
print(f"  input:  {src}")
print(f"  output: {out}")
print(f"  expected: {expected}")
print(f"  PASS" if out == expected else f"  FAIL")
print()

print("===== Test 2: applyDataI18n (with nested tag) =====")
src = '<p data-i18n="nested.key">Hello <a href="/x">link</a> world</p>'
zh = {"nested.key": "你好世界"}
out = applyDataI18n(src, zh)
expected = '<p>你好世界</p>'
print(f"  input:  {src}")
print(f"  output: {out}")
print(f"  expected: {expected}")
print(f"  PASS" if out == expected else f"  FAIL")
print()

print("===== Test 3: applyDataI18n (missing key) =====")
src = '<h1 data-i18n="missing.key">Original</h1>'
zh = {"other.key": "其他"}
out = applyDataI18n(src, zh)
expected = '<h1>Original</h1>'
print(f"  input:  {src}")
print(f"  output: {out}")
print(f"  expected: {expected}")
print(f"  PASS" if out == expected else f"  FAIL")
print()

print("===== Test 4: applyDataI18nAttr =====")
src = '<meta name="description" data-i18n-attr="content:desc.key" content="old desc" />'
zh = {"desc.key": "新描述"}
out = applyDataI18nAttr(src, zh)
expected = '<meta name="description" content="新描述" />'
print(f"  input:  {src}")
print(f"  output: {out}")
print(f"  expected: {expected}")
print(f"  PASS" if out == expected else f"  FAIL")
print()

print("===== Test 5: setOgLocale (existing tag) =====")
src = '<meta property="og:locale" content="en_US">'
out = setOgLocale(src, "zh")
expected = '<meta property="og:locale" content="zh_CN">'
print(f"  PASS" if out == expected else f"  FAIL: {out}")
print()

print("===== Test 6: rewriteInLanguage =====")
src = '<script type="application/ld+json">{"@context":"https://schema.org","@type":"Article","inLanguage":"en-US","headline":"x"}</script>'
out = rewriteInLanguage(src, "zh")
expected_in_language = '"inLanguage":"zh-CN"'
print(f"  input:  {src}")
print(f"  output: {out}")
print(f"  contains 'inLanguage:zh-CN': {expected_in_language in out}")
print(f"  PASS" if expected_in_language in out else f"  FAIL")
print()

print("===== Test 7: fixOgUrlTrailingSlash =====")
src = '<meta property="og:url" content="https://weddingai.video/about">'
out = fixOgUrlTrailingSlash(src)
expected = '<meta property="og:url" content="https://weddingai.video/about/">'
print(f"  PASS" if out == expected else f"  FAIL: {out}")
src2 = '<meta property="og:url" content="https://weddingai.video/about/">'
out2 = fixOgUrlTrailingSlash(src2)
print(f"  Already has slash: {'PASS' if out2 == src2 else f'FAIL: {out2}'}")
print()

print("===== Test 8: addNoindexIfSuccess =====")
src = "<html><head><title>x</title></head><body></body></html>"
out = addNoindexIfSuccess(src, "/success")
expected_marker = '<meta name="robots" content="noindex, follow">'
print(f"  /success/ → has noindex: {expected_marker in out}")
print(f"  PASS" if expected_marker in out else f"  FAIL: {out}")
src2 = addNoindexIfSuccess(src, "/about")
print(f"  /about/ → no change: {'PASS' if src2 == src else f'FAIL: {src2}'}")
print()

print("===== Test 9: Real page (index.html) — full middleware pipeline =====")
index = (ROOT / "index.html").read_text(encoding="utf-8")
zh_dict = json.loads((ROOT / "i18n" / "zh.json").read_text(encoding="utf-8"))

# Simulate the pipeline
out = index
out = setOgLocale(out, "zh")
out = rewriteInLanguage(out, "zh")
out = fixOgUrlTrailingSlash(out)
out = applyDataI18n(out, zh_dict)
out = applyDataI18nAttr(out, zh_dict)

# Check: og:locale
m = re.search(r'<meta\s+property="og:locale"\s+content="([^"]+)"', out)
print(f"  og:locale = {m.group(1) if m else 'NOT FOUND'} (expected zh_CN)")

# Check: <h1> Make Every Wedding Moment Unforgettable
m = re.search(r'<h1[^>]*>([^<]+)</h1>', out)
print(f"  <h1> = {m.group(1) if m else 'NOT FOUND'}")
print(f"  <h1> changed from English? {'PASS' if m and 'Make Every' not in m.group(1) else 'FAIL'}")

# Check: title
m = re.search(r'<title[^>]*>([^<]+)</title>', out)
print(f"  <title> = {m.group(1) if m else 'NOT FOUND'}")
# Title in en.json is "AI-Powered Wedding Video Services | WeddingAI.video"
# Title in zh.json should be different
zh_title = zh_dict.get("index.title_text.ai_powered_wedding_video_services_weddin.58583865", "(not in dict)")
print(f"  zh dict title: {zh_title}")
print(f"  <title> matches zh: {'PASS' if m and m.group(1) == zh_title else 'FAIL'}")
