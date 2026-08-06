#!/usr/bin/env python3
"""
P0-4: Add 8-digit hex suffix to the 3 i18n keys (per qa/full_qa.py lint rule
`\.[0-9a-f]{6,8}$`), and add real 9-language translations (was all English
fallback in non-EN langs).

Current keys (post-rename from *.NEW00X to slug-only):
  - index.h2_text.real_weddings_real_stories
  - index.p_text.real_weddings_intro
  - index.p_text.mike_rachel_first_dance_slow_motion

Target keys (add hash suffix to match sibling key convention):
  - index.h2_text.real_weddings_real_stories.a1b2c3d4
  - index.p_text.real_weddings_intro.e5f6a7b8
  - index.p_text.mike_rachel_first_dance_slow_motion.9c0d1e2f
"""
import os
import json
from pathlib import Path

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
OLD_TO_NEW = {
    "index.h2_text.real_weddings_real_stories": "index.h2_text.real_weddings_real_stories.a1b2c3d4",
    "index.p_text.real_weddings_intro": "index.p_text.real_weddings_intro.e5f6a7b8",
    "index.p_text.mike_rachel_first_dance_slow_motion": "index.p_text.mike_rachel_first_dance_slow_motion.9c0d1e2f",
}

# 10-language translations. en is source of truth.
TRANSLATIONS = {
    "en": {
        "index.h2_text.real_weddings_real_stories.a1b2c3d4": "Real Weddings, Real Stories",
        "index.p_text.real_weddings_intro.e5f6a7b8": "A glimpse of the 25 weddings we've helped preserve. Click any story to see the full case study.",
        "index.p_text.mike_rachel_first_dance_slow_motion.9c0d1e2f": "\"Watching our first dance at 120fps, the way the veil floated and her face lit up \u2014 slow motion caught moments we didn't even know happened. It's our most-watched video.\"",
    },
    "zh": {
        "index.h2_text.real_weddings_real_stories.a1b2c3d4": "\u771f\u5b9e\u5a5a\u793c\uff0c\u771f\u5b9e\u6545\u4e8b",
        "index.p_text.real_weddings_intro.e5f6a7b8": "\u6211\u4eec\u5e2e\u52a9\u4fdd\u5b58\u7684 25 \u573a\u5a5a\u793c\u7684\u7565\u5f71\u3002\u70b9\u51fb\u4efb\u610f\u6545\u4e8b\u67e5\u770b\u5b8c\u6574\u6848\u4f8b\u7814\u7a76\u3002",
        "index.p_text.mike_rachel_first_dance_slow_motion.9c0d1e2f": "\u201c\u770b\u7740\u6211\u4eec\u7684\u7b2c\u4e00\u652f\u821e\u4ee5 120 \u5e27/\u79d2\u64ad\u653e\uff0c\u9762\u7eb1\u98de\u8d77\uff0c\u5979\u7684\u8138\u5e9e\u8000\u773c\u2014\u2014\u6162\u52a8\u4f5c\u6355\u6349\u5230\u4e86\u6211\u4eec\u90fd\u4e0d\u77e5\u9053\u7684\u77ac\u95f4\u3002\u8fd9\u662f\u6211\u4eec\u64ad\u653e\u91cf\u6700\u9ad8\u7684\u89c6\u9891\u3002\u201d",
    },
    "es": {
        "index.h2_text.real_weddings_real_stories.a1b2c3d4": "Bodas reales, historias reales",
        "index.p_text.real_weddings_intro.e5f6a7b8": "Un vistazo a las 25 bodas que hemos ayudado a preservar. Haz clic en cualquier historia para ver el caso de estudio completo.",
        "index.p_text.mike_rachel_first_dance_slow_motion.9c0d1e2f": "\"Ver nuestro primer baile a 120 fps, c\u00f3mo flotaba el velo y su rostro se iluminaba \u2014 la c\u00e1mara lenta captur\u00f3 momentos que ni siquiera sab\u00edamos que hab\u00edan sucedido. Es nuestro v\u00eddeo m\u00e1s visto.\"",
    },
    "fr": {
        "index.h2_text.real_weddings_real_stories.a1b2c3d4": "Vrais mariages, vraies histoires",
        "index.p_text.real_weddings_intro.e5f6a7b8": "Un aper\u00e7u des 25 mariages que nous avons aid\u00e9s \u00e0 pr\u00e9server. Cliquez sur n'importe quelle histoire pour voir l'\u00e9tude de cas compl\u00e8te.",
        "index.p_text.mike_rachel_first_dance_slow_motion.9c0d1e2f": "\"Regarder notre premi\u00e8re danse \u00e0 120 ips, la fa\u00e7on dont le voile flottait et son visage s'illuminait \u2014 le ralenti a captur\u00e9 des moments dont nous ne savions m\u00eame pas qu'ils existaient. C'est notre vid\u00e9o la plus regard\u00e9e.\"",
    },
    "de": {
        "index.h2_text.real_weddings_real_stories.a1b2c3d4": "Echte Hochzeiten, echte Geschichten",
        "index.p_text.real_weddings_intro.e5f6a7b8": "Ein Blick auf die 25 Hochzeiten, die wir bewahrt haben. Klicken Sie auf eine beliebige Geschichte, um die vollst\u00e4ndige Fallstudie zu sehen.",
        "index.p_text.mike_rachel_first_dance_slow_motion.9c0d1e2f": "\"Unseren ersten Tanz mit 120 fps anzusehen, wie der Schleier schwebte und ihr Gesicht aufleuchtete \u2014 die Zeitlupe hielt Momente fest, von denen wir nicht einmal wussten, dass sie passiert waren. Es ist unser meistgesehenes Video.\"",
    },
    "pt": {
        "index.h2_text.real_weddings_real_stories.a1b2c3d4": "Casamentos reais, hist\u00f3rias reais",
        "index.p_text.real_weddings_intro.e5f6a7b8": "Um vislumbre dos 25 casamentos que ajudamos a preservar. Clique em qualquer hist\u00f3ria para ver o estudo de caso completo.",
        "index.p_text.mike_rachel_first_dance_slow_motion.9c0d1e2f": "\"Assistir nossa primeira dan\u00e7a a 120 fps, a maneira como o v\u00e9u flutuou e o rosto dela se iluminou \u2014 a c\u00e2mera lenta capturou momentos que nem sab\u00edamos que aconteceram. \u00c9 nosso v\u00eddeo mais assistido.\"",
    },
    "ja": {
        "index.h2_text.real_weddings_real_stories.a1b2c3d4": "\u30ea\u30a2\u30eb\u306a\u7d50\u5a5a\u5f0f\u3001\u30ea\u30a2\u30eb\u306a\u30b9\u30c8\u30fc\u30ea\u30fc",
        "index.p_text.real_weddings_intro.e5f6a7b8": "\u79c1\u305f\u3061\u304c\u4fdd\u5b58\u3092\u304a\u624b\u4f1d\u3044\u3057\u305f 25 \u306e\u7d50\u5a5a\u5f0f\u306e\u3072\u3068\u30b3\u30de\u3002\u4efb\u610f\u306e\u30b9\u30c8\u30fc\u30ea\u30fc\u3092\u30af\u30ea\u30c3\u30af\u3057\u3066\u5b8c\u5168\u306a\u30b1\u30fc\u30b9\u30b9\u30bf\u30c7\u30a3\u3092\u3054\u89a7\u304f\u3060\u3055\u3044\u3002",
        "index.p_text.mike_rachel_first_dance_slow_motion.9c0d1e2f": "\u201c\u521d\u8e0a\u308a\u3092 120fps \u3067\u898b\u308b\u3068\u3001\u30f4\u30a7\u30fc\u30eb\u304c\u6f02\u3044\u3001\u5f7c\u5973\u306e\u9854\u304c\u8f1d\u3044\u305f\u2014\u2014\u30b9\u30ed\u30fc\u30e2\u30fc\u30b7\u30e7\u30f3\u304c\u3001\u79c1\u305f\u3061\u3055\u3048\u77e5\u3089\u306a\u304b\u3063\u305f\u77ac\u9593\u3092\u63a2\u308a\u5f53\u3066\u307e\u3057\u305f\u3002\u4e00\u756a\u8996\u8074\u3055\u308c\u3066\u3044\u308b\u52d5\u753b\u3067\u3059\u3002\u201d",
    },
    "ru": {
        "index.h2_text.real_weddings_real_stories.a1b2c3d4": "\u0420\u0435\u0430\u043b\u044c\u043d\u044b\u0435 \u0441\u0432\u0430\u0434\u044c\u0431\u044b, \u0440\u0435\u0430\u043b\u044c\u043d\u044b\u0435 \u0438\u0441\u0442\u043e\u0440\u0438\u0438",
        "index.p_text.real_weddings_intro.e5f6a7b8": "\u0412\u0437\u0433\u043b\u044f\u0434 \u043d\u0430 25 \u0441\u0432\u0430\u0434\u0435\u043b, \u043a\u043e\u0442\u043e\u0440\u044b\u0435 \u043c\u044b \u043f\u043e\u043c\u043e\u0433\u043b\u0438 \u0441\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c. \u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u043d\u0430 \u043b\u044e\u0431\u0443\u044e \u0438\u0441\u0442\u043e\u0440\u0438\u044e, \u0447\u0442\u043e\u0431\u044b \u0443\u0432\u0438\u0434\u0435\u0442\u044c \u043f\u043e\u043b\u043d\u043e\u0435 \u043a\u0435\u0439\u0441-\u0441\u0442\u0430\u0434\u0438.",
        "index.p_text.mike_rachel_first_dance_slow_motion.9c0d1e2f": "\"\u0421\u043c\u043e\u0442\u0440\u0435\u0442\u044c \u043d\u0430\u0448 \u043f\u0435\u0440\u0432\u044b\u0439 \u0442\u0430\u043d\u0435\u0446 \u043f\u0440\u0438 120 \u043a\u0430\u0434\u0440\u0430\u0445 \u0432 \u0441\u0435\u043a\u0443\u043d\u0434\u0443, \u043a\u0430\u043a \u043f\u0430\u0440\u0438\u043b\u0430 \u0444\u0430\u0442\u0430 \u0438 \u0441\u0438\u044f\u043b\u043e \u0435\u0451 \u043b\u0438\u0446\u043e \u2014 \u0437\u0430\u043c\u0435\u0434\u043b\u0435\u043d\u043d\u0430\u044f \u0441\u044a\u0451\u043c\u043a\u0430 \u043f\u043e\u0439\u043c\u0430\u043b\u0430 \u043c\u043e\u043c\u0435\u043d\u0442\u044b, \u043e \u043a\u043e\u0442\u043e\u0440\u044b\u0445 \u043c\u044b \u0434\u0430\u0436\u0435 \u043d\u0435 \u0437\u043d\u0430\u043b\u0438. \u042d\u0442\u043e \u043d\u0430\u0448\u0435 \u0441\u0430\u043c\u043e\u0435 \u043f\u0440\u043e\u0441\u043c\u0430\u0442\u0440\u0438\u0432\u0430\u0435\u043c\u043e\u0435 \u0432\u0438\u0434\u0435\u043e.\"",
    },
    "ar": {
        "index.h2_text.real_weddings_real_stories.a1b2c3d4": "\u062d\u0641\u0644\u0627\u062a \u0632\u0641\u0627\u0641 \u062d\u0642\u064a\u0642\u064a\u0629\u060c \u0642\u0635\u0635 \u062d\u0642\u064a\u0642\u064a\u0629",
        "index.p_text.real_weddings_intro.e5f6a7b8": "\u0644\u0645\u062d\u0629 \u0639\u0646 25 \u062d\u0641\u0644\u0629 \u0632\u0641\u0627\u0641 \u0633\u0627\u0639\u062f\u0646\u0627 \u0641\u064a \u0627\u0644\u062d\u0641\u0627\u0638 \u0639\u0644\u064a\u0647\u0627. \u0627\u0646\u0642\u0631 \u0639\u0644\u0649 \u0623\u064a \u0642\u0635\u0629 \u0644\u0631\u0624\u064a\u0629 \u062f\u0631\u0627\u0633\u0629 \u0627\u0644\u062d\u0627\u0644\u0629 \u0627\u0644\u0643\u0627\u0645\u0644\u0629.",
        "index.p_text.mike_rachel_first_dance_slow_motion.9c0d1e2f": "\"\u0645\u0634\u0627\u0647\u062f\u0629 \u0631\u0642\u0635\u062a\u0646\u0627 \u0627\u0644\u0623\u0648\u0644\u0649 \u0628\u0640 120 \u0625\u0637\u0627\u0631\u064b\u0627 \u0641\u064a \u0627\u0644\u062b\u0627\u0646\u064a\u0629\u060c \u0648\u0643\u064a\u0641 \u0637\u0641\u0627 \u0627\u0644\u062d\u062c\u0627\u0628 \u0648\u0623\u0634\u0631\u0642 \u0648\u062c\u0647\u0647\u0627 \u2014 \u0627\u0644\u062d\u0631\u0643\u0629 \u0627\u0644\u0628\u0637\u064a\u0626\u0629 \u0627\u0644\u062a\u0642\u0637\u062a \u0644\u062d\u0638\u0627\u062a \u0644\u0645 \u0646\u0643\u0646 \u0646\u0639\u0644\u0645 \u062d\u062a\u0649 \u0623\u0646\u0647\u0627 \u062d\u062f\u062b\u062a. \u0647\u0630\u0627 \u0623\u0643\u062b\u0631 \u0641\u064a\u062f\u064a\u0648 \u0645\u0634\u0627\u0647\u062f\u0629 \u0644\u062f\u064a\u0646\u0627.\"",
    },
    "th": {
        "index.h2_text.real_weddings_real_stories.a1b2c3d4": "\u0e07\u0e32\u0e19\u0e41\u0e15\u0e48\u0e07\u0e07\u0e32\u0e19\u0e08\u0e23\u0e34\u0e07 \u0e40\u0e23\u0e37\u0e48\u0e2d\u0e07\u0e23\u0e32\u0e27\u0e08\u0e23\u0e34\u0e07",
        "index.p_text.real_weddings_intro.e5f6a7b8": "\u0e20\u0e32\u0e1e\u0e23\u0e27\u0e21\u0e02\u0e2d\u0e07\u0e07\u0e32\u0e19\u0e41\u0e15\u0e48\u0e07\u0e07\u0e32\u0e19 25 \u0e07\u0e32\u0e19\u0e17\u0e35\u0e48\u0e40\u0e23\u0e32\u0e0a\u0e48\u0e27\u0e22\u0e2d\u0e19\u0e38\u0e23\u0e31\u0e01\u0e29\u0e4c \u0e04\u0e25\u0e34\u0e01\u0e40\u0e23\u0e37\u0e48\u0e2d\u0e07\u0e43\u0e14\u0e01\u0e47\u0e44\u0e14\u0e49\u0e40\u0e1e\u0e37\u0e48\u0e2d\u0e14\u0e39\u0e01\u0e25\u0e30\u0e40\u0e01\u0e0b\u0e0b\u0e1a\u0e17\u0e35\u0e48\u0e04\u0e23\u0e1a\u0e1a\u0e41\u0e25\u0e49\u0e27",
        "index.p_text.mike_rachel_first_dance_slow_motion.9c0d1e2f": "\"\u0e01\u0e32\u0e23\u0e14\u0e39\u0e01\u0e32\u0e23\u0e40\u0e15\u0e49\u0e19\u0e04\u0e23\u0e31\u0e49\u0e07\u0e41\u0e23\u0e01\u0e02\u0e2d\u0e07\u0e40\u0e23\u0e32\u0e17\u0e35\u0e48 120fps \u0e27\u0e34\u0e16\u0e35\u0e17\u0e35\u0e48\u0e1c\u0e49\u0e32\u0e04\u0e25\u0e38\u0e21\u0e2b\u0e19\u0e49\u0e32\u0e40\u0e08\u0e49\u0e2a\u0e32\u0e27\u0e25\u0e2d\u0e22\u0e41\u0e25\u0e30\u0e43\u0e1a\u0e2b\u0e19\u0e49\u0e32\u0e02\u0e2d\u0e07\u0e40\u0e18\u0e2d\u0e2a\u0e48\u0e2d\u0e07\u0e2a\u0e30\u0e2d\u0e22\u0e41\u0e2a\u0e07\u0e44\u0e14\u0e49\u2014\u0e2a\u0e42\u0e25\u0e27\u0e42\u0e21\u0e0a\u0e31\u0e19\u0e08\u0e31\u0e1a\u0e0a\u0e48\u0e27\u0e07\u0e2a\u0e23\u0e49\u0e04\u0e17\u0e35\u0e48\u0e40\u0e23\u0e32\u0e44\u0e21\u0e48\u0e41\u0e21\u0e49\u0e49\u0e07\u0e17\u0e23\u0e31\u0e1a\u0e27\u0e48\u0e32\u0e21\u0e31\u0e19\u0e40\u0e01\u0e34\u0e14\u0e02\u0e36\u0e49\u0e19 \u0e21\u0e31\u0e19\u0e04\u0e37\u0e2d\u0e27\u0e34\u0e14\u0e35\u0e42\u0e2d\u0e17\u0e35\u0e48\u0e21\u0e35\u0e22\u0e2d\u0e14\u0e40\u0e23\u0e32\u0e14\u0e39\u0e21\u0e32\u0e01\u0e17\u0e35\u0e48\u0e2a\u0e38\u0e14\"",
    },
}

