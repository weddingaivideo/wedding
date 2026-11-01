#!/usr/bin/env python3
"""Fix the broken trust-line binding and the half-applied trust unification.

Three defects, one root area:

1. BROKEN BINDING (the one the audit found as a residual "500"):
   index.html binds
       index.p_text.trusted_by_9400_couples_in_11_languages.32124339
   but ALL 11 dictionaries only hold
       index.p_text.trusted_by_500_couples_in_the_us_europe.32124339
   The rename happened in commit 5127bc3a ("unify couples number to 9,400+"),
   which changed index.html and forgot the dictionaries. The later trust pass
   (5720fbcc) put the VALUE back to "500+" but left the KEY NAME alone, so
   the value and the key now disagree AND the binding is dead: every
   localized homepage renders this line in English.

   Fix: point index.html at the key the dictionaries actually hold. The
   dictionary key has existed under that name since the initial commit
   (a6d438d2), so no dictionary needs renaming and no hash churn is needed.

2. HALF-APPLIED TRUST UNIFICATION:
   commit 5720fbcc replaced "4.9/5 from 6 verified reviews" with "Top-rated
   4.9/5" in en, ru and hi only. The other 8 dictionaries still say "6
   reviews", which contradicts the site's own "500+ customer reviews" claim
   on the very same homepage. Once the binding is fixed those 8 values
   become visible, so they have to be corrected in the same pass.

3. NEW KEY for the footer badge title attribute:
   the site-wide footer badge carries title="500+ couples served, 4.9/5
   rating" on 720 pages, and that attribute was never bound to the
   dictionary, so it stays English on every localized page. This script
   adds the key to all 11 dictionaries; scripts/fix-footer-badge-title-i18n.py
   binds it in the HTML.

Run from the repo root:  python scripts/fix-trust-key-binding.py [--apply]
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

LANGS = ["en", "de", "es", "fr", "pt", "ja", "ru", "ar", "th", "hi", "zh"]

BROKEN_KEY = "index.p_text.trusted_by_9400_couples_in_11_languages.32124339"
LIVE_KEY = "index.p_text.trusted_by_500_couples_in_the_us_europe.32124339"

NEW_TITLE_KEY = "about.a_text.couples_served_title.ddddddd3"
AFTER_KEY = "about.a_text.couples_served.ddddddd1"

# The trust line, "Top-rated" form. en/ru/hi already carry it; the other
# eight still carried the old "6 verified reviews" wording.
TRUST_LINE = {
    "en": "Trusted by 500+ couples · Top-rated 4.9/5 · 48h turnaround",
    "de": "Vertrauen von mehr als 500 Paaren · Top-bewertet mit 4,9/5 · 48-h-Lieferung",
    "es": "Más de 500 parejas confían en nosotros · Con 4.9/5 de valoración · Entrega en 48 h",
    "fr": "Plus de 500 couples nous font confiance · 4,9/5 de note · Livraison en 48 h",
    "pt": "Mais de 500 casais confiam em nós · 4,9/5 de avaliação · Entrega em 48 h",
    "ja": "500 組以上のカップルが信頼 · 4.9/5 の高評価 · 48 時間納品",
    "ru": "Нам доверяют более 500 пар · Высшая оценка 4,9 из 5 · Срок выполнения 48 часов",
    "ar": "يثق بنا أكثر من 500 زوج · تقييم 4.9/5 من الأعلى · التسليم خلال 48 ساعة",
    "th": "คู่รักกว่า 500 คู่ไว้วางใจ · คะแนน 4.9/5 ระดับสูงสุด · ส่งงานภายใน 48 ชม.",
    "hi": "500+ जोड़ों द्वारा विश्वसनीय · शीर्ष रेटेड 4.9/5 · 48 घंटे का टर्नअराउंड",
    "zh": "500+ 对夫妇信赖 · 4.9/5 最高评分 · 48 小时交付",
}

# The footer badge tooltip (the title attribute of the trust badge).
FOOTER_TITLE = {
    "en": "500+ couples served, 4.9/5 rating",
    "de": "Mehr als 500 Paare betreut, 4,9/5 Bewertung",
    "es": "Más de 500 parejas atendidas, 4.9/5 de valoración",
    "fr": "Plus de 500 couples accompagnés, note 4,9/5",
    "pt": "Mais de 500 casais atendidos, avaliação 4,9/5",
    "ja": "500組以上のお客様に対応、4.9/5 の評価",
    "ru": "Обслужено более 500 пар, рейтинг 4,9/5",
    "ar": "تم خدمة أكثر من 500 زوج، تقييم 4.9/5",
    "th": "ให้บริการคู่รักมากกว่า 500 คู่ คะแนน 4.9/5",
    "hi": "500+ जोड़ों को सेवा दी गई, 4.9/5 रेटिंग",
    "zh": "已服务 500+ 对新人，4.9/5 评分",
}


def dump_json(path, data):
    """Write the dictionary exactly the way the repo already stores it:
    UTF-8 without BOM, LF line endings, 2-space indent, ensure_ascii=False."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


