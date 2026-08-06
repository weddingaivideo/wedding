"""
Targeted fixes for the most-obvious machine-translation errors in i18n/*.json.

Discovered during the 5-min spot-check of the top 60 lines of each translation.
Scope: ONLY keys with high user-visibility (CTAs, headings, form labels, hero copy,
proper nouns, format names). Idempotent: re-running applies the same values.

Run from repo root:
    python scripts/i18n_fix_critical.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "i18n"

# (key, lang) -> corrected value
# Each entry is a string in the target language. Only fix what is *clearly* wrong
# (mistranslation of a proper noun, wrong sense of an English polyseme, etc.).
# Do NOT add stylistic preferences here.
FIXES: dict[tuple[str, str], str] = {
    # 404 footer / page-level nav
    ("404.h3_text.contact.47569808", "zh"): "联系",
    ("404.h3_text.contact.47569808", "ja"): "お問い合わせ",
    # "Resolution" in video context = 分辨率 (display resolution), NOT 解决 (problem solving)
    ("blog.03-ai-wedding-video-generator.strong_text.resolution.74915346", "zh"): "分辨率",
    ("blog.03-ai-wedding-video-generator.strong_text.resolution.74915346", "ja"): "解像度",
    ("blog.03-ai-wedding-video-generator.strong_text.resolution.74915346", "th"): "ความละเอียด",
    # "Turnaround" in delivery/shipping context = delivery time. Google picked the
    # verb (turn around) and produced nonsense across 7 languages.
    ("blog.03-ai-wedding-video-generator.strong_text.turnaround.02723176", "es"): "Plazo de entrega",
    ("blog.03-ai-wedding-video-generator.strong_text.turnaround.02723176", "fr"): "Délai de livraison",
    ("blog.03-ai-wedding-video-generator.strong_text.turnaround.02723176", "de"): "Lieferzeit",
    ("blog.03-ai-wedding-video-generator.strong_text.turnaround.02723176", "pt"): "Prazo de entrega",
    ("blog.03-ai-wedding-video-generator.strong_text.turnaround.02723176", "ja"): "納期",
    ("blog.03-ai-wedding-video-generator.strong_text.turnaround.02723176", "ru"): "Срок выполнения",
    ("blog.03-ai-wedding-video-generator.strong_text.turnaround.02723176", "ar"): "مدة التسليم",
    ("blog.03-ai-wedding-video-generator.strong_text.turnaround.02723176", "th"): "ระยะเวลาดำเนินการ",
    # "CapCut" is a proper noun (video-editing app). Don't translate.
    ("blog.05-wedding-slow-motion-effect.strong_text.capcut.48651080", "es"): "CapCut",
    ("blog.05-wedding-slow-motion-effect.strong_text.capcut.48651080", "pt"): "CapCut",
    # "Hi8" is a tape-format name. RU got "Привет" (Hello).
    ("blog.02-vhs-to-digital-wedding-cost.strong_text.hi8_video8.42487760", "ru"): "Hi8/Video8:",
    # "The Patels" is a plural surname in EN, but PT/AR don't pluralize surnames
    # with an extra letter — drop the s in the local-script spelling.
    ("blog.01-restore-old-wedding-videos.strong_text.the_patels.34884081", "pt"): "Os Patel:",
    ("blog.01-restore-old-wedding-videos.strong_text.the_patels.34884081", "ar"): "الباتل:",
    # "MiniDV" / "Digital8" / "Hi8" / "VHS-C" / "Betamax" — all proper format names
    # (Sony / JVC / Matsushita trademarked). Keep Latin transliteration when possible
    # to avoid confusion with the actual products.
    ("blog.02-vhs-to-digital-wedding-cost.strong_text.minidv.16424136", "ru"): "MiniDV:",
    ("blog.02-vhs-to-digital-wedding-cost.strong_text.digital8.00463441", "ru"): "Digital8:",
    # "Act Now" in AR — drop the definite article prefix; the imperative is cleaner.
    ("blog.01-restore-old-wedding-videos.strong_text.act_now.40625536", "ar"): "تصرف الآن",
    # "Best for" — keep semantically equivalent; idiomatic tweak only.
    ("blog.01-restore-old-wedding-videos.strong_text.best_for.45069183", "es"): "Ideal para",
    ("blog.01-restore-old-wedding-videos.strong_text.best_for.45069183", "pt"): "Ideal para",
    ("blog.01-restore-old-wedding-videos.strong_text.best_for.45069183", "de"): "Ideal für",
}


def main() -> int:
    if not I18N.is_dir():
        print(f"i18n dir not found: {I18N}")
        return 1

    by_lang: dict[str, list[tuple[str, str]]] = {}
    for (key, lang), value in FIXES.items():
        by_lang.setdefault(lang, []).append((key, value))

    total_files = 0
    total_keys = 0
    total_misses: list[str] = []

    for lang, kvs in sorted(by_lang.items()):
        path = I18N / f"{lang}.json"
        if not path.exists():
            print(f"  SKIP {lang}: file not found")
            continue
        data: dict = json.loads(path.read_text(encoding="utf-8"))
        changed = 0
        for k, v in kvs:
            if k not in data:
                total_misses.append(f"{lang} :: {k}")
                continue
            old = data[k]
            if old == v:
                continue
            data[k] = v
            changed += 1
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        total_files += 1
        total_keys += changed
        print(f"  {lang}.json: {changed}/{len(kvs)} keys fixed")

    if total_misses:
        print("\nMISSING KEYS (no-op, key not in this language file):")
        for m in total_misses:
            print(f"  {m}")

    print(f"\nDone. {total_files} files, {total_keys} keys updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