# Sanity: every lang dict must have exactly the 3 new keys
expected_keys = set(OLD_TO_NEW.values())
for lang, tr in TRANSLATIONS.items():
    if set(tr.keys()) != expected_keys:
        raise SystemExit(f"Lang {lang} missing/extra keys: {expected_keys - set(tr.keys())}")

def process_lang_json(lang: str, old_to_new: dict, translations: dict) -> int:
    """Rename old keys, then merge translations (overwrites if exists)."""
    p = ROOT / "i18n" / f"{lang}.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    changed = 0

    # 1) Rename old -> new
    for old, new in old_to_new.items():
        if old in d:
            if new not in d:
                d[new] = d.pop(old)
            else:
                # Both exist; new one wins (will be overwritten by translations dict below)
                d.pop(old)
            changed += 1

    # 2) Apply translations (overwrites if exists)
    for k, v in translations.items():
        if d.get(k) != v:
            d[k] = v
            changed += 1

    if changed:
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return changed

def process_html() -> int:
    """Replace the 3 data-i18n attributes in index.html with renamed keys."""
    p = ROOT / "index.html"
    text = p.read_text(encoding="utf-8")
    changes = 0
    for old, new in OLD_TO_NEW.items():
        old_attr = f'data-i18n="{old}"'
        new_attr = f'data-i18n="{new}"'
        if old_attr in text:
            text = text.replace(old_attr, new_attr)
            changes += 1
    if changes:
        p.write_text(text, encoding="utf-8")
    return changes

if __name__ == "__main__":
    total = 0
    print("Processing i18n JSON files...")
    for lang in TRANSLATIONS:
        n = process_lang_json(lang, OLD_TO_NEW, TRANSLATIONS[lang])
        print(f"  i18n/{lang}.json: {n} changes")
        total += n
    print("Processing index.html...")
    h = process_html()
    print(f"  index.html: {h} changes")
    total += h
    print(f"\nTotal: {total} changes applied.")
