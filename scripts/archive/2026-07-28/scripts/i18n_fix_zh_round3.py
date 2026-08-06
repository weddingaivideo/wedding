"""
Targeted ZH fixes — round 3.

Three categories of fixes:
  1) Step number formatting: normalize to "第 N 步" (Arabic) — the dominant
     pattern (40 keys). 10 keys still use "第二步" / "步骤一" — fix to "第 2 步".
  2) Specific mistranslations identified during the round-3 review:
     - "胶带" (scotch tape) → "磁带" (video tape) in digitize context
     - "单词" (vocabulary word) → "词句" (words/lyrics) in memorial context
     - "审查" (audit) → "审看" (review) in video context
     - "捕捉" (catch) → "录制" (record) in video context
     - "抛光" (polish surface) → "润色" (polish/refine) in video context
  3) Brand/trademark consistency: keep as English.

Sister to: i18n_fix_critical.py (round 1) and i18n_fix_zh_round2.py
(round 2 — title truncation).

Idempotent.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZH = ROOT / "i18n" / "zh.json"
EN = ROOT / "i18n" / "en.json"

# Each entry: (en-regex, fixed-zh)
# The script finds the key by EN-value regex match.
FIXES: list[tuple[str, str]] = [
    # ---------- 1) Step number normalization (10 keys) ----------
    ("^Step 1: Assess the Physical Condition$", "第 1 步：评估磁带物理状态"),
    ("^Step 2: Choose Your Style$", "第 2 步：选择您的风格"),
    ("^Step 4: Let AI Work Its Magic$", "第 4 步：让人工智能施展魔法"),
    ("^Step 2: Arrange Your Story$", "第 2 步：编排您的故事"),
    ("^Step 2: Choose Your Tribute Style$", "第 2 步：选择您的致敬风格"),
    ("^Step 4: Decide on Length and Timing$", "第 4 步：确定长度与时机"),
    ("^Step 5: Production and Display$", "第 5 步：制作与展示"),
    ("^Step 5: Export Correctly$", "第 5 步：正确导出"),
    ("^Step 4: Present It Meaningfully$", "第 4 步：富有意义地呈现"),
    ("^Step 5: Polish and Export$", "第 5 步：润色与导出"),
    ("^Step 2: Look at the style, not the brand$", "第 2 步：看风格而非品牌"),
    ("^Step 6: Write a Captivating Caption$", "第 6 步：撰写引人入胜的文案"),

    # ---------- 2) Specific mistranslations ----------
    # blog.36 step 2: Prepare the Tape — "胶带" (scotch tape) -> "磁带" (video tape)
    ("^Step 2: Prepare the Tape$", "第 2 步：准备磁带"),
    # blog.36 step 3: Capture the Video — "捕捉" (catch) -> "录制" (record)
    ("^Step 3: Capture the Video$", "第 3 步：录制视频"),
    # blog.36 step 4: Review and Enhance — "审查" (audit) -> "审看" (review)
    ("^Step 4: Review and Enhance$", "第 4 步：审看与增强"),
    # blog.06 step 3: Write or Select Words — "单词" (vocab) -> "词句" (lyrics/words)
    ("^Step 3: Write or Select Words$", "第 3 步：撰写或选定词句"),
]


def main() -> int:
    if not ZH.exists() or not EN.exists():
        print("Missing zh.json or en.json", file=sys.stderr)
        return 1
    en = json.loads(EN.read_text(encoding="utf-8"))
    zh = json.loads(ZH.read_text(encoding="utf-8"))

    en_value_to_key: dict[str, str] = {}
    for k, v in en.items():
        en_value_to_key.setdefault(v, k)

    applied = 0
    noop = 0
    skipped = 0
    for en_pattern, new_zh in FIXES:
        matched = [(k, v) for v, k in en_value_to_key.items() if re.match(en_pattern, v)]
        if not matched:
            print(f"  SKIP no-en-match  {en_pattern!r}")
            skipped += 1
            continue
        if len(matched) > 1:
            print(f"  WARN multi-match  {en_pattern!r} -> {[k[:60] for k, _ in matched]}")
        k, v_en = matched[0]
        if k not in zh:
            print(f"  SKIP no-zh-key    {k[:60]}")
            skipped += 1
            continue
        old_zh = zh[k]
        if old_zh == new_zh:
            print(f"  NO-OP             {k[:60]}")
            noop += 1
            continue
        zh[k] = new_zh
        print(f"  FIX  {k[:60]}")
        print(f"    en:  {v_en!r}")
        print(f"    old: {old_zh!r}")
        print(f"    new: {new_zh!r}")
        applied += 1

    tmp = ZH.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(zh, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    tmp.replace(ZH)
    print(f"\nApplied {applied} fixes, {noop} no-op, {skipped} skipped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
