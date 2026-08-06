# weddingai.video — i18n 独立 URL 架构改造

**日期:** 2026-07-27
**部署:** `da194454.weddingai-video.pages.dev` (preview)
**改造:** client-side `?lang=xx` → 独立 URL 路径 `/xx/path`

---

## 🎯 目标

把 i18n 架构从 query-param 切换到独立 URL 路径：

| 之前 | 现在 |
|------|------|
| `/about/?lang=zh` | `/zh/about/` |
| `/order/?lang=ja` | `/ja/order/` |
| 1 个 URL × 10 语 | 10 个 URL × 78 页面 = 780 个独立 URL |

**SEO 收益**：Google 可以独立索引每语版本，hreflang 信号告诉搜索引擎每个 URL 对应哪种语言。

---

## 🔧 实现

### 1. Pages Function（核心）
`functions/_middleware.js` — 拦截 `/xx/path`：

```
请求: /zh/about/
       ↓
匹配 /^\/(en|zh|es|fr|de|pt|ja|ru|ar|th)(\/.*|$)/
       ↓
lang = "zh", rest = "/about/"
       ↓
fetch("https://...pages.dev/about/") 拿原 HTML
       ↓
修改:
  - <html lang="en"> → <html lang="zh" dir="rtl"> (RTL 仅 ar)
  - canonical: /about/ → /zh/about/
  - hreflang: 加 10 语 + x-default
       ↓
返回修改后的 HTML
```

### 2. `_redirects` 备份
```
/en/* /:splat 200
/zh/* /:splat 200
... 10 语
```

如果 function 失败，redirect 仍然 200 重写（让 URL 至少能访问）。

### 3. `js/i18n.js` 改造

**`getLang()` 优先级（新版）**：
1. URL 路径前缀（`/zh/about/` → "zh"）
2. `?lang=xx` query（向后兼容）
3. localStorage
4. `<html lang="...">`

**`setLang(lang)` 改造**：
- 旧：设 `?lang=xx` + reload
- 新：导航到 `/xx/path`（自动剥旧前缀 + 加新前缀）

### 4. HTML hreflang 全量注入
93 个 HTML 全部加上完整 hreflang 块：
- 1 个 canonical
- 10 个 `<link rel="alternate" hreflang="xx">`
- 1 个 `<link rel="alternate" hreflang="x-default">`

---

## ✅ 验证

| URL | 状态 | lang | dir | canonical | hreflangs |
|-----|------|------|-----|-----------|-----------|
| `/` | 200 | en | ltr | `/` | 11 |
| `/zh/` | 200 | zh | ltr | `/zh/` | 11 |
| `/zh/about/` | 200 | zh | ltr | `/zh/about/` | 11 |
| `/ja/` | 200 | ja | ltr | `/ja/` | 11 |
| `/ar/about/` | 200 | ar | **rtl** | `/ar/about/` | 11 |
| `/de/services/personalization/wedding-trailer/` | 200 | de | ltr | `/de/...` | 11 |
| `/ja/blog/01-restore-old-wedding-videos/` | 200 | ja | ltr | `/ja/blog/...` | 11 |
| `/zh/order/` | 200 | zh | ltr | `/zh/order/` | 11 |
| `/about/` | 200 | en | ltr | `/about/` | 11 |

**全部 200，lang/canonical/hreflang 正确。**

---

## 🐛 修复过程踩的坑

| 问题 | 解决 |
|------|------|
| `context.next({ request: newRequest })` 报 "Invalid URL: [object Object]" | CF Pages 不支持在 middleware 里改 request URL。改用 `fetch(underlyingUrl)` 直接读 |
| URL 拼接 `rest + url.search` 给 `new URL()` 当相对 URL 解析失败 | 改用 `url.origin + rest` 绝对 URL |
| 顶层 `.html` + 目录 `index.html` 重复 | `_redirects` 已经 `/about.html → /about/ 308`，不删文件也 OK |

---

## 📊 改动文件

- `functions/_middleware.js` — 新建（37 行）
- `js/i18n.js` — 修改（getLang + setLang）
- `_redirects` — 加 10 行 200 重写
- 93 个 HTML — 加完整 hreflang + canonical
- `qa/test_i18n_v3.py` — 验证脚本

---

## 🚀 部署

- **Latest preview**: https://da194454.weddingai-video.pages.dev
- **新 URL 模式**: `/{lang}/{path}/` （10 语 × 78 页 = 780 独立 URL）
- **缓存**: CF CDN 按 URL 分别缓存各语版本，function 只在 cache miss 跑

---

## ⚠️ 后续待办

1. **删顶层 `*.html`**（about.html, gallery.html, order.html 等）— `_redirects` 已 308，但文件还在 deploy 包里占空间
2. **9 语言 native review** — 翻译表 `i18n/{lang}.json` 已全量 6,532 keys
3. **测试 form submit** — 实际从 `/zh/order/` 提交表单，确认 i18n 不影响 API
4. **生产部署** — 用户确认后 promote 到 weddingai.video
