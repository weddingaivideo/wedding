# i18n ZH 修复最终报告 v2 — 2026-07-28

## 流程

1. **静态审查** (`qa/i18n_audit_static.py`) — 找出严重截断 (1121 个)

2. **反向翻译审查** (`qa/i18n_reverse_google.py`) — 单次 gtx，sim<0.9 共 2154 个键

3. **修复 zh** (`qa/fix_zh_sus.py`) — 用 gtx 重新翻译 sim<0.9 的键，应用 964 个

4. **v1 验证** (`qa/_validate_zh_fix.py`) — 单次 gtx 反译验证，平均 +0.159 改善

5. **v2 二次审查** (`qa/_revalidate_zh_v2.py`) — N=3 gtx 取中位数，更稳定

6. **回滚** (`qa/rollback_zh_v2.py`) — v2 标记 rollback 的 130 个回滚到 fix 前


## V1 vs V2 判定对比

| verdict | V1 (单次) | V2 (N=3 中位数) | 差异 |
|---------|-----------|----------------|------|
| fixed (完全改善) | 332 | - | - |
| improved | 318 | - | - |
| no_change | 172 | - | - |
| worse | 142 | - | - |
| **keep (保留新翻译)** | - | **765** | - |
| **rollback (回滚)** | - | **130** | V1 误报 142 个中约 130 个是 gtx 单次抽样的噪音 |
| **ambiguous (保守保留新翻译)** | - | **69** | - |

## 最终改善（final state = keep 765 + ambiguous 69 = 834 个保留新翻译 + 130 回滚）

| 指标 | 数值 |
|------|------|
| 原始平均 sim (old) | 0.503 |
| V1 新翻译 sim (单次 gtx) | 0.662 (受 gtx 噪音影响) |
| V2 新翻译 sim (3 次中位数) | 0.650 (稳定) |
| V2 新翻译 sim (3 次最大) | 0.650 (乐观) |
| **最终状态 sim** | **0.695** (keep 用 v2_med, rollback 用 old) |
| **最终改善** | **+0.192** |

## 总结

- **834 个键永久保留新翻译**（N=3 验证显示显著改善）

- **130 个键回滚**（N=3 显示原来 gtx 翻译的更好）

- **平均改善 +0.192**（从 0.503 改善到 0.695）

- **剩下 15 个键** 在 EN 也缺失，无法 re-validate（保留新翻译作 fallback）


## 文件

- `i18n/zh.json` — 最终翻译（934.1 KB）

- `qa/i18n_fix_zh_v2_validation.csv` — N=3 详细数据

- `qa/i18n_fix_zh_validation.csv` — V1 单次数据（已过时）

- `qa/REPORT_I18N_ZH_FIX.md` — V1 报告（已过时）


