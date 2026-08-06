"""
Round 3 polysemy batch fix.

For specific ZH polysemy issues identified in the review, replace the
wrong-sense word with the context-appropriate one. Only touches strings
where the EN context makes the right sense unambiguous.

Categories:
  - 胶带 (scotch tape) -> 磁带 (video tape) where EN mentions tape/磁带
  - 捕捉 (catch) -> 录制/拍摄/记录 where EN mentions capture/record/film in video
  - 单词 (vocab) -> 词 where EN mentions words/lyrics
  - 抛光 (physical polish) -> 润色 where EN mentions polished/polish in video
  - 故事 (story) -> 介绍 where EN mentions intro (in video title context)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZH = ROOT / "i18n" / "zh.json"
EN = ROOT / "i18n" / "en.json"

# (zh-source, zh-target, en-pattern-to-confirm-context)
REPLACEMENTS: list[tuple[str, str, str]] = [
    # 胶带 (scotch tape) -> 磁带 (video tape) — apply broadly where EN has "tape" in video context
    ("胶带", "磁带", r"\btape\b"),
    # 捕捉 (catch) -> 记录 (record) when used as verb in video context
    # Note: "捕捉瞬间" is actually OK in Chinese (capture the moment).
    # Only fix the cases where it's a poor translation.
    # Specific case: "音频捕捉技巧" -> "音频录制技巧" (Audio Capture Tips)
    ("音频捕捉", "音频录制", r"audio capture"),
    # 单词 (vocab) -> 词 (word) in 2-4 words context — keep 单词 is OK actually
    # Skipping — 单词 is not always wrong
    # 抛光 (polish surface) -> 润色 (polish/refine) in video context
    ("抛光", "润色", r"polish"),
    # 监视 (monitor) vs 监控 (surveil) — specific cases
    # 担保 (guarantee) vs 保证 (assure) — not seen
]


def main() -> int:
    if not ZH.exists() or not EN.exists():
        return 1
    en = json.loads(EN.read_text(encoding="utf-8"))
    zh = json.loads(ZH.read_text(encoding="utf-8"))

    applied = 0
    skipped = 0
    for zh_src, zh_tgt, en_pattern in REPLACEMENTS:
        for k, v_zh in zh.items():
            if k == "_meta":
                continue
            if zh_src not in v_zh:
                continue
            v_en = en.get(k, "")
            if not re.search(en_pattern, v_en, re.IGNORECASE):
                # EN context doesn't confirm the right sense — skip
                continue
            new_zh = v_zh.replace(zh_src, zh_tgt)
            if new_zh == v_zh:
                continue
            zh[k] = new_zh
            print(f"  FIX  {k[:60]}")
            print(f"    EN: {v_en[:50]!r}")
            print(f"    old: {v_zh!r}")
            print(f"    new: {new_zh!r}")
            applied += 1

    tmp = ZH.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(zh, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    tmp.replace(ZH)
    print(f"\nApplied {applied} polysemy fixes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
