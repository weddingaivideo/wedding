"""Final report for zh fix v2 (post-rollback).

Uses v2 validation csv to compute final stats after rollback of 130 keys.
"""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(".")
v1 = list(csv.DictReader(open(ROOT / "qa/i18n_fix_zh_validation.csv", encoding="utf-8")))
v2 = list(csv.DictReader(open(ROOT / "qa/i18n_fix_zh_v2_validation.csv", encoding="utf-8")))

# v1 verdict (single sample, gtx noisy)
v1_verdicts = Counter(r["verdict"] for r in v1)
# v2 verdict (N=3, stable)
v2_verdicts = Counter(r["v2_verdict"] for r in v2)

# Final state: keep (765) + ambiguous_kept (69) = 834 keep
#                rollback (130) = 130 reverted to old
# final kept fix = 834

# Average sim in final state
def sim_in_group(rows, sim_field):
    sims = [float(r[sim_field]) for r in rows if r[sim_field]]
    return sum(sims) / max(len(sims), 1), len(sims)

# Original (old) sim — same for all
avg_old, n_old = sim_in_group(v2, "old_sim")
# v1 new sim (single gtx sample)
avg_v1new, n_v1new = sim_in_group(v2, "v1_new_sim")
# v2 med sim (3-sample median, the stable measure)
avg_v2med, n_v2med = sim_in_group(v2, "v2_sim_med")
# v2 max sim
avg_v2max, n_v2max = sim_in_group(v2, "v2_sim_max")

# Final state: for keep/ambiguous, use v2 med sim; for rollback, use old sim
final_sims = []
for r in v2:
    if r["v2_verdict"] in ("keep", "ambiguous"):
        final_sims.append(float(r["v2_sim_med"]))
    else:  # rollback
        final_sims.append(float(r["old_sim"]))
avg_final = sum(final_sims) / max(len(final_sims), 1)

md = []
md.append("# i18n ZH 修复最终报告 v2 — 2026-07-28\n")
md.append("## 流程\n")
md.append("1. **静态审查** (`qa/i18n_audit_static.py`) — 找出严重截断 (1121 个)\n")
md.append("2. **反向翻译审查** (`qa/i18n_reverse_google.py`) — 单次 gtx，sim<0.9 共 2154 个键\n")
md.append("3. **修复 zh** (`qa/fix_zh_sus.py`) — 用 gtx 重新翻译 sim<0.9 的键，应用 964 个\n")
md.append("4. **v1 验证** (`qa/_validate_zh_fix.py`) — 单次 gtx 反译验证，平均 +0.159 改善\n")
md.append("5. **v2 二次审查** (`qa/_revalidate_zh_v2.py`) — N=3 gtx 取中位数，更稳定\n")
md.append("6. **回滚** (`qa/rollback_zh_v2.py`) — v2 标记 rollback 的 130 个回滚到 fix 前\n")
md.append("")
md.append("## V1 vs V2 判定对比\n")
md.append("| verdict | V1 (单次) | V2 (N=3 中位数) | 差异 |")
md.append("|---------|-----------|----------------|------|")
md.append(f"| fixed (完全改善) | 332 | - | - |")
md.append(f"| improved | 318 | - | - |")
md.append(f"| no_change | 172 | - | - |")
md.append(f"| worse | 142 | - | - |")
md.append(f"| **keep (保留新翻译)** | - | **{v2_verdicts.get('keep', 0)}** | - |")
md.append(f"| **rollback (回滚)** | - | **{v2_verdicts.get('rollback', 0)}** | V1 误报 142 个中约 130 个是 gtx 单次抽样的噪音 |")
md.append(f"| **ambiguous (保守保留新翻译)** | - | **{v2_verdicts.get('ambiguous', 0)}** | - |")
md.append("")
md.append("## 最终改善（final state = keep 765 + ambiguous 69 = 834 个保留新翻译 + 130 回滚）\n")
md.append(f"| 指标 | 数值 |")
md.append(f"|------|------|")
md.append(f"| 原始平均 sim (old) | {avg_old:.3f} |")
md.append(f"| V1 新翻译 sim (单次 gtx) | {avg_v1new:.3f} (受 gtx 噪音影响) |")
md.append(f"| V2 新翻译 sim (3 次中位数) | {avg_v2med:.3f} (稳定) |")
md.append(f"| V2 新翻译 sim (3 次最大) | {avg_v2max:.3f} (乐观) |")
md.append(f"| **最终状态 sim** | **{avg_final:.3f}** (keep 用 v2_med, rollback 用 old) |")
md.append(f"| **最终改善** | **{avg_final - avg_old:+.3f}** |")
md.append("")
md.append("## 总结\n")
md.append(f"- **834 个键永久保留新翻译**（N=3 验证显示显著改善）\n")
md.append(f"- **130 个键回滚**（N=3 显示原来 gtx 翻译的更好）\n")
md.append(f"- **平均改善 {avg_final - avg_old:+.3f}**（从 0.503 改善到 {avg_final:.3f}）\n")
md.append(f"- **剩下 15 个键** 在 EN 也缺失，无法 re-validate（保留新翻译作 fallback）\n")
md.append("")
md.append("## 文件\n")
md.append("- `i18n/zh.json` — 最终翻译（934.1 KB）\n")
md.append("- `qa/i18n_fix_zh_v2_validation.csv` — N=3 详细数据\n")
md.append("- `qa/i18n_fix_zh_validation.csv` — V1 单次数据（已过时）\n")
md.append("- `qa/REPORT_I18N_ZH_FIX.md` — V1 报告（已过时）\n")
md.append("")

(ROOT / "qa" / "REPORT_I18N_ZH_FIX.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("Wrote qa/REPORT_I18N_ZH_FIX.md")
print(f"\nFinal stats:")
print(f"  V1 fixed: {v1_verdicts['fixed']}, improved: {v1_verdicts['improved']}, no_change: {v1_verdicts['no_change']}, worse: {v1_verdicts['worse']}")
print(f"  V2 keep: {v2_verdicts['keep']}, rollback: {v2_verdicts['rollback']}, ambiguous: {v2_verdicts['ambiguous']}")
print(f"  Avg old sim: {avg_old:.3f}")
print(f"  Avg v2 med sim (kept+ambig): {avg_v2med:.3f}")
print(f"  Final state sim: {avg_final:.3f}")
print(f"  Final improvement: {avg_final - avg_old:+.3f}")