def patch_dict(lang):
    path = os.path.join("i18n", f"{lang}.json")
    with open(path, encoding="utf-8") as fh:
        original = fh.read()
    data = json.loads(original)

    changes = []

    # --- 2. trust line -------------------------------------------------
    if LIVE_KEY not in data:
        raise SystemExit(f"{path}: {LIVE_KEY} is missing - cannot patch")
    if data[LIVE_KEY] != TRUST_LINE[lang]:
        changes.append(("trust-line", data[LIVE_KEY], TRUST_LINE[lang]))
        data[LIVE_KEY] = TRUST_LINE[lang]

    # --- 3. new footer-title key ---------------------------------------
    if NEW_TITLE_KEY in data:
        if data[NEW_TITLE_KEY] != FOOTER_TITLE[lang]:
            changes.append(("footer-title", data[NEW_TITLE_KEY], FOOTER_TITLE[lang]))
            data[NEW_TITLE_KEY] = FOOTER_TITLE[lang]
    else:
        if AFTER_KEY not in data:
            raise SystemExit(f"{path}: anchor key {AFTER_KEY} is missing")
        rebuilt = {}
        for k, v in data.items():
            rebuilt[k] = v
            if k == AFTER_KEY:
                rebuilt[NEW_TITLE_KEY] = FOOTER_TITLE[lang]
        data = rebuilt
        changes.append(("footer-title+", "(absent)", FOOTER_TITLE[lang]))

    # Round-trip check: the dump must be byte-identical to the input when
    # nothing changed, otherwise the file's formatting would drift on every
    # run of this script.
    candidate = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if not changes:
        if candidate != original:
            raise SystemExit(
                f"{path}: reformatting detected - refusing to write.\n"
                "  The stored JSON format differs from json.dump(indent=2); "
                "adjust dump_json() before touching this file.")
        return changes

    dump_json(path, data)
    return changes


def patch_index_html():
    path = "index.html"
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if BROKEN_KEY not in text:
        if LIVE_KEY in text:
            print("  index.html: already bound to the live key - nothing to do")
            return []
        raise SystemExit("index.html: neither the broken nor the live key is present")
    count = text.count(BROKEN_KEY)
    text = text.replace(BROKEN_KEY, LIVE_KEY)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    os.replace(tmp, path)
    return [("index.html", BROKEN_KEY, LIVE_KEY, count)]


def main():
    apply = "--apply" in sys.argv
    print("=== fix-trust-key-binding ===")
    print(f"mode: {'APPLY' if apply else 'DRY RUN (add --apply to write)'}")
    print()

    for lang in LANGS:
        changes = patch_dict(lang) if apply else _preview_dict(lang)
        if changes:
            for c in changes:
                print(f"  {lang}: {c[0]:14} {c[1]!r} -> {c[2]!r}")

    idx = patch_index_html() if apply else _preview_index()
    for c in idx:
        print(f"  index.html: {c[3]} occurrence(s) of {c[1]} -> {c[2]}")

    print()
    print("done." if apply else "dry run - nothing written.")


def _preview_dict(lang):
    path = os.path.join("i18n", f"{lang}.json")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    changes = []
    if data.get(LIVE_KEY) != TRUST_LINE[lang]:
        changes.append(("trust-line", data.get(LIVE_KEY), TRUST_LINE[lang]))
    if data.get(NEW_TITLE_KEY) != FOOTER_TITLE[lang]:
        changes.append(("footer-title", data.get(NEW_TITLE_KEY, "(absent)"),
                        FOOTER_TITLE[lang]))
    return changes


def _preview_index():
    with open("index.html", encoding="utf-8") as fh:
        text = fh.read()
    if BROKEN_KEY in text:
        return [("index.html", BROKEN_KEY, LIVE_KEY, text.count(BROKEN_KEY))]
    return []


if __name__ == "__main__":
    main()
