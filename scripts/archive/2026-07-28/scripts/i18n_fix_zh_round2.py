"""
Targeted ZH fixes — round 2.

Uses EN-value regex to find keys (avoids the 8-char hash suffix problem
from i18n_extract). For each fix, searches the en.json for the matching key
by EN value, then updates the corresponding zh.json entry.

Idempotent.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZH = ROOT / "i18n" / "zh.json"
EN = ROOT / "i18n" / "en.json"

# (key-hint, en-regex, fixed-zh)
# key-hint is just for the human-readable log; the script actually uses the
# en-regex to find the key in en.json (and thus zh.json).
FIXES: list[tuple[str, str, str]] = [
    # ---------- 1) Title truncation: restore "| WeddingAI.video" suffix ----------
    ("about.title_text",
     r"^About Us \| Filmmakers \+ AI Engineers \| WeddingAI\.video$",
     "关于我们 | 电影制作人 + AI 工程师 | WeddingAI.video"),
    ("gallery.title_text",
     r"^Wedding Video Portfolio \| Before/After \| WeddingAI\.video$",
     "婚礼视频作品集 | 前后对比 | WeddingAI.video"),
    ("order.title_text",
     r"^Free Wedding Video Quote \| WeddingAI\.video$",
     "免费婚礼视频报价 | WeddingAI.video"),
    ("resources.title_text",
     r"^Wedding Video Guides & Resources \| WeddingAI\.video$",
     "婚礼视频指南和资源 | WeddingAI.video"),
    ("terms.title_text",
     r"^Terms of Service: Service Terms & Policies \| WeddingAI\.video$",
     "服务条款：服务条款与政策 | WeddingAI.video"),
    ("services.title_text",
     r"^All Wedding Video Services \| WeddingAI\.video$",
     "所有婚礼视频服务 | WeddingAI.video"),
    ("celebrity-message.title_text",
     r"^Celebrity Wedding Messages .*\| WeddingAI\.video$",
     "名人风格婚礼致辞 — AI 生成 | WeddingAI.video"),
    ("family-tribute.title_text",
     r"^Honor a Loved One in Your Wedding Video \| WeddingAI\.video$",
     "在您的婚礼视频中向挚爱致敬 | WeddingAI.video"),
    ("meme-generator.title_text",
     r"^Wedding GIFs & Memes: Share the Joy \| WeddingAI\.video$",
     "婚礼 GIF 与表情包：分享喜悦 | WeddingAI.video"),
    ("family-message.title_text",
     r"^Family Wedding Messages . Seamlessly Integrated$",
     "家人婚礼致辞 — 视频中无缝融入"),

    # ---------- 2) Over-summarized blog titles ----------
    ("blog.03 title",
     r"^AI Wedding Video Generator: Photos to Cinematic Film$",
     "AI 婚礼视频生成器：照片到电影级影片"),
    ("blog.06 title",
     r"^Honor a Deceased Parent at Your Wedding: Video Tributes$",
     "在婚礼上纪念已故的亲人：视频致敬"),
    ("blog.07 title (EN truncated at slug boundary)",
     r"^Create a Cinematic Wedding Trailer: What Videographers$",
     "制作电影级婚礼预告片：摄像师绝不会告诉你的事"),
    ("blog.08 title",
     r"^Pet Wedding Videos: The Trend Taking Over Social Media$",
     "宠物婚礼视频：席卷社交媒体的潮流"),
    ("blog.12 title",
     r"^Wedding Video Formats: What to Ask Your Videographer$",
     "婚礼视频格式：向摄像师该问什么"),
    ("blog.13 title",
     r"^How Long Should a Wedding Video Be\? Expert Guide$",
     "婚礼视频应该多长？专家指南"),
    ("blog.21 title (capital With)",
     r"^How to Restore Old Black and White Wedding Photos With AI$",
     "如何用 AI 恢复老旧黑白婚纱照"),
    ("blog.28 title",
     r"^Holiday Wedding Video: Capture the Magic of Christmas$",
     "节日婚礼视频：捕捉圣诞节的魔力"),
    ("blog.30 title",
     r"^What to Do With Your Wedding Video After the Big Day$",
     "大喜之后如何处理您的婚礼视频"),
    ("blog.36 title",
     r"^How to Digitize Your Parents' Wedding Video: Step-by-Step Guide$",
     "如何将父母的婚礼视频数字化：分步指南"),
    ("blog.38 title",
     r"^How to Create a Wedding Photo Slideshow That Doesn't Bore Everyone$",
     "如何制作不让所有人无聊的婚礼照片幻灯片"),
    ("blog.39 title (EN truncated at slug boundary)",
     r"^How to Add Subtitles to Your Wedding Video for$",
     "如何为多语言家庭的婚礼视频添加字幕"),
    ("blog.40 title (EN truncated at slug boundary)",
     r"^How to Turn Your Wedding Photos Into a Cartoon or Animation$",
     "如何将您的婚纱照变成卡通或动画视频"),
    ("blog.43 title",
     r"^How to Remove Background Noise From Wedding Video Audio$",
     "如何消除婚礼视频音频中的背景噪音"),
    ("blog.46 title",
     r"^WeddingAI\.video vs Traditional Wedding Videography$",
     "WeddingAI.video vs 传统婚礼摄像"),

    # ---------- 3) Polysemous mistranslations ----------
    ("blog.01 step 1",
     r"^Step 1: Assess the Physical Condition$",
     "步骤一：评估磁带物理状态"),

    # ---------- 4) Person name formatting: missing middle dot ----------
    ("about.h3_text.maria_santos",
     r"^Maria Santos$",
     "玛丽亚·桑托斯"),
]


def main() -> int:
    if not ZH.exists() or not EN.exists():
        print(f"Missing {ZH} or {EN}", file=sys.stderr)
        return 1
    en = json.loads(EN.read_text(encoding="utf-8"))
    zh = json.loads(ZH.read_text(encoding="utf-8"))

    # Build reverse index: en_value -> key
    en_value_to_key: dict[str, str] = {}
    for k, v in en.items():
        en_value_to_key.setdefault(v, k)

    applied = 0
    skipped = 0
    noop = 0
    for hint, en_pattern, new_zh in FIXES:
        # Find all EN values matching the regex
        matched_keys = []
        for v_en, k in en_value_to_key.items():
            if re.match(en_pattern, v_en):
                matched_keys.append((k, v_en))
        if not matched_keys:
            print(f"  SKIP no-en-match  [{hint}]")
            skipped += 1
            continue
        if len(matched_keys) > 1:
            print(f"  WARN multi-match  [{hint}] -> {[k[:60] for k, _ in matched_keys]}")
        # Use first match
        k_to_fix, v_en = matched_keys[0]
        if k_to_fix not in zh:
            print(f"  SKIP no-zh-key    [{hint}] -> {k_to_fix[:60]}")
            skipped += 1
            continue
        old_zh = zh[k_to_fix]
        if old_zh == new_zh:
            print(f"  NO-OP             [{hint}]")
            noop += 1
            continue
        zh[k_to_fix] = new_zh
        print(f"  FIX               [{hint}]")
        print(f"    key: {k_to_fix[:70]}")
        print(f"    en:  {v_en[:60]!r}")
        print(f"    zh:  {old_zh!r} -> {new_zh!r}")
        applied += 1

    # Atomic write
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
