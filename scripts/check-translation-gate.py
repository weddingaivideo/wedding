#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Regression test for the translation gate's script rules.

Four rules live here and every one of them has bitten:

1. script_independent() - a measurement, a paper size, a brand and a
   domain are spelled the same in every language, so the English source
   IS the translation. Before the rule, script_ok() threw the correct
   answer away and the runner asked for it again in every round, for
   every language.

2. The Japanese kana rule - a Japanese label is often pure kanji and is
   correct. Before the rule, script_ok() threw those away too.

3. The English echo - for a non-Latin target the model handing back the
   English source is never a translation, and foreign_spans() cannot
   see it, because an all-Latin value has no non-Latin run.

4. The Chinese rendering - a Chinese sentence in a Japanese page. That
   one is caught exactly, by comparing against the Chinese rendering of
   the same string, not by a heuristic.

WHY A TEST AND NOT A RULE
-------------------------
Every one of these rules was added to fix a false rejection, and a rule
that only ever rejects is easy to write and easy to get wrong in the
loose direction. So every ACCEPT case has a twin REJECT case that
differs only in the way the rule must not be blind to, and the negative
control turns the new rule OFF to prove the test can see it.

Usage:
    python scripts/check-translation-gate.py
    python scripts/check-translation-gate.py --negative-control
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_gate():
    spec = importlib.util.spec_from_file_location(
        "ttp", os.path.join(ROOT, "scripts", "translate-tool-page.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


T = load_gate()

# (source, value, lang, zh_value, expected_accept, why)
STORED = [
    # --- kept verbatim: the English source IS the translation ---
    ("5 × 7 in", "5 × 7 in", "ja", None, True, "a measurement"),
    ("1500 × 2100 px", "1500 × 2100 px", "zh", None, True, "a measurement"),
    ("300 DPI", "300 DPI", "th", None, True, "a resolution"),
    ("A2", "A2", "ru", None, True, "a paper size"),
    ("A7 (5.25 × 7.25 in)", "A7 (5.25 × 7.25 in)", "hi", None, True, "a paper size"),
    ("4-bar (A1)", "4-bar (A1)", "ja", None, True, "a paper size"),
    ("Canva", "Canva", "ar", None, True, "a brand"),
    ("Greetings Island", "Greetings Island", "zh", None, True, "a vendor name"),
    ("Smallpdf", "Smallpdf", "ru", None, True, "a vendor name"),
    ("WeddingAI.video", "WeddingAI.video", "th", None, True, "the brand"),
    ("PDF", "PDF", "ja", None, True, "a format name"),
    ("18 × 24 in", "18 × 24 in", "es", None, True, "a Latin target, same spelling"),

    # --- the value must be IDENTICAL, not merely similar ---
    ("5 × 7 in", "5 x 7 in", "ja", None, False, "the sign was changed"),
    ("A2", "A3", "ru", None, False, "the paper size was changed"),

    # --- a Japanese label in pure kanji is correct ---
    ("Wedding date", "挙式日", "ja", "婚礼日期", True, "pure kanji Japanese"),
    ("Ceremony venue", "挙式会場", "ja", "典礼场地", True, "pure kanji Japanese"),
    ("City", "市区町村", "ja", "城市", True, "pure kanji Japanese"),
    ("Reception venue", "披露宴会場", "ja", "婚宴场地", True, "pure kanji Japanese"),
    ("Envelope", "封筒", "ja", "信封", True, "pure kanji Japanese"),
    ("Output", "出力", "ja", "输出", True, "pure kanji Japanese"),
    ("Invitation", "招待状", "ja", "邀请函", True, "pure kanji Japanese"),
    ("Place card", "席札", "ja", "座位卡", True, "pure kanji Japanese"),
    ("Print resolution", "印刷解像度", "ja", "打印分辨率", True, "pure kanji Japanese"),
    ("Standard PDF", "標準PDF", "ja", "标准PDF", True, "kanji plus a format name"),

    # --- a CHINESE sentence in a Japanese page is still caught ---
    ("Frequently asked questions", "常见问题", "ja", "常见问题", False,
     "the Chinese rendering"),
    ("Wedding date", "婚礼日期", "ja", "婚礼日期", False,
     "the Chinese rendering"),

    # --- an English echo is never a translation ---
    ("Wedding date", "Wedding date", "ja", "婚礼日期", False, "an English echo"),
    ("Output", "Output", "th", None, False, "an English echo"),
    ("Home", "Home", "ar", None, False, "an English echo"),

    # --- an English paragraph is still caught ---
    ("Your wedding details are drawn and exported in your browser.",
     "Your wedding details are drawn and exported in your browser.",
     "ja", None, False, "an untranslated paragraph"),
    ("Print resolution", "Print resolution", "zh", None, False, "an untranslated label"),
    ("Free Tools", "Free Tools", "ru", None, False, "an untranslated label"),
    ("Output", "Output", "th", None, False, "an untranslated label"),

    # --- a SIZE WRITTEN WITH AN "x" is a measurement ---
    ("5x7", "5x7", "zh", None, True, "a size written with an x"),
    ("3.5x5", "3.5x5", "ja", None, True, "a size written with an x"),
    ("18x24", "18x24", "ru", None, True, "a size written with an x"),
    ("print size 5x7 inch", "打印尺寸 5x7 inch", "zh", None, True,
     "a size inside a phrase"),
    ("Free in-browser wedding stationery set maker. Six pieces in four "
     "coordinated styles, exported as ONE PDF where every page keeps its own "
     "print size (5x7, 3.5x5, 3.5x2, 4.25x5.5 and 18x24 inch) at 300 DPI.",
     "浏览器内的免费婚礼纸品套装制作工具。四个协调风格，导出一份 PDF，"
     "每页保留自己的印刷尺寸（5x7、3.5x5、3.5x2、4.25x5.5 和 18x24 英寸），"
     "300 DPI。",
     "zh", None, True, "a description that quotes the sizes"),

    # --- a word that is English AND a word of the target ---
    ("On quantity: one invitation per household, plus 10 to 15 people.",
     "Auf Menge: eine Einladung pro Haushalt, plus 10 bis 15 Personen, und "
     "Sie können auch die Karte selbst gestalten.",
     "de", None, True, "a German sentence with the German word 'also'"),
    ("On quantity: one invitation per household, plus 10 to 15 people.",
     "On quantity: one invitation per household, plus 10 to 15 people, and "
     "you can also design the card yourself.",
     "es", None, False, "an English sentence in a Spanish page"),

    # --- a CODEC name the model keeps, next to a format name ---
    ("Opus or Vorbis, copied when it fits",
     "Opus 或 Vorbis，合适时复制", "zh", None, True, "a codec name"),
    ("Opus or Vorbis, copied when it fits",
     "Opus または Vorbis、収まるものをコピー", "ja", None, True,
     "a codec name next to a format name"),
    ("Opus or Vorbis, copied when it fits",
     "Opus oder Vorbis, je nachdem, was passt", "de", None, True,
     "a codec name in a Latin language"),

    # --- "Shorts" on its own, the way the model writes it ---
    ("For a phone, use MP4. convertbox.app recommends MP4 with H.264 for "
     "Reels, TikTok and YouTube Shorts.",
     "手机观看请使用 MP4。convertbox.app 推荐在 Reels、TikTok 和 Shorts 中"
     "使用采用 H.264 编码的 MP4。",
     "zh", None, True, "a bare product name next to a vendor domain"),

    # --- the Lightroom menus the copy quotes ---
    ("Open the Print module - Alt+Ctrl+6 on Windows, ALT+CMD+6 on Mac - "
     "pick a layout from the Template Browser, set the Page Grid and the "
     "Cell Spacing.",
     "Windows では Alt+Ctrl+6、Mac では ALT+CMD+6 で開き、Template "
     "Browser からレイアウトを選び、Page Grid と Cell Spacing を設定します。",
     "ja", None, True, "a menu name the copy quotes on purpose"),

    # --- a vendor domain and a product name INSIDE a translated sentence ---
    # The video editor quotes two vendor sites, four platforms and a codec
    # in one sentence. The model translated the sentence and kept the
    # names; the gate read "MP4 convertbox.app" as one English run and
    # threw the whole paragraph away in six languages at once.
    ("For a phone, use MP4. convertbox.app recommends MP4 with H.264 for "
     "Reels, TikTok and YouTube Shorts, and feelthefile.com lists Instagram "
     "at up to 1080 × 1920 and 30 fps and YouTube at up to 1080p and 60 fps. "
     "The vertical preset in this editor is exactly 1080 × 1920.",
     "在手机上使用 MP4。convertbox.app 推荐在 Reels、TikTok 和 YouTube Shorts "
     "中使用采用 H.264 的 MP4；feelthefile.com 列出的规格为 Instagram 最高 "
     "1080 × 1920、30 fps，YouTube 最高 1080p、60 fps。本编辑器的竖屏预设正是 "
     "1080 × 1920。",
     "zh", None, True, "a vendor domain next to a format name"),
    ("For a phone, use MP4. convertbox.app recommends MP4 with H.264 for "
     "Reels, TikTok and YouTube Shorts, and feelthefile.com lists Instagram "
     "at up to 1080 × 1920 and 30 fps and YouTube at up to 1080p and 60 fps. "
     "The vertical preset in this editor is exactly 1080 × 1920.",
     "For a phone, use MP4. convertbox.app recommends MP4 with H.264 for "
     "Reels, TikTok and YouTube Shorts, and feelthefile.com lists Instagram "
     "at up to 1080 × 1920 and 30 fps and YouTube at up to 1080p and 60 fps. "
     "The vertical preset in this editor is exactly 1080 × 1920.",
     "zh", None, False, "the same names, but the sentence is still English"),

    # --- a browser name next to a version, in a Japanese sentence ---
    ("The export needs WebCodecs, the browser API that does the actual "
     "video work. Chrome and Edge have shipped it for years, Safari 16.4 and "
     "newer have it, and freevideogenerator.io lists Firefox as limited "
     "support. If the export button refuses to run, that is usually why.",
     "書き出しには、実際に動画処理を行うブラウザAPIであるWebCodecsが必要です。"
     "ChromeとEdgeでは数年前から対応しており、Safari 16.4以降でも利用できます。"
     "freevideogenerator.ioではFirefoxは限定的なサポートと記載されています。"
     "書き出しボタンが動作しない場合は、通常これが原因です。",
     "ja", None, True, "browser names and a version in a Japanese sentence"),
    ("The export needs WebCodecs, the browser API that does the actual "
     "video work. Chrome and Edge have shipped it for years, Safari 16.4 and "
     "newer have it, and freevideogenerator.io lists Firefox as limited "
     "support. If the export button refuses to run, that is usually why.",
     "The export needs WebCodecs, the browser API that does the actual "
     "video work. Chrome and Edge have shipped it for years, Safari 16.4 and "
     "newer have it, and freevideogenerator.io lists Firefox as limited "
     "support. If the export button refuses to run, that is usually why.",
     "ja", None, False, "the same names, but the sentence is still English"),

    # --- "has" is the Spanish verb, not an English leftover ---
    ("One thing is worth knowing before you start. If the clip is already in "
     "the format you asked for and you did not change the frame size, the "
     "editor copies the original video stream instead of re-encoding it. "
     "That is fast and it changes nothing in the picture. As soon as you "
     "change the size or the container, the video has to be re-encoded, and "
     "a re-encode always costs a little quality.",
     "Conviene saber una cosa antes de empezar. Si el clip ya está en el "
     "formato que has elegido y no has cambiado las dimensiones del "
     "fotograma, el editor copia el flujo de video original en lugar de "
     "volver a codificarlo. Es rápido y no altera la imagen. En cuanto "
     "cambias el tamaño o el contenedor, el video debe volver a codificarse, "
     "y eso siempre supone una pequeña pérdida de calidad.",
     "es", None, True, "the Spanish verb 'has'"),
    ("One thing is worth knowing before you start. If the clip is already in "
     "the format you asked for and you did not change the frame size, the "
     "editor copies the original video stream instead of re-encoding it. "
     "That is fast and it changes nothing in the picture. As soon as you "
     "change the size or the container, the video has to be re-encoded, and "
     "a re-encode always costs a little quality.",
     "One thing is worth knowing before you start. If the clip is already in "
     "the format you asked for and you did not change the frame size, the "
     "editor copies the original video stream instead of re-encoding it. "
     "That is fast and it changes nothing in the picture. As soon as you "
     "change the size or the container, the video has to be re-encoded, and "
     "a re-encode always costs a little quality.",
     "es", None, False, "the English sentence in a Spanish page"),

    # --- a numbered step whose label is a format name ---
    ("1. Add your PDF files", "1. PDF ファイルを追加",
     "ja", None, True, "a list marker next to a format name"),
    ("1. Add your PDF files", "1. Add your PDF ファイルを追加",
     "ja", None, False, "a list marker next to English words"),

    # --- the two rules added on 2026-11-16 ------------------------------
    # A value of "...." is what a failed pipeline leaves behind. It has no
    # English word, no Latin run, and for a Latin target the script check is
    # vacuous - so every other rule called it good.
    ("Wedding Cake Servings Guide", "....", "ja", None, False,
     "a placeholder, not a translation"),
    ("Wedding Cake Servings Guide", "....", "de", None, False,
     "a placeholder in a Latin target too"),
    ("Wedding Cake Servings Guide", "How....", "ja", None, False,
     "a truncated placeholder"),
    # A word from ANOTHER language inside this one. foreign_spans() only
    # looks for Latin runs, so the Chinese word in a Russian sentence was
    # invisible to it.
    ("A small display cake for photos", "Небольшой展示торт для фотографий",
     "ru", None, False, "a Chinese word inside a Russian sentence"),
    ("A small display cake for photos", "婚礼展示蛋糕",
     "ja", None, False, "a Chinese sentence in the Japanese dictionary"),
    ("A small display cake for photos", "Небольшой торт для фотографий",
     "ru", None, True, "a clean Russian sentence"),
    # ... and the rules must not fire on a good value.
    ("Wedding date", "挙式日", "ja", "婚礼日期", True,
     "Han is not foreign to Japanese"),
    ("Wedding date", "婚礼日期", "zh", None, True,
     "Han is not foreign to Chinese"),
    ("WeddingAI.video", "WeddingAI.video", "ru", None, True,
     "the brand stays Latin in every language"),
    ("WeddingAI.video PDF", "WeddingAI.video PDF", "ru", None, True,
     "a brand and a format name stay Latin"),
    # A single Latin letter is a SIZE GRADE, not an English span: Japanese
    # writes "A判" and keeps the letter. The gate used to reject the whole
    # translation over it and the re-translation wrote the ENGLISH SOURCE
    # into the Japanese dictionary instead.
    ("A-series or square formats", "A判や正方形サイズ", "ja", None, True,
     "a single Latin letter is not an English span"),
    ("A-series or square formats", "A判や square formats", "ja", None, False,
     "but a whole English phrase next to it still is"),
    # A COLOUR PROFILE next to a format name. The names are already in
    # LATIN_KEEP as whole runs; the gap was that they could not sit inside
    # a LONGER run, and a correct Japanese paragraph was thrown away over
    # "sRGB JPEG" on 2026-11-16.
    ("Colour profiles differ too", "sRGB JPEG と Adobe RGB を選ぶ", "ja", None, True,
     "a colour profile name next to another name"),
    ("Colour profiles differ too", "sRGB JPEG と square formats を選ぶ", "ja", None, False,
     "but an English phrase next to it still is"),
]

# (source, value, lang, expected_ok, why)
FRESH = [
    ("Wedding date", "挙式日", "ja", True, "pure kanji Japanese is fine"),
    ("5 × 7 in", "5 × 7 in", "ja", True, "a measurement stays Latin"),
    ("Output", "出力", "ja", True, "a normal Japanese label"),
    ("City", "市区町村", "zh", True, "a normal Chinese label"),
    ("Wedding date", "Wedding date", "ja", False, "an English echo"),
    ("Output", "Output", "th", False, "an English echo"),
    ("Home", "Home", "ru", False, "an English echo"),
    # --- the two rules added on 2026-11-16 ------------------------------
    ("Portion", "....", "ja", False, "a placeholder, not a translation"),
    ("Portion", "....", "th", False, "a placeholder in any language"),
    ("A small display cake", "Небольшой展示торт", "ru", False,
     "a Chinese word inside a Russian sentence"),
    ("A small display cake", "Небольшой торт", "ru", True,
     "a clean Russian sentence"),
    ("Part of the cake", "ケーキの一部", "ja", True,
     "a clean Japanese sentence"),
    # --- the single-letter rule, added 2026-11-16 after the re-translation
    # --- lost a good Japanese value to it -------------------------------
    ("A-series or square formats", "A判や正方形サイズ", "ja", True,
     "a single Latin letter is not an English span"),
    ("A-series or square formats", "A判や square formats", "ja", False,
     "but a whole English phrase next to it still is"),
    ("Colour profiles differ too", "sRGB JPEG と Adobe RGB を選ぶ", "ja", True,
     "a colour profile name next to another name"),
    ("Colour profiles differ too", "sRGB JPEG と square formats を選ぶ", "ja", False,
     "but an English phrase next to it still is"),
]


# The cases that depend on the rules added on 2026-11-16: a technical
# NAME is allowed next to another name inside a Latin run, and "has" is
# the Spanish verb. The negative control has to be able to see them too,
# or a test that cannot see them proves nothing about them.
NEW_RULE_WHYS = {
    "a vendor domain next to a format name",
    "browser names and a version in a Japanese sentence",
    "the Spanish verb 'has'",
    "a single Latin letter is not an English span",
    "a colour profile name next to another name",
}

# The good values that the 2026-11-16 rules must NOT fire on. They are
# checked by the normal run (run_cases asserts they are accepted with the
# rules ON); the negative control does not use them, because a case that is
# accepted with the rules off as well is not a rule-dependent case.
NEW_RULE_KEEP_WHYS = {
    "Han is not foreign to Japanese",
    "Han is not foreign to Chinese",
    "the brand stays Latin in every language",
    "a brand and a format name stay Latin",
    "a clean Russian sentence",
    "a clean Japanese sentence",
}

# The cases that MUST be rejected BECAUSE of the 2026-11-16 rules. With the
# rules switched off they would be accepted, and that is exactly what the
# negative control has to observe: a rule nothing depends on is a rule
# nothing tests.
#
# The other new cases are the opposite kind: a good value that must still be
# ACCEPTED. Those prove the rules do not fire on a brand, a format name, a
# Han-character Japanese label or a clean sentence.
NEW_RULE_REJECT_WHYS = {
    "a placeholder, not a translation",
    "a placeholder in a Latin target too",
    "a placeholder in any language",
    "a truncated placeholder",
    "a Chinese word inside a Russian sentence",
    "a Chinese sentence in the Japanese dictionary",
}


def run_cases():
    failures = []
    for source, value, lang, zh, expect, why in STORED:
        got = T.verify_stored(source, value, 0, lang, zh)
        if got != expect:
            failures.append("verify_stored %-3s %-22r expected=%s got=%s  (%s)"
                            % (lang, value[:22], expect, got, why))
    for source, value, lang, ok, why in FRESH:
        reason = T.llm_verify(source, value, [], 0, lang)
        if (reason is None) != ok:
            failures.append("llm_verify    %-3s %-22r expected_ok=%s reason=%r  (%s)"
                            % (lang, value[:22], ok, reason, why))
    return failures


def negative_control_new_rules():
    """Turn the NEW rules off and prove the test notices.

    The first negative control disables script_independent(). That rule is
    old; the rules of 2026-11-16 are newer and a test that cannot see
    them is just as blind. The 2026-11-16 rules are three: a technical
    NAME may sit next to another name inside a Latin run, "has" is the
    Spanish verb, and a value may not be a placeholder ("....") or carry a
    word from another language.
    """
    original_word_okay = T.technical_word_okay
    original_keep = dict(T.LATIN_TARGET_KEEP)
    original_placeholder = T.placeholder_value
    original_foreign = T.foreign_script_spans
    original_single_letter = T.single_letter_run_allowed
    # Two kinds of new-rule case, and they need OPPOSITE observations.
    #
    # (a) a case that must be ACCEPTED and that the new rules are what make
    #     acceptable: with the rules off it has to be REJECTED. If it is
    #     still accepted, the test cannot see the rule at all.
    # (b) a case that must be REJECTED BECAUSE of the new rules: with the
    #     rules off it has to be ACCEPTED. If it is still rejected, some
    #     older rule was doing the work and the new rule is untested.
    accept_depends = [c for c in STORED if c[5] in NEW_RULE_WHYS and c[4]]
    accept_fresh = [c for c in FRESH if c[4] in NEW_RULE_WHYS and c[3]]
    reject_depends = [c for c in STORED if c[5] in NEW_RULE_REJECT_WHYS]
    reject_fresh = [c for c in FRESH if c[4] in NEW_RULE_REJECT_WHYS]
    if not (accept_depends or accept_fresh or reject_depends or reject_fresh):
        print("[FAIL] negative control: no case depends on the new rules")
        return 1
    T.technical_word_okay = lambda word: False
    T.LATIN_TARGET_KEEP = {k: (set(v) - {"has"})
                           for k, v in original_keep.items()}
    T.placeholder_value = lambda value: False
    T.foreign_script_spans = lambda value, lang: []
    # The single-letter allowance is a rule too: with it off, "A判" has to
    # be REJECTED, or the test cannot see the rule at all.
    T.single_letter_run_allowed = lambda run: False
    try:
        still_passing = []
        for s, v, l, z, e, w in accept_depends:
            if T.verify_stored(s, v, 0, l, z):
                still_passing.append((s, v, l))
        for s, v, l, ok, w in accept_fresh:
            if T.llm_verify(s, v, [], 0, l) is None:
                still_passing.append((s, v, l))
        newly_accepted = []
        for s, v, l, z, e, w in reject_depends:
            if T.verify_stored(s, v, 0, l, z):
                newly_accepted.append((s, v, l))
        for s, v, l, ok, w in reject_fresh:
            if T.llm_verify(s, v, [], 0, l) is None:
                newly_accepted.append((s, v, l))
    finally:
        T.technical_word_okay = original_word_okay
        T.LATIN_TARGET_KEEP = original_keep
        T.placeholder_value = original_placeholder
        T.foreign_script_spans = original_foreign
        T.single_letter_run_allowed = original_single_letter

    problems = []
    if still_passing:
        problems.append("%d of %d accept-case(s) still passed without the new "
                        "rules: %r" % (len(still_passing),
                                        len(accept_depends) + len(accept_fresh),
                                        still_passing[:3]))
    if not newly_accepted:
        problems.append("none of the %d reject-case(s) changed when the new "
                        "rules were disabled, so an older rule was doing the "
                        "work and the new rule is untested"
                        % (len(reject_depends) + len(reject_fresh)))
    if problems:
        for p in problems:
            print("[FAIL] negative control: %s" % p)
        return 1
    print("[OK] negative control: with the rule off %d accept-case(s) flip to "
          "rejected and %d reject-case(s) flip to accepted, so the test is "
          "sensitive to the new rules."
          % (len(accept_depends) + len(accept_fresh),
             len(newly_accepted)))
    return 0


def negative_control():
    """Turn the new rule OFF and prove the test notices.

    A test that passes whether the rule is there or not proves nothing.
    With script_independent() disabled the measurement cases must go
    back to being REJECTED - that is the old behaviour, and the test
    has to see it.
    """
    original = T.script_independent
    # The cases that DEPEND on the rule: a source the rule calls script
    # independent, in a language whose script check can fail. A Latin
    # target is not one of them - script_ok() always passes there - and
    # neither is the pure-kanji Japanese, which has a rule of its own.
    depends = [(s, v, l, z) for s, v, l, z, e, _ in STORED
               if e and l not in T.LATIN_TARGETS and original(s)]
    T.script_independent = lambda source: False
    try:
        failures = run_cases()
        # With the rule off, those cases must fail. If they still pass,
        # the test is blind to the rule. This has to be measured BEFORE
        # the original function is put back.
        still_passing = [(s, v, l) for s, v, l, z in depends
                          if T.verify_stored(s, v, 0, l, z)]
    finally:
        T.script_independent = original

    problems = []
    if not failures:
        problems.append("nothing changed when the rule was disabled")
    if not depends:
        problems.append("no case depends on the rule")
    if still_passing:
        problems.append("%d of %d rule-dependent cases still passed without "
                        "the rule: %r" % (len(still_passing), len(depends),
                                          still_passing[:3]))
    if problems:
        print("[FAIL] negative control: %s" % "; ".join(problems))
        return 1
    print("[OK] negative control: with the rule off %d case(s) fail and all "
          "%d rule-dependent cases flip, so the test is sensitive to it."
          % (len(failures), len(depends)))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--negative-control", action="store_true",
                    help="prove the test can fail")
    args = ap.parse_args()

    if args.negative_control:
        rc = negative_control()
        if rc:
            return rc
        return negative_control_new_rules()

    failures = run_cases()
    print("cases: %d" % (len(STORED) + len(FRESH)))
    if failures:
        print("[FAIL] %d case(s):" % len(failures))
        for line in failures:
            print("  " + line)
        return 1
    print("[OK] the translation gate accepts the right values and rejects "
          "the wrong ones.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
