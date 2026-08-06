"""Build a clean final report with severity buckets and top-issues-per-lang."""
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["zh", "ja", "th", "es", "de", "fr", "pt", "ru", "ar"]
LANG_NAMES = {
    "zh": "Chinese", "ja": "Japanese", "th": "Thai", "es": "Spanish",
    "de": "German", "fr": "French", "pt": "Portuguese", "ru": "Russian",
    "ar": "Arabic",
}

en = json.loads((ROOT / "i18n" / "en.json").read_text(encoding="utf-8"))
EN_KEYS = [k for k in en if k != "_meta"]

md = ["# i18n Translation Audit — 2026-07-28\n",
      "**Auditor:** Mavis (static analysis, no native-speaker review)  ",
      f"**Scope:** 9 non-EN languages × {len(EN_KEYS)} source keys  ",
      "**Translator (declared in `_meta`):** Google Translate (machine) for all 9 langs\n"]

# Severity bucketing
# too_short is a normal trait of ZH/JA/TH/AR/RU (different character density).
# Real issue: when the ratio is < 0.2 on a long EN string -> likely truncated mid-sentence.
SEVERE_TRUNCATION_RATIO = 0.20
SEVERE_TRUNCATION_MIN_EN = 100  # only flag if EN is at least 100 chars

per_lang = {}
for code in LANGS:
    csv_p = ROOT / "qa" / f"i18n_audit_{code}.csv"
    with open(csv_p, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    by_kind = defaultdict(list)
    severe_trunc = []
    for r in rows:
        kind = r["issue"].split("(")[0]
        by_kind[kind].append(r)
        if kind == "too_short" and len(r["en"]) >= SEVERE_TRUNCATION_MIN_EN:
            ratio = len(r["tgt"]) / max(len(r["en"]), 1)
            if ratio < SEVERE_TRUNCATION_RATIO:
                severe_trunc.append((r, ratio))
    per_lang[code] = {
        "all": rows,
        "by_kind": by_kind,
        "severe_trunc": severe_trunc,
    }

md.append("\n## TL;DR — 关键问题\n")
md.append("1. **Google 机器翻译对长文本有内部截断** — 所有 9 个语言都受影响。\n"
          f"   标尺: EN ≥ {SEVERE_TRUNCATION_MIN_EN} 字符 且译文比率 < {SEVERE_TRUNCATION_RATIO:.2f}。\n")
md.append("2. **EN 缺 2 个键** — `_meta` 和 `index.p_text.the_real_time_editing_at_our_reception.87089643`\n"
          "   后者在所有 9 个非EN语言里有完整翻译，但 EN 是 source 反而空。\n")
md.append("3. **覆盖率 100%**（没有 missing 键，没有占位符错位，没有空值）— 但**翻译完整性很差**。\n")
md.append("4. **专有名词处理**：15 个键保持原文（产品名/邮箱），是正确行为。\n")

md.append("\n## 各语言严重截断数（高优先级）\n")
md.append("| lang | name | severe_truncation | total_findings | trunc% |")
md.append("|------|------|-------------------|----------------|--------|")
for code in LANGS:
    p = per_lang[code]
    n_total = len(p["all"])
    n_severe = len(p["severe_trunc"])
    pct = f"{n_severe / n_total * 100:.0f}%" if n_total else "0%"
    md.append(f"| {code} | {LANG_NAMES[code]} | **{n_severe}** | {n_total} | {pct} |")

md.append("\n## 各语言全部 findings 分类\n")
md.append("| lang | missing | untranslated | too_short | en_leak | empty | extra |")
md.append("|------|---------|--------------|-----------|---------|-------|-------|")
for code in LANGS:
    by = per_lang[code]["by_kind"]
    md.append("| " + " | ".join([
        code,
        str(len(by.get("missing", []))),
        str(len(by.get("untranslated", []))),
        str(len(by.get("too_short", []))),
        str(len(by.get("en_token_leak", []))),
        str(len(by.get("empty", []))),
        str(len(by.get("extra_in_target", []))),
    ]) + " |")

md.append("\n## 严重截断的典型例子（每个语言挑 3 个）\n")
for code in LANGS:
    severe = per_lang[code]["severe_trunc"]
    if not severe:
        continue
    md.append(f"\n### {code} ({LANG_NAMES[code]}) — {len(severe)} 个严重截断\n")
    for r, ratio in severe[:3]:
        en_s = r["en"][:160].replace("\n", " ")
        tgt_s = r["tgt"][:160].replace("\n", " ")
        md.append(f"- **`{r['key']}`** (ratio {ratio:.2f})")
        md.append(f"  - EN: {en_s}")
        md.append(f"  - {code.upper()}: {tgt_s}")

# Top 10 untranslated per lang
md.append("\n## 未翻译 (untranslated) — 完整列表\n")
for code in LANGS:
    by = per_lang[code]["by_kind"]
    items = by.get("untranslated", [])
    if not items:
        continue
    md.append(f"\n### {code} ({len(items)} 个)")
    for r in items:
        md.append(f"- `{r['key']}` — `{r['en'][:80]}`")

# Extra-in-target
md.append("\n## 目标语言多出但 EN 没有的键\n")
for code in LANGS:
    by = per_lang[code]["by_kind"]
    items = by.get("extra_in_target", [])
    if not items:
        continue
    md.append(f"\n### {code} ({len(items)} 个)")
    for r in items:
        md.append(f"- `{r['key']}` — `{r['tgt'][:120]}`")

# EN missing
md.append("\n## EN (source) 缺键\n")
md.append("- `_meta` (其他 9 个语言都有)")
md.append("- `index.p_text.the_real_time_editing_at_our_reception.87089643` "
          "— 这是 EN 自己的 bug；其他 9 个语言都有完整翻译")

md.append("\n## 建议下一步（待用户决定）\n")
md.append("**选项 A — 报告到此为止**：你已经看到完整问题清单，自己决定是否投入修复。\n")
md.append("**选项 B — 重译严重截断的键**：用百度翻译 API 重新翻译所有 `severe_truncation` 项。\n"
          f"  - 估算：~{sum(len(per_lang[c]['severe_trunc']) for c in LANGS)} 个键 × 9 语言重译\n"
          "  - 需要：百度翻译 appid（用户给了密钥 `yoUb_...`，但缺 appid）\n")
md.append("**选项 C — 全量重译**：所有 9 语言用百度 API 重新翻译全部 6536 键。\n"
          "  - 估算：~59000 次 API 调用，免费版 QPS=1 约 16 小时\n"
          "  - 风险：覆盖原本就翻译好的 100% 覆盖内容，可能引入新 bug\n")
md.append("**选项 D — 先跑全量反向翻译审查**：用百度 API 把每条翻译翻回英文，对比 EN 原文相似度，\n"
          "  找出真正『语义偏移』或『漏译』的键。这比单纯长度比对更精确。\n"
          "  - 同样需要 appid\n")
md.append("**选项 E — 修 EN 自身的 2 个 bug**：硬编码缺失的 2 个键到 HTML 或 EN 字典。\n")

(ROOT / "qa" / "REPORT_I18N_AUDIT.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("Wrote qa/REPORT_I18N_AUDIT.md")
print(f"Total severe_truncation across 9 langs: {sum(len(per_lang[c]['severe_trunc']) for c in LANGS)}")
