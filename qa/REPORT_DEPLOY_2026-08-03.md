# WeddingAI.video 部署报告

**日期:** 2026-08-03  
**部署 URL:** https://085ea7a8.weddingai-video.pages.dev  
**生产域名:** https://weddingai.video  
**部署工具:** Wrangler 4.114.0 (Cloudflare Pages)  
**分支:** main  

---

## 1. 部署摘要

| 项目 | 数值 |
|------|------|
| 上传文件总数 | 4,089 |
| 本次变更文件 | 2 |
| 上传耗时 | 2.35s |
| Pre-deploy 检查 | 0 errors, 1 warning |
| 部署结果 | 成功 |

---

## 2. 资源统计

| 资源类型 | 数量 / 大小 |
|----------|------------|
| HTML 页面 | 527 |
| 图片资源 | 1,472 |
| CSS (styles.min.css) | 36,440 bytes |
| JS (main.min.js) | 4,411 bytes |
| Critical CSS (内联) | 4,459 bytes |
| Cloudflare Functions | 6 endpoints |

---

## 3. i18n 多语言统计

### 3.1 各语言翻译覆盖率

| 语言 | Key 数量 | JSON 大小 (KB) | 覆盖率 vs EN | 
|------|---------|----------------|-------------|
| **en** (English) | 15,232 | 2,658 | 基准 |
| **zh** (中文) | 17,136 | 2,409 | 112.5% |
| **es** (Español) | 16,505 | 2,960 | 108.4% |
| **pt** (Português) | 16,285 | 2,827 | 106.9% |
| **de** (Deutsch) | 16,035 | 2,760 | 105.3% |
| **fr** (Français) | 15,731 | 2,890 | 103.3% |
| **ja** (日本語) | 15,302 | 2,675 | 100.5% |
| **th** (ไทย) | 15,197 | 3,818 | 99.8% |
| **ar** (العربية) | 14,844 | 2,782 | 97.5% |
| **ru** (Русский) | 8,731 | 2,148 | 57.3% |

> 注：部分语言 key 数多于 EN 是因为 blog 翻译页面引入了额外的 h2/h3/li 结构键。

### 3.2 Key 分布（按页面模块，以 EN 为基准）

| 模块 | Key 数 |
|------|--------|
| blog | 14,141 |
| services | 428 |
| resources | 174 |
| gallery | 125 |
| index (首页) | 73 |
| privacy | 64 |
| terms | 57 |
| order | 44 |
| about | 41 |
| search | 35 |
| 404 | 32 |
| success | 17 |
| pricing | 1 |
| **合计** | **15,232** |

### 3.3 Sitemap 统计

| 语言 | Sitemap 文件 |
|------|-------------|
| en | sitemap-en.xml |
| zh | sitemap-zh.xml |
| es | sitemap-es.xml |
| fr | sitemap-fr.xml |
| de | sitemap-de.xml |
| pt | sitemap-pt.xml |
| ja | sitemap-ja.xml |
| ru | sitemap-ru.xml |
| ar | sitemap-ar.xml |
| th | sitemap-th.xml |

- 唯一页面数：523
- 总 URL 数：523 × 10 语言 = 5,230
- Sitemap 索引：sitemap.xml (1.4 KB)

---

## 4. Pre-deploy 检查详情

| 检查项 | 状态 |
|--------|------|
| HTML `<title>` 标签完整性 (610 文件) | PASS |
| CSP nonce 占位符 (525 文件) | PASS |
| Service 页面图片路径 | PASS |
| srcset / picture 标签规范 | PASS |
| CSS 空规则 / 括号匹配 | PASS |
| 关键文件存在性 (10 项) | PASS |
| 死链接检查 (Privacy/Terms) | PASS |
| Google Analytics 4 (607/610 页) | WARN |
| 页面与资源计数 | PASS (611 HTML, 969 图片) |
| SEO title/description 长度 (535 页) | PASS |
| Cloudflare Functions (6 endpoints) | PASS |
| Blog 301 重定向保留 | PASS (173天剩余) |

---

## 5. 已知问题

| 问题 | 严重程度 | 说明 |
|------|---------|------|
| GA4 覆盖不完整 | 低 | 607/610 页面含 GA4，3 个页面缺失 |
| ru 翻译覆盖率低 | 中 | 仅 57.3% 覆盖率，8,731 keys vs 15,232 |
| Blog 多语言 key 碎片化 | 低 | blog 页面存在语言目录下的独立 HTML key，不在根 JSON 中 |
| IndexNow 通知失败 | 低 | 403 - key 文件尚未被 CDN 缓存（通常几分钟后自动恢复） |

---

## 6. 本次修复

- **修复 critical CSS 嵌套 @media bug**：`inject-critical-css.py` 中的正则表达式导致 `@media (max-width:768px)` 块被深度嵌套。改用括号计数法正确解析 minified CSS，页面布局恢复正常。
