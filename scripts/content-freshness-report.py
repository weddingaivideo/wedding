# -*- coding: utf-8 -*-
"""Content ageing board: what needs a real editorial review, and when.

Usage:
    python scripts/content-freshness-report.py            # write the report
    python scripts/content-freshness-report.py --stdout   # also print summary

Deliberately NOT a hard gate: 100+ existing posts are older than 90 days, so
failing the deploy would be noise. Run it weekly (or before a content sprint)
and work the priority list from the top.
"""
import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TODAY = datetime.now(timezone.utc).date()   # same clock CI / sitemaps use
OUT = ROOT / "research" / ("内容老化看板-%s.md" % TODAY.isoformat())


def scan():
    rows = []
    for base, label in ((ROOT / "blog", "blog"), (ROOT / "guides", "guide")):
        if not base.exists():
            continue
        for f in sorted(base.glob("*/index.html")):
            s = f.read_text(encoding="utf-8")
            m = re.search(r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})"', s)
            t = re.search(r"<title[^>]*>([\s\S]*?)</title>", s, re.I)
            title = re.sub("<[^>]+>", "", t.group(1)).strip() if t else ""
            d = datetime.strptime(m.group(1), "%Y-%m-%d").date() if m else None
            rows.append({
                "type": label,
                "slug": f.parent.name,
                "date": d,
                "age": (TODAY - d).days if d else None,
                "title": title,
                "year_in_title": bool(re.search(r"20\d\d", title)),
                "price_in_title": "$" in title,
            })
    return rows


def main():
    rows = scan()
    buckets = defaultdict(list)
    for r in rows:
        if r["age"] is None:
            buckets["no-date"].append(r)
        elif r["age"] <= 30:
            buckets["fresh"].append(r)
        elif r["age"] <= 90:
            buckets["ageing"].append(r)
        else:
            buckets["stale"].append(r)

    priority = [r for r in rows
                if (r["age"] or 9999) > 90 and
                (r["year_in_title"] or r["price_in_title"])]
    priority.sort(key=lambda r: (-(r["age"] or 0), r["slug"]))

    lines = [
        "# 内容老化看板 — %s" % TODAY.isoformat(), "",
        "依据页面 JSON-LD 的 `dateModified`，不是 sitemap lastmod。",
        "`sitemap-<lang>.xml` 的 lastmod 现由 `scripts/sync-sitemap-lastmod.py`",
        "按真实文件变更日期生成，两者应保持一致。", "",
        "## 总览", "",
        "| 分类 | 篇数 | 判定 |", "|---|---:|---|",
        "| 新鲜（≤30 天） | %d | 无需动作 |" % len(buckets["fresh"]),
        "| 进入复核期（31–90 天） | %d | 排期 |" % len(buckets["ageing"]),
        "| 待复核（>90 天） | %d | 需要真实内容更新 |" % len(buckets["stale"]),
        "| 无 dateModified | %d | 补元数据 |" % len(buckets["no-date"]),
        "| 合计 | %d | |" % len(rows), "",
        "## 优先级队列：过期 + 易失效信号", "",
        "标题含年份或价格的页面在跨年、调价后会立刻失真，优先复核。共 %d 篇。" %
        len(priority), "",
        "| 页 | 类型 | 上次修改 | 天数 | 信号 |", "|---|---|---|---:|---|",
    ]
    for r in priority[:60]:
        sig = ",".join(x for x, ok in (("年份", r["year_in_title"]),
                                       ("价格", r["price_in_title"])) if ok)
        lines.append("| `%s` | %s | %s | %d | %s |" %
                     (r["slug"], r["type"],
                      r["date"].isoformat() if r["date"] else "-",
                      r["age"] or 0, sig))
    lines += ["", "## 复核规则", "",
              "1. 只在实际改了事实、数据、截图或结论时更新 `dateModified`；",
              "   不要为了「显得新鲜」刷日期，也不要用 `_refresh_sitemap_lastmod.py` 全量刷。",
              "2. 改动后同步 JSON-LD 的 `dateModified`、11 语词典对应键和分片，",
              "   再跑 `python scripts/sync-sitemap-lastmod.py`。",
              "3. 带年份的标题在每年 12 月统一复核；带价格的标题在调价时全量复核。",
              "4. 复核后如果内容已无检索价值，考虑合并到指南页并 301，而不是删了事。", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("fresh=%d ageing=%d stale=%d no-date=%d priority=%d" %
          (len(buckets["fresh"]), len(buckets["ageing"]), len(buckets["stale"]),
           len(buckets["no-date"]), len(priority)))
    print("report:", OUT)


if __name__ == "__main__":
    main()
