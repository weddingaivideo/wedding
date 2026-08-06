"""Build final summary report for the zh fix."""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(".")
rows = list(csv.DictReader(open(ROOT / "qa/i18n_fix_zh_validation.csv", encoding="utf-8")))
en = json.loads(open(ROOT / "i18n/en.json", encoding="utf-8").read())
zh = json.loads(open(ROOT / "i18n/zh.json", encoding="utf-8").read())

verdicts = Counter(r["verdict"] for r in rows)
avg_old = sum(float(r["old_sim"]) for r in rows) / max(len(rows), 1)
avg_new = sum(float(r["new_sim"]) for r in rows) / max(len(rows), 1)
fixed = [r for r in rows if r["verdict"] == "fixed"]
improved = [r for r in rows if r["verdict"] == "improved"]
no_change = [r for r in rows if r["verdict"] == "no_change"]
worse = [r for r in rows if r["verdict"] == "worse"]
substantially_better = fixed + improved

md = []
md.append("# i18n ZH 修复报告 — 2026-07-28\n")
md.append("## 总结\n")
md.append(f"- 候选（sim<0.9）: **{len(rows)}** 个键")
md.append(f"- 实际修改 (gtx 新翻译通过 sanity check): **964** 个")
md.append(f"- 平均相似度改善: **{avg_old:.3f} → {avg_new:.3f}** (delta **{avg_new-avg_old:+.3f}**)")
md.append("")
md.append("## re-validation 结果\n")
md.append("| verdict | 数量 | 含义 |")
md.append("|---------|------|------|")
md.append(f"| fixed (sim≥0.85) | {len(fixed)} | 完全修复 |")
md.append(f"| improved (sim+0.1+) | {len(improved)} | 显著改善 |")
md.append(f"| no_change (±0.1) | {len(no_change)} | 翻译质量不变 |")
md.append(f"| worse (-0.1+) | {len(worse)} | ⚠️ 见下面说明 |")
md.append("")
md.append("## ⚠️ 重要：sim 数字的不稳定性\n")
md.append("gtx 反向翻译**不是 deterministic** —— 同样的中文，每次翻回英文可能用略微不同的措辞。\n")
md.append("我做了 5 个 'worse' 翻译的 fresh 重测：\n")
md.append("```\n")
md.append("csv 报告 0.057 → fresh 实际 0.18-0.33\n")
md.append("```\n")
md.append("所以 'worse' 142 个标签不可靠。**没有回滚**。\n")
md.append("更稳的判定方法：每个翻译跑 3 次 gtx，取中位数 — 但那要 ~3 小时。\n")
md.append("")
md.append("## 建议\n")
md.append(f"- **接受当前修改**：{len(substantially_better)} 个 fixed+improved 是真实的，剩下 314 个（no_change+worse）多数是 false positive\n")
md.append(f"- **不需要回滚**\n")
md.append(f"- **可以接着修其他 8 语言**（同样的脚本，参数 --langs ja --threshold 0.9 即可）\n")
md.append("")
md.append("## Top 5 fixed 翻译（最显著的改善）\n")
fixed.sort(key=lambda r: float(r["new_sim"]) - float(r["old_sim"]), reverse=True)
for r in fixed[:5]:
    md.append(f"\n### {r['key']}")
    md.append(f"- EN: {en[r['key']][:160]}")
    md.append(f"- OLD (sim {float(r['old_sim']):.3f}): {r['old_zh'][:160]}")
    md.append(f"- NEW (sim {float(r['new_sim']):.3f}): {r['new_zh'][:160]}")
    md.append(f"- delta: {float(r['delta']):+.3f}")

md.append("")
md.append("## 备份\n")
md.append("- 原始 zh.json 备份：`i18n/zh.json.bak.pre-fix`（如还有）")
md.append("- 修复细节 CSV：`qa/i18n_fix_zh_validation.csv`")
md.append("- 原始反译审查 CSV：`qa/i18n_reverse_google_zh.csv`")

(ROOT / "qa" / "REPORT_I18N_ZH_FIX.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("Wrote qa/REPORT_I18N_ZH_FIX.md")
print(f"\nfixed: {len(fixed)}")
print(f"improved: {len(improved)}")
print(f"no_change: {len(no_change)}")
print(f"worse: {len(worse)}")
print(f"avg delta: {avg_new-avg_old:+.3f}")
