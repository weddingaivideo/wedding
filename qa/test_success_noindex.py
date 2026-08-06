"""Test that /success/ gets noindex correctly in EN and all languages."""
import os
import json
import re
from pathlib import Path

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
exec((ROOT / "qa" / "test_middleware_regex.py").read_text(encoding="utf-8").split("# --- Tests ---")[0])
i18n = {}
for lang in ["zh", "ar", "es"]:
    i18n[lang] = json.loads((ROOT / "i18n" / f"{lang}.json").read_text(encoding="utf-8"))

success = (ROOT / "success" / "index.html").read_text(encoding="utf-8")

# Simulate the lang prefix scenarios
for prefix, lang in [("", "en"), ("/zh", "zh"), ("/ar", "ar"), ("/es", "es")]:
    rest = "/success"
    out = success
    if lang != DEFAULT_LANG:
        out = out.replace('<html lang="en">', f'<html lang="{lang}"' + (' dir="rtl"' if lang == "ar" else "") + '>')
    out = setOgLocale(out, lang)
    out = rewriteInLanguage(out, lang)
    out = fixOgUrlTrailingSlash(out)
    out = addNoindexIfSuccess(out, rest)
    if lang != DEFAULT_LANG:
        out = applyDataI18n(out, i18n[lang])
        out = applyDataI18nAttr(out, i18n[lang])

    m = re.search(r'<meta\s+name="robots"\s+content="([^"]+)"', out)
    print(f"  {prefix or '(no prefix)'}{rest} → robots: {m.group(1) if m else 'NOT FOUND (FAIL)'}")
