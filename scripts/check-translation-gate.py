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
]


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
    print("[OK] negative control: %d of %d rule-dependent cases change when "
          "the rule is disabled, so the test is sensitive to it."
          % (len(failures), len(depends)))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--negative-control", action="store_true",
                    help="prove the test can fail")
    args = ap.parse_args()

    if args.negative_control:
        return negative_control()

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
