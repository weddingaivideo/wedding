"""Full pipeline test on multiple page types."""
import os
import json
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
exec((ROOT / "qa" / "test_middleware_regex.py").read_text(encoding="utf-8").split("# --- Tests ---")[0])

# Load all i18n dicts
i18n = {}
for lang in ["zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th"]:
    i18n[lang] = json.loads((ROOT / "i18n" / f"{lang}.json").read_text(encoding="utf-8"))


def run_pipeline(html, lang):
    out = html
    if lang != DEFAULT_LANG:
        out = out.replace('<html lang="en">', f'<html lang="{lang}"' + (' dir="rtl"' if lang == "ar" else "") + '>')
    out = setOgLocale(out, lang)
    out = rewriteInLanguage(out, lang)
    out = fixOgUrlTrailingSlash(out)
    out = addNoindexIfSuccess(out, "/test" if lang == DEFAULT_LANG else "/test")
    if lang != DEFAULT_LANG:
        out = applyDataI18n(out, i18n[lang])
        out = applyDataI18nAttr(out, i18n[lang])
    return out


pages = [
    ROOT / "index.html",
    ROOT / "about" / "index.html",
    ROOT / "blog" / "ai-wedding-video-generator-guide" / "index.html",
    ROOT / "services" / "personalization" / "pet-wedding" / "index.html",
    ROOT / "success" / "index.html",
    ROOT / "pricing" / "index.html",
]

for page in pages:
    if not page.exists():
        print(f"MISSING: {page.relative_to(ROOT)}")
        continue
    print(f"\n{'='*70}\n{page.relative_to(ROOT)}\n{'='*70}")
    html = page.read_text(encoding="utf-8")

    for lang in ["en", "zh", "ar"]:
        out = run_pipeline(html, lang)
        # Quick checks
        m_html = re.search(r'<html\s+lang="([^"]+)"', out)
        m_og = re.search(r'<meta\s+property="og:locale"\s+content="([^"]+)"', out)
        m_title = re.search(r'<title[^>]*>([^<]+)</title>', out)
        m_h1 = re.search(r'<h1[^>]*>([^<]+)</h1>', out)
        m_robots = re.search(r'<meta\s+name="robots"\s+content="([^"]+)"', out)

        print(f"\n  [{lang}]")
        print(f"    <html lang> = {m_html.group(1) if m_html else 'NOT FOUND'}")
        print(f"    og:locale = {m_og.group(1) if m_og else 'NOT FOUND'}")
        print(f"    robots = {m_robots.group(1) if m_robots else '(default)'}")
        print(f"    title = {m_title.group(1)[:70] if m_title else 'NOT FOUND'}")
        print(f"    h1 = {m_h1.group(1)[:70] if m_h1 else 'NOT FOUND'}")
