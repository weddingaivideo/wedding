#!/usr/bin/env python3
"""Post-launch demand verification + search-performance reconciliation.

Produces one Markdown report from three inputs:
  1. a live retry of the Google Trends API (the original research hit 429),
  2. the verified citation set now shipped on the tool pages,
  3. an optional Google Search Console CSV export.

Usage:
  python scripts/post-launch-review.py
  python scripts/post-launch-review.py --gsc ~/Downloads/Pages.csv --days 28

With --gsc the report contains real per-tool impressions / clicks / position
and compares them with the monthly estimates in
research/欧美免费工具需求研究-2026-11-10.md. Without it, the report states
exactly what data is still needed and gives the export steps. No credentials
are stored in this repo.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "research"
LANGS = ["zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
SLUGS = [
    "wedding-checklist-generator", "wedding-alcohol-calculator",
    "wedding-vow-writer", "wedding-speech-writer",
    "wedding-guest-count-calculator", "wedding-day-timeline-generator",
    "wedding-gift-calculator", "name-change-checklist",
    "wedding-thank-you-note-generator", "wedding-cake-serving-calculator",
    "wedding-dress-code-decoder", "wedding-vendor-tipping-calculator",
    "wedding-countdown-widget", "wedding-vendor-questions-checklist",
]
# Monthly US search volume estimates, from section four of the research doc.
ESTIMATE = {
    "wedding-checklist-generator": 40000, "wedding-guest-count-calculator": 8000,
    "wedding-speech-writer": 12000, "wedding-vow-writer": 13000,
    "wedding-alcohol-calculator": 6000, "wedding-cake-serving-calculator": 2000,
    "wedding-day-timeline-generator": 5000, "wedding-gift-calculator": 4000,
    "wedding-thank-you-note-generator": 3000, "name-change-checklist": 5000,
    "wedding-vendor-tipping-calculator": 4000, "wedding-countdown-widget": 5000,
    "wedding-vendor-questions-checklist": 4000, "wedding-dress-code-decoder": None,
}
COLS = {
    "page": {"page", "pages", "top pages", "url", "页面", "网址"},
    "clicks": {"clicks", "点击次数", "点击量"},
    "impressions": {"impressions", "展示次数", "曝光量"},
    "ctr": {"ctr", "点击率"},
    "position": {"position", "average position", "排名", "平均排名"},
}


def probe_trends() -> tuple[str, str]:
    req = {"comparisonItem": [{"keyword": "wedding checklist", "geo": "US",
                               "time": "today 12-m"}], "category": 0, "property": ""}
    url = "https://trends.google.com/trends/api/explore?" + urllib.parse.urlencode(
        {"hl": "en-US", "tz": "0", "req": json.dumps(req, separators=(",", ":"))})
    try:
        r = urllib.request.urlopen(urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.9"}),
            timeout=15)
        body = r.read(200).decode("utf-8", "replace")
        return str(r.status), body[:120].replace("\n", " ")
    except Exception as exc:  # noqa: BLE001
        return getattr(exc, "code", type(exc).__name__).__str__(), str(exc)[:120]


def citation_count() -> int:
    src = (ROOT / "scripts" / "add-tool-extras.py").read_text(encoding="utf-8")
    return len(re.findall(r'^\s+\("', src, re.M))


def parse_gsc(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise SystemExit("[FAIL] empty CSV")
    names = {k.lower().strip(): k for k in rows[0]}
    def column(cands):
        for c in cands:
            if c in names:
                return names[c]
        return None
    page_c = column(COLS["page"])
    if not page_c:
        raise SystemExit("[FAIL] no page/URL column found; headers=%s" % list(rows[0])[:8])
    clicks_c, imp_c, pos_c = column(COLS["clicks"]), column(COLS["impressions"]), column(COLS["position"])

    def num(v):
        try:
            return float(str(v).replace(",", "").replace("%", "").strip() or 0)
        except ValueError:
            return 0.0

    by_tool = defaultdict(lambda: {"clicks": 0.0, "impr": 0.0, "pos": 0.0, "n": 0})
    by_lang = defaultdict(lambda: {"clicks": 0.0, "impr": 0.0})
    for row in rows:
        url = str(row.get(page_c, ""))
        path_part = re.sub(r"^https?://[^/]+", "", url).strip("/")
        parts = path_part.split("/")
        lang = parts[0] if parts and parts[0] in LANGS else "en"
        rest = parts[1:] if lang != "en" else parts
        slug = next((p for p in rest if p in SLUGS), None)
        clicks, impr, pos = num(row.get(clicks_c, 0)), num(row.get(imp_c, 0)), num(row.get(pos_c, 0))
        by_lang[lang]["clicks"] += clicks
        by_lang[lang]["impr"] += impr
        if not slug:
            continue
        b = by_tool[slug]
        b["clicks"] += clicks
        b["impr"] += impr
        b["pos"] += pos * impr
        b["n"] += 1
    return by_tool, by_lang, len(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gsc", type=Path, help="Google Search Console CSV export (Pages report)")
    ap.add_argument("--days", type=int, default=28, help="length of the export window, for context")
    ap.add_argument("--out", type=Path, help="output markdown path")
    args = ap.parse_args()

    today = dt.date.today().isoformat()
    out = args.out or REPORT / ("上线后验证与效果回收-%s.md" % today)
    status, detail = probe_trends()

    L = [
        "# 免费工具：上线后验证与搜索表现回收", "",
        "生成时间：%s ｜ 数据源：Google Trends 直连探测 / 站内已核实引用 / GSC 导出" % today, "",
        "## 一、需求验证复核", "",
        "- **Google Trends 直连**：本次复测返回 `%s`（%s）。研究阶段亦为 429 且页面依赖 JS 渲染，"
        "因此**直接验证仍未打通**，结论继续依赖四路间接验证：公开搜索量、竞品密度、权威文化统计、行业媒体覆盖。" % (status, detail),
        "- **站内引用已补强**：新增 %d 条经检索核实的权威来源（The Knot / Zola / Wilton / SSA / USA.gov / Brides），"
        "分布在原先没有可见引用的 6 个工具页，见 `scripts/add-tool-extras.py` 的 `SOURCES`。" % citation_count(),
        "- **建议的替代直连**：Search Console 的「查询」报表比 Trends 更适合本场景——它给出本站真实曝光词与点击，"
        "而非相对兴趣指数；本报告第二节即为该数据的落地格式。", "",
        "## 二、上线后搜索表现", "",
    ]
    if not args.gsc:
        L += [
            "> ⚠️ 目前**尚无真实效果数据**。下面的表格是待回填模板，不是测量结果。", "",
            "取数步骤（需要站点所有者权限，本仓库不存凭证）：", "",
            "1. 打开 Google Search Console → 选择 `weddingai.video` 资源 → **效果 → 搜索结果 → 页面**。",
            "2. 日期范围选最近 28 天，对比「与上一周期比较」；导出 **CSV（页面）**。",
            "3. 运行 `python scripts/post-launch-review.py --gsc <导出的.csv> --days 28`，"
            "报告会自动按工具与语言聚合，并与研究文档的月搜索量估算对照。", "",
            "| 工具 | 研究文档月搜索量估算 | 曝光 | 点击 | CTR | 平均排名 |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        L += ["| `%s` | %s | 待回填 | 待回填 | 待回填 | 待回填 |"
              % (s, ESTIMATE[s] or "—") for s in SLUGS]
        L += ["", "另需回填：14 工具 × 10 语言 = 140 个本地化页的收录率（`site:` 或 GSC 页面过滤 `/<lang>/tools/`）。"]
    else:
        by_tool, by_lang, rows = parse_gsc(args.gsc)
        L += [
            "数据源：`%s`（%d 行，窗口 %d 天）。" % (args.gsc.name, rows, args.days), "",
            "| 工具 | 研究文档月搜索量估算 | 曝光 | 点击 | CTR | 平均排名 |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for s in SLUGS:
            b = by_tool.get(s)
            if not b:
                L.append("| `%s` | %s | 0 | 0 | — | — |" % (s, ESTIMATE[s] or "—"))
                continue
            ctr = (b["clicks"] / b["impr"] * 100) if b["impr"] else 0
            pos = (b["pos"] / b["impr"]) if b["impr"] else 0
            L.append("| `%s` | %s | %d | %d | %.2f%% | %.1f |"
                     % (s, ESTIMATE[s] or "—", b["impr"], b["clicks"], ctr, pos))
        L += ["", "### 按语言", "", "| 语言 | 曝光 | 点击 |", "|---|---:|---:|"]
        for lang in ["en"] + LANGS:
            b = by_lang.get(lang, {"impr": 0, "clicks": 0})
            L.append("| %s | %d | %d |" % (lang, b["impr"], b["clicks"]))
        L += ["", "> 估算值来自研究文档的**美国关键词月搜索量**，与 GSC 的**全站实际曝光**口径不同，"
              "仅用于判断量级与优先级，不能直接相除求「达成率」。"]

    L += [
        "", "## 三、复盘口径", "",
        "- 流量最大化看 `wedding-checklist-generator`（研究估算 40k/mo）是否进入曝光前列；",
        "- 主产品转化看 `wedding-vow-writer` / `wedding-speech-writer` 的产出物是否带来回访与视频生成；",
        "- 本地化收益看非 `en` 语言的曝光占比，以及 140 个本地化页的收录率；",
        "- 若某工具曝光高但点击率低，优先改 title / description，而不是改工具逻辑。", "",
        "复跑本脚本即可生成新一期报告；历史报告按日期文件名保留。", "",
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L), encoding="utf-8", newline="\n")
    print("report -> %s" % out.relative_to(ROOT))
    print("trends status: %s | citations: %d | gsc: %s"
          % (status, citation_count(), args.gsc.name if args.gsc else "not supplied"))


if __name__ == "__main__":
    main()
