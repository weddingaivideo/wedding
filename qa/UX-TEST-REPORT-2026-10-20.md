# WeddingAI.video — 体验与交互测试报告

| 项目 | 内容 |
|---|---|
| 测试日期 | 2026-10-20 |
| 被测版本 | git `6481a590` (工作区含未提交改动) |
| 被测环境 | 本地 `wrangler pages dev` → `http://127.0.0.1:8788`（与生产同构：`_middleware.js` i18n 重写、CSP nonce、`_redirects`、`_headers` 全部生效） |
| 测试对象 | https://weddingai.video （生产环境另做 6 个 URL 交叉验证） |
| 测试工具 | Python 3.10 + Playwright/Chromium 129 + 自研探针 `qa/ux/` |
| 页面级扫描 | **436** 次页面加载，覆盖 **436** 条记录，11 种语言，2 个视口 |
| 交互断言 | **179** 条 |
| 内链体检 | **171** 个站内目标 |

## 1. 执行摘要

本次以“真实浏览器 + 真实点击”的方式对 WeddingAI.video 做了逐页体验与交互测试，覆盖全部页面类型、11 种语言、移动与桌面视口。交互断言 **78.2% 通过**（140 通过 / 33 失败 / 5 警告 / 1 阻塞）；页面级扫描 **436** 条记录中，**1** 条完全干净、**298** 条仅有可访问性建议、**137** 条存在需要修复的问题（几乎每个页面都被归到“仅有建议”一档，是因为 WCAG 2.2 的 24px 点击热区在全站普遍不达标）。

**总体结论**：内容、路由、站内链接、案例库筛选、博客、表单校验等主干功能都工作正常，语言切换与 11 语言的 URL 结构可用，页面无死链、无未捕获 JS 错误、无坏图、每页恰好一个 H1、图片 alt 覆盖率 100%。但有 **3 个 P0 缺陷会让真实用户“用不了”核心功能**：

1. **手机上打不开主菜单的下半部分** —— 菜单面板固定 999px 高且不可滚动，iPhone SE 上有 9 个入口（含主 CTA「Get a Quote」）永远落在屏幕外；
2. **站内搜索结果点不动** —— 结果链接被拼成 `//services/...`，浏览器会跳到不存在的域名；
3. **13 个免费工具里有 3 个完全不可用** —— CSP 的 `img-src` 漏了 `blob:`，上传的照片无法解码，用户只会看到“Could not decode this file”这种误导性提示。

此外还有 4 个 P1：俄语站整体未翻译（94%–100% 正文是英文）、报价接口在邮件配置缺失时返回 500 裸错误页（用户拿不到参考号）、移动端 30% 以上页面整页横向溢出、2 个工具的上传控件键盘不可达。

### 1.1 缺陷分级统计

| 严重度 | 数量 | 含义 |
|---|---:|---|
| P0 | 3 | 阻断：核心转化路径不可用 |
| P1 | 4 | 严重：主要用户群体受损 |
| P2 | 3 | 中等：明显体验/无障碍缺陷 |
| P3 | 4 | 轻微：细节与一致性问题 |
| P4 | 2 | 提示：优化建议 |
| **合计** | **16** | |

### 1.2 最高优先级问题 Top 5

| # | 缺陷 | 影响面 | 一句话结论 |
|---|---|---|---|
| 1 | UX-001 移动端主菜单高度 999px 且不可滚动：真机上「Get a Quote」等主要入口完全够不到 | 所有手机用户（按视口高度递增，4 款主流机型受影响） | 菜单面板 `overflow-y:visible` + 头部 `position:sticky`，面板底部 227–404px 落在屏幕外且无法滚动到 |
| 2 | UX-002 搜索结果链接全部指向不存在的域名（`//services/...`），搜索链路完全断裂 | 站内搜索的全部 12 条结果 | 模板写成 `href="/${item.url}"`，而 `item.url` 本身已以 `/` 开头，拼成协议相对 URL |
| 3 | UX-003 CSP 的 img-src 未放行 blob:，5 个工具无法解码上传的照片，3 个完全不可用 | 13 个免费工具中的 5 个（compress / crop / remove-background 完全失效，add-text / collage 无法预览） | `fileToImage()` 用 `URL.createObjectURL()` 生成 blob: 图片，被 CSP 拒绝加载后误报“文件无法解码” |
| 4 | UX-004 邮件服务缺 key 时下单接口返回 500 纯文本，用户丢失参考号且看不到成功页 | 报价表单提交链路（转化漏斗最末端） | 同一函数的“其他失败”分支会 303 到 `/success/?status=pending`，唯独缺 key 分支直接 500 |
| 5 | UX-005 俄语站点几乎完全未翻译：12 个关键页 94%–100% 正文仍是英文 | 俄语全部转化页（首页、定价、下单、工具、博客、关于、资源、服务、案例库、成功页） | `i18n/ru.json` 只填充了 7.3% 的键，中间件回落英文，俄语用户看到的是英文站点 |

## 1.3 修复与复测（2026-10-20 当日完成）

报告交付后立即实施了修复，并在同一个本地环境复测。下表是**修复前 → 修复后**的实测对比：

| 缺陷 | 修复方式（涉及文件） | 修复前 | 修复后 | 状态 |
|---|---|---|---|---|
| UX-001 移动端菜单下半部分够不到 | `styles.css` / `styles.min.css` / `index.html` / `ai-wedding-video-generator/index.html` 的 `.main-nav` 移动端规则加 `max-height:calc(100dvh - 72px)` + `overflow-y:auto` + `overscroll-behavior:contain` | 面板 999px 固定、不可滚动；iPhone SE 有 9 个入口不可达 | 5 款真机（SE/S8/12/14PM/iPad mini）**全部通过**：面板内滚动后 20 个入口全部可见，“Get a Quote” CTA 均在视口内 | ✅ 已修复 |
| UX-002 搜索结果链接指向不存在域名 | `search/index.html` 去掉多余斜杠，顺带修好未闭合的 `<li>` | `//services/...` → `http://services/...` | 12 条结果全部解析到本站 `/services/...` | ✅ 已修复 |
| UX-003 CSP 缺 `blob:` 致 3 个工具失效 | `functions/_middleware.js` 的 `img-src` 加 `blob:`、新增 `media-src`；`_headers` 的静态回退 CSP 同步更新 | compress / crop / remove-background 点主按钮必报 “Could not decode this file” | 13 个工具逐个实测：5 个原本被拦截的工具全部解码成功并产出结果 | ✅ 已修复 |
| UX-004 报价接口 500 裸错误页 | `functions/api/quote.js` 缺 key 分支改为 `redirect303(successUrl("pending"))` | `POST /api/quote` → 500 纯文本 | → 成功页（含参考号与提示） | ✅ 已修复 |
| UX-006 移动端横向溢出 | `.comparison-table/.full-pricing-table` 加滚动容器；`[class*=tool-grid] > *` 等加 `min-width:0`；移动端表格兜底规则；全局 `overflow-wrap:break-word`；`styles/tools.css`、座位表与资源页的内联样式 | **42/139** 英文页面溢出，最宽 927px | **1/139**（仅 `/tools/wedding-budget-calculator/` 残留 84px），**无任何回归** | 🟡 基本解决（1 页残留） |
| UX-007 2 个工具上传控件键盘不可达 | `save-the-date-maker` 的 `#photo-zone` 加 `role=button tabindex=0`；`wedding-photo-book-planner` 的隐藏 input 改为视觉隐藏并加 `:focus-within` 样式 | 键盘无法打开文件选择器 | 两页实测 `inputFocusable`/`zoneFocusable` 均为 true | ✅ 已修复 |

**回归扫描（全站 139 个英文 URL，390×844 视口）**

| 指标 | 修复前 | 修复后 |
|---|---:|---:|
| 横向溢出页面 | 42 | 1 |
| 回归（改动后变差的页面） | — | **0** |
| HTTP 非 200 | 0 | 0 |
| 未捕获 JS 异常 | 0 | 0 |
| 图片无法解码 | 0 | 0 |
| H1 数量异常页面 | 0 | 0 |
| 缺少 alt 的图片 | 0 | 0 |

样式表缓存版本已从 `v=3.31` 升到 `v=3.35`（`scripts/bump_cache_version.py`，721 个文件），浏览器与 CDN 都会拿到新样式。

**遗留项**：

1. `/tools/wedding-budget-calculator/` 仍有 84px 横向溢出——该页的 `.bg-tool-grid`（`360px 1fr`）与 `.bg-form-row`（内联 `1fr 100px`）是页面私有布局，全局规则只覆盖了一部分，需要在页面内补 `@media (max-width:768px)` 的降级。
2. `/tools/wedding-photo-book-planner/` 加载时会请求一个不存在的地址 `/tools/wedding-photo-book-planner/'%20+%20photo.url%20+%20'`（404）。该字符串既不在 HTML 源码里也不在 DOM 里，是运行时拼接出来的，不影响功能，属于代码卫生问题。
3. UX-005（俄语未翻译）需要内容层面的 v10 重译，不属于本次前端修复范围。

> 复测提示：`_middleware.js` 有 5 分钟的正文缓存（`getCachedProcessedBody`）。改完 HTML 后立刻复测，需要带一次性 query 参数或等待缓存过期，否则会读到旧正文。

## 2. 测试范围与方法

### 2.1 覆盖范围

| 维度 | 覆盖内容 |
|---|---|
| 页面 | EN 站点地图全部 139 个 URL（首页、定价、下单、成功页、搜索、404、13 个工具、14 个服务页、101 篇博客文章、案例库、关于、资源、AI 生成器落地页、隐私、条款） |
| 语言 | 11 种：ar, de, en, es, fr, hi, ja, pt, ru, th, zh（每语言 15 个页面原型 + 1 篇文章） |
| 视口 | 390×844（iPhone 14）、768×1024（iPad mini）、1440×900（桌面）——全站扫描用移动视口，原型页额外跑桌面，视口专项验证用 5 款真机尺寸 |
| 交互套件 | 全局框架（菜单/Cookie/语言切换/键盘/跳转链接）、导航点击链路、首页 CTA 链路、定价、工具中心、13 个工具页（含逐工具真实照片上传与主按钮执行）、案例库筛选、报价表单全流程、搜索、博客列表与文章、404、多语言（10 种语言 × 7 个原型页） |

### 2.2 判定标准

| 检查项 | 判定阈值 | 依据 |
|---|---|---|
| 移动端横向溢出 | `scrollWidth - clientWidth > 2px` 即失败 | 用户无法左右滚动到正文之外的内容，属于内容丢失 |
| 点击热区 | 最小 24×24 CSS px | WCAG 2.2 AA · 2.5.8 Target Size (Minimum)；行内文本链接按规范豁免 |
| 表单字段标签 | 每个可交互字段必须有 `label[for]` / `aria-label` / 包裹式 label | WCAG 4.1.2 Name, Role, Value |
| 图片替代文本 | 所有 `<img>` 必须有 `alt` | WCAG 1.1.1 Non-text Content |
| 标题结构 | 每页恰好 1 个 `<h1>`，层级不跳级 | WCAG 1.3.1 Info and Relationships |
| 语言标记 | `<html lang>` 与 URL 语言一致，且正文字符构成与语言相符（防止 i18n 失效回落英文） | WCAG 3.1.1 Language of Page |
| 缩放 | viewport 不得 `user-scalable=no`；输入框字号 ≥16px | WCAG 1.4.4 Resize Text（iOS 聚焦自动缩放） |
| 键盘可达 | 上传、菜单、筛选、表单等全部可用 Tab + Enter/Space 完成 | WCAG 2.1.1 Keyboard |

### 2.3 环境与限制（重要）

1. 测试在本地 `wrangler pages dev` 上进行，与生产同构（中间件、CSP、重定向全部生效），但**没有边缘缓存**，因此本地加载耗时不能直接代表线上 Core Web Vitals；页体积为**未压缩**本地值。
2. GA4 / Clarity / 百度统计 / AdSense 等第三方脚本在测试中被拦截，以避免网络波动污染结果；因此本报告的 console 结果只反映第一方代码。
3. Service Worker 被显式禁用，避免上一轮访问的缓存污染结果。
4. 本地 miniflare 运行时在长时间高并发扫描下会崩溃退出（与生产 1102 问题不同源），已用守护进程自动重启 + 扫描器重试规避；崩溃期间的记录已全部重跑，未混入报告。

## 3. 缺陷清单

### P0 级缺陷（3 项）

#### UX-001 · 移动端主菜单高度 999px 且不可滚动：真机上「Get a Quote」等主要入口完全够不到

- **严重度**：P0　**影响页面**：全站（任何页面的汉堡菜单）　**影响面**：所有手机用户（按视口高度递增，4 款主流机型受影响）
- **现象**：390×844 视口下 `.main-nav` 面板 top=72 / bottom=1071（高 999px），而视口只有 844px；`overflow-y: visible`、`scrollHeight == clientHeight`（不可滚动）；页面本身此时也无法滚动（实测 scrollY 恒为 0），面板被 sticky 头部锚定。实测各机型落在屏幕外、无法点击的菜单项：iPhone SE 375×667 → **9 项**（View all services、Gallery、Blog、Resources、Free Tools、About、Pricing、**Get a Quote**、语言切换器）；Galaxy S8 360×740 → 8 项；iPhone 12 390×844 → 5 项（Free Tools、About、Pricing、**Get a Quote**、语言切换器）；iPhone 14 Pro Max 430×932 → 3 项；iPad mini 768×1024 → 1 项（语言切换器）。
- **根因**：`.main-nav` 在移动端展开为绝对定位的全宽面板，但没有 `max-height: 100vh` / `overflow-y: auto`；同时头部是 `position: sticky`，面板随头部固定，页面滚动无法把它带回视口内。面板固定高度 999px 也说明其中的“服务”下拉分组（11 个子项）被强制全部展开。
- **复现步骤**：
  1. 以 375×667（iPhone SE）打开首页
  1. 点击右上角汉堡菜单
  1. 向下看：Gallery / Blog / Resources / Free Tools / About / Pricing / Get a Quote 均在屏幕外
  1. 尝试滚动页面（scrollY 始终为 0）或在面板内滚动（overflow-y: visible）——都无法到达
- **证据**：`qa/ux/nav_probe2.py` 输出（5 种机型实测）；交互断言 `NAV-03`、`NAV-07`
- **修复建议**：给移动端面板加 `max-height: calc(100dvh - 72px); overflow-y: auto; -webkit-overflow-scrolling: touch;`，并把“服务”子菜单改为可折叠（默认收起），使面板高度控制在 ~480px；同时保证语言切换器始终在首屏可见（可放在面板顶部固定区）。

#### UX-002 · 搜索结果链接全部指向不存在的域名（`//services/...`），搜索链路完全断裂

- **严重度**：P0　**影响页面**：`/search/`（任意查询词）　**影响面**：站内搜索的全部 12 条结果
- **现象**：在 `/search/?q=wedding+video` 渲染出 12 条结果，但每条链接的 href 都是双斜杠开头，浏览器解析为协议相对地址：`//services/personalization/ai-video-generator/` → `http://services/personalization/ai-video-generator/`、`//about/` → `http://about/`、`//services/` → `http://services/`……这些主机名不存在，用户点击后会跳到无法解析的地址，站内搜索的价值归零。
- **根因**：`search/index.html:504` 模板字符串 `<a href="/${item.url}">`，而索引数组 `INDEX` 中的 `url` 字段本身已经是 `/services/...` 形式。
- **复现步骤**：
  1. 打开 `/search/?q=wedding+video`
  1. 查看任意结果链接：`a.search-result h3 a` 的 `getAttribute('href')` 为 `//services/...`
  1. 点击后会离开本站
- **证据**：`qa/ux/verify_bugs.py` 输出；源码 `search/index.html:504`；同一段代码还把 `</li>` 写成了 `<li></li>`（无效标签）
- **修复建议**：改为 `<a href="${item.url}">`（去掉多余斜杠），并把 `INDEX` 中的 url 统一成不带前导斜杠或带斜杠的其中一种；同时修正未闭合的 `<li>`。建议把本条纳入 CI：解析搜索结果链接并断言其 origin 与页面一致。

#### UX-003 · CSP 的 img-src 未放行 blob:，5 个工具无法解码上传的照片，3 个完全不可用

- **严重度**：P0　**影响页面**：`/tools/compress-wedding-photos/`、`/tools/crop-wedding-photo-for-reels/`、`/tools/remove-background-wedding-portrait/`、`/tools/add-text-to-wedding-photo/`、`/tools/wedding-photo-collage/`　**影响面**：13 个免费工具中的 5 个（compress / crop / remove-background 完全失效，add-text / collage 无法预览）
- **现象**：上传一张合法 JPEG（1600×1200，668KB，渐进式/EXIF 旋转/PNG/WebP 均试过）：文件列表出现该文件且缩略图元素存在，但 `naturalWidth === 0`（图片被拦截）；点击主按钮后提示 **“Could not decode this file. Try a JPG, PNG, or WebP.”**。3 个工具的主按钮永远不会产出结果（无下载链接、无 blob 输出），另 2 个工具画布停留在默认 300×150。
- **根因**：`functions/_middleware.js:65` 的 CSP 为 `img-src 'self' data: https://hm.baidu.com ...`，**没有 `blob:`**；而 `js/tools/common.js:51 fileToImage()` 正是 `URL.createObjectURL(file)` → `img.src = blob:...`。浏览器拦截后触发 `img.onerror`，被翻译成“文件无法解码”的误导性提示。对照：`wedding-photo-book-planner` 用 `FileReader.readAsDataURL`（`data:` 已被放行）因此正常。
- **复现步骤**：
  1. 打开 `/tools/compress-wedding-photos/`，上传任意 JPG
  1. 缩略图区域空白（`<img src=blob:...>` 的 `naturalWidth=0`）
  1. 点击“Compress” → 状态栏出现 “Could not decode this file. Try a JPG, PNG, or WebP.”
- **证据**：`qa/ux/results/tool-verdicts.json`（13 个工具逐个实测）、`qa/ux/decode_probe.py`、源码 `functions/_middleware.js:65` 与 `js/tools/common.js:51`
- **修复建议**：在 CSP 的 `img-src`（如需处理 canvas 导出的图片预览，同时检查 `media-src`）加入 `blob:`；改完后需复核全部工具。另建议：解码失败时区分“文件损坏”和“被策略拦截”，并把真实原因写进控制台，避免再次出现误导性提示。


### P1 级缺陷（4 项）

#### UX-004 · 邮件服务缺 key 时下单接口返回 500 纯文本，用户丢失参考号且看不到成功页

- **严重度**：P1　**影响页面**：`/order/`（POST `/api/quote`）　**影响面**：报价表单提交链路（转化漏斗最末端）
- **现象**：本地复现：POST `/api/quote` → `500`，响应体为纯文本 “Server is not configured to send email. Please email order@weddingai.video directly.”。浏览器停在 `/api/quote`，既没有跳到 `/success/`，也没有展示前端生成的 `WA-YYYYMMDD-XXXX` 参考号（`#reference-copy` 不会出现），用户只会看到一个裸错误页。
- **根因**：`functions/api/quote.js:327-343`：`if (!apiKey) { … return new Response(..., {status: 500}) }`。而同函数在 Resend 返回非 2xx（第 387 行）与 fetch 抛异常时都会 `redirect303(origin_base, successUrl("pending"))`，前端 `js/main.js` 也已实现 `status=pending` 分支。即前端已准备好降级路径，唯独缺 key 这一分支没走。
- **复现步骤**：
  1. 在未配置 `RESEND_API_KEY` 的环境打开 `/order/`，填写必填项并提交
  1. 页面停在 `/api/quote`，显示纯文本 500
- **证据**：`qa/ux/verify_bugs.py` 的 POST 结果；源码 `functions/api/quote.js:328-343`；对比分支 `quote.js:387`
- **修复建议**：把缺 key 分支也改成 `redirect303(origin_base, successUrl("pending"))`，让用户至少拿到参考号并看到“已收到、24 小时内回复”的页面（lead 已经在 KV 里，不会丢单）；运维侧用 `/api/dead-letters` 或 cron 重试补发。

#### UX-005 · 俄语站点几乎完全未翻译：12 个关键页 94%–100% 正文仍是英文

- **严重度**：P1　**影响页面**：`/ru/`、`/ru/pricing/`、`/ru/order/`、`/ru/blog/`、`/ru/about/`、`/ru/gallery/`、`/ru/resources/`、`/ru/services/`、`/ru/success/`、`/ru/tools/`　**影响面**：俄语全部转化页（首页、定价、下单、工具、博客、关于、资源、服务、案例库、成功页）
- **现象**：浏览器实测 `/ru/blog/` 正文 17,626 个拉丁字符、仅 157 个西里尔字符（latinRatio 0.99）；`/ru/about/`、`/ru/success/` 为 100% 拉丁字符（完全未翻译）；`/ru/pricing/` 0.96、`/ru/order/` 0.94、`/ru/gallery/` 0.98、`/ru/resources/` 0.99、`/ru/services/` 0.96。另有 `/ja/blog/` 100% 拉丁、`/th/gallery/` 100%、`/th/order/` 100%。
- **根因**：`i18n/ru.json` 仅 3,235 / 44,131 个键有值（7.3%），而其余语言均 ≥ 60,000 键。`functions/_middleware.js` 找不到键时直接回落到 HTML 中的英文原文，因此页面能正常打开、不报错，但内容是英文——这正是纯静态扫描工具看不到的失效模式。
- **复现步骤**：
  1. 打开 `http://127.0.0.1:8788/ru/blog/`
  1. 统计 `document.body.innerText` 的字符构成：拉丁 17,626 / 西里尔 157
- **证据**：`qa/ux/results/sweep-archetypes.json` 中 24 条 ru 记录 `langOK=false`；`qa/ux/rootcause.py`：ru 3,235/44,131 键（7.3%），其余语言均 ≥ 60,000
- **修复建议**：① 短期：在语言切换器中暂时下架俄语入口，或对未翻译页面加明显提示，避免用户误以为站点只支持英语；② 按 v10 重译计划补齐 ru 词典；③ 把“实际渲染语言 vs URL 语言”做成 CI 检查（本次探针已实现，可直接复用 `qa/ux/sweep.py` 的 `langOK` 判据）。

#### UX-006 · 移动端横向溢出：42/139 个英文页面 + 11 种语言共 75 条记录出现整页左右滚动

- **严重度**：P1　**影响页面**：`/ai-wedding-video-generator/`、`/tools/*`、`/services/*`、`/pricing/`、`/`、`/gallery/`、`/resources/`、10 篇文章及其多语言版本　**影响面**：全部工具页（13/14）、全部服务页（14/14）、首页、定价、案例库、资源页、AI 生成器落地页
- **现象**：在 390×844（iPhone 14）视口下打开页面，`documentElement.scrollWidth - clientWidth` 大于 2px，整页可以左右拖动，正文与页脚被推到屏幕外。溢出最严重的页面：`/de/ai-wedding-video-generator/` 927px、`/es/ai-wedding-video-generator/` 744px、`/pt/ai-wedding-video-generator/` 743px、`/ai-wedding-video-generator/` 666px、`/tools/wedding-seating-chart-maker/` 592px、`/fr/tools/compress-wedding-photos/` 520px。
- **根因**：三类元素撑破容器：① 对比表格 `.comparison-table`（实测 992–1293px）与定价全表 `.full-pricing-table`（实测 626–886px）只有 `width:100%`，表格的 min-content 宽度会把容器撑开，而外层没有 `overflow-x:auto` 的滚动容器；② `/tools/wedding-seating-chart-maker/` 的 `.seating-panel` / `.seating-layout-wrap` 为 `position:sticky` 的固定宽度布局（958px），在窄屏没有切换为纵向堆叠；③ `/tools/wedding-video-invitation-maker/` 的 `.wa-tool-card` 实测 426px。非英语页面更严重，因为德语/西语/法语译文更长。
- **复现步骤**：
  1. 以 390×844 视口打开 `http://127.0.0.1:8788/ai-wedding-video-generator/`
  1. 执行 `document.documentElement.scrollWidth - document.documentElement.clientWidth`
  1. 观察返回值 666px，并可见横向滚动条
- **证据**：扫描结果 `qa/ux/results/sweep-en.json`：EN 139 页中 42 页溢出；`sweep-archetypes.json`：11 语言 × 15 原型 × 2 视口中 75 条记录溢出；取证截图 `qa/ux/results/shots/overflow-*.png`
- **修复建议**：① 给所有宽表格套一层 `overflow-x:auto` 的滚动容器（或 `table-layout:fixed` + 允许换行）；② 窄屏（≤768px）为 `.seating-layout-wrap` 改为单列、取消 `.seating-panel` 的 sticky；③ `.wa-tool-card` 加 `max-width:100%`；④ 不建议用 `html,body{overflow-x:hidden}` 掩盖问题。

#### UX-007 · 2 个工具的上传控件对键盘与读屏用户完全不可达

- **严重度**：P1　**影响页面**：`/tools/save-the-date-maker/`、`/tools/wedding-photo-book-planner/`（及其 10 个语言版本）　**影响面**：save-the-date-maker、wedding-photo-book-planner
- **现象**：这两个页面的 `#dropzone` 没有 `tabindex`、没有 `role="button"`，同时 `styles/tools.css:62` 的 `.wa-tool-dropzone input[type="file"] { display:none }` 让原生输入既不可聚焦也不被读屏播报；键盘用户 Tab 遍历全页找不到任何能打开文件选择器的控件。（其余 8 个上传类工具已正确设置 `tabindex=0 role=button`，本项只针对这 2 个页面。）
- **根因**：这两个工具的模板没有跟上其余工具的 a11y 修复：拖放区缺少可聚焦语义与键盘事件绑定。
- **复现步骤**：
  1. 打开 `/tools/save-the-date-maker/`
  1. 反复按 Tab，焦点永远到不了上传区
  1. 检查 `#file-input` 计算样式为 `display: none`
- **证据**：交互断言 `TOOL-save-the-date-maker-KBD`、`TOOL-wedding-photo-book-planner-KBD`（FAIL）；CSS `styles/tools.css:62`
- **修复建议**：与其余工具对齐：`<div id="dropzone" role="button" tabindex="0" aria-label="上传照片">` 并绑定 Enter/Space；或用 `<label for="file-input">` 包裹整个拖放区。


### P2 级缺陷（3 项）

#### UX-008 · 全部 139 个英文页面存在小于 24×24px 的点击热区

- **严重度**：P2　**影响页面**：全部页面（139/139 英文页 + 11 种语言页面均命中）　**影响面**：全站（页脚评分徽章、面包屑等），老年用户与运动障碍用户点击困难
- **现象**：`a.footer-badge.footer-badge-secondary` 实测 181×15px（“⭐ 4.9/5 · 9,400+ couples”），面包屑链接 `nav.breadcrumb a` 实测 37×16px。非英语页面最多可达 25 个。
- **根因**：`.footer-badge` 使用较小的字号与紧凑行高，未预留最小点击区域；面包屑通过 `font-size:0.875rem` + 行内排版实现，没有 `padding`/`min-height`。
- **复现步骤**：
  1. 390px 视口打开任意页面
  1. 量取 `.footer-badge` 的 `getBoundingClientRect()`：181×15
- **证据**：扫描探针 `probe.tiny24`，样本见报告第 4 章页面矩阵
- **修复建议**：给这两类元素加 `min-height:24px; min-width:24px; display:inline-flex; align-items:center; padding:4px 8px;`（页脚徽章建议直接提升到 44px）。

#### UX-009 · 5 个语言版本的下单页把非法 `<span>` 写进了 `<select>`，浏览器直接丢弃该节点

- **严重度**：P2　**影响页面**：`/es/order/`、`/ja/order/`、`/pt/order/`、`/ru/order/`、`/th/order/`　**影响面**：西班牙语、日语、葡萄牙语、俄语、泰语的下单页
- **现象**：这 5 个页面的控制台稳定输出 HTML 解析告警，说明响应 HTML 中 `<select>` 内部出现了 `<span>`，浏览器在解析阶段就把它从文档中移除。EN 版本没有该告警，说明是中间件按语言改写 `<select>` 内容时引入的。经运行时复核，4 个 `<select>` 的选项数量与内容仍完整，用户可选，但代码路径存在隐患。
- **根因**：`functions/_middleware.js` 在替换 `<option>`/`<optgroup>` 文本时保留了原 HTML 片段（`<span data-i18n=...>`），只对部分语言生效。
- **复现步骤**：
  1. 打开 `/es/order/`，打开 DevTools Console
  1. 看到 “A span tag was parsed inside of a <select> which was not inserted into the document”
- **证据**：`qa/ux/results/sweep-archetypes.json` consoleErrors，分类统计 29 条，命中 5 个页面
- **修复建议**：中间件改写 `<select>` 内节点时只替换 `option.textContent`，不要回写包含标签的 HTML；并在构建期校验 `select` 的子元素只能是 `option`/`optgroup`。

#### UX-010 · 重型 i18n 页面本地加载超时，提示线上存在 Workers CPU 超限风险

- **严重度**：P2　**影响页面**：`/pt/resources/`、`/th/success/`、`/th/blog/…`、`/hi/tools/`、`/ja/ai-wedding-video-generator/` 等　**影响面**：泰语/印地语/日语/葡萄牙语等重型页面（首页、工具中心、博客、资源、落地页）
- **现象**：扫描中 6 条记录触发 `Page.goto: Timeout 45000ms exceeded`；按语言统计本地 `load > 5s` 的页面占比：zh 28/28、hi 27/27、ar 26/28、th 24/25、ja 26/27，而英文页仅 2/175。
- **根因**：中间件需要为每个非英语页面加载 1MB 级 i18n JSON 并对整页做逐 `data-i18n` 属性替换（`/ar/blog/wedding-video-inspiration/` 单页有 483 个 `data-i18n` 属性）。本地无缓存且单 isolate，等价于线上首次访问的冷启动成本。
- **复现步骤**：
  1. 查看 `qa/ux/results/sweep-archetypes.json` 中 `error` 字段非空的记录
  1. 按语言统计 `probe.load > 5000` 的记录数
- **证据**：语言健康度统计（`qa/ux/lang_report.py`）
- **修复建议**：沿用已有的 `getCachedProcessedBody` 5 分钟 `caches.default` 缓存；把日期多样化等 URL 确定性逻辑移到构建期；或升级 Workers 计划提高 CPU 上限。


### P3 级缺陷（4 项）

#### UX-011 · 两篇博客文章存在重复 DOM id，锚点与目录会指向错误位置

- **严重度**：P3　**影响页面**：上述 2 篇 + `/ru/` 对应版本　**影响面**：`/blog/affordable-wedding-video-ai/`、`/blog/ai-editor-vs-traditional-editing/`（及俄语版）
- **现象**：页面内出现重复 id，读屏软件与 `getElementById` 只会命中第一个，SERP 对比区块的锚点跳转与目录高亮会错位。
- **根因**：文章模板片段被复用/复制时未对 id 加唯一后缀。
- **复现步骤**：
  1. 打开任一受影响页面
  1. 统计所有 `[id]` 出现次数
- **证据**：`probe.dupIds` 字段
- **修复建议**：为该区块 id 加上文章 slug 或计数器后缀；并在构建期加“全站重复 id”门禁。

#### UX-012 · 一个工具页引用被 CSP 拦截的 Google Fonts，控制台报错且字体与其余 12 个工具不一致

- **严重度**：P3　**影响页面**：`/tools/wedding-photo-collage/`　**影响面**：`/tools/wedding-photo-collage/`
- **现象**：控制台：“Refused to load the stylesheet 'https://fonts.googleapis.com/css2?family=Cormorant+Garamond…'”，该页回落到本地字体栈，其余 12 个工具页没有这条外链。
- **根因**：该工具页模板里残留了 Google Fonts `<link>`，而站点 CSP 只允许同源样式（其余页面使用自托管字体）。
- **复现步骤**：
  1. 打开 `/tools/wedding-photo-collage/`
  1. 查看 Console 的 stylesheet 拒绝信息
- **证据**：consoleErrors，仅此 1 页命中
- **修复建议**：删除该页的 Google Fonts `<link>`，改用与其余工具页一致的本地字体变量；或在 CSP 中显式放行 `https://fonts.googleapis.com` 并加 `font-src https://fonts.gstatic.com`。

#### UX-013 · 站内死链：`/blog/elopement-wedding-video-guide/` 在中文博客中被引用但不存在

- **严重度**：P3　**影响页面**：`/blog/elopement-wedding-video-guide/`（被 `/zh/blog/affordable-wedding-video-ai/` 引用）　**影响面**：中文博客文章 `/zh/blog/affordable-wedding-video-ai/`
- **现象**：点击中文博客里的相关推荐会进入 404 页面。
- **根因**：翻译时沿用了旧 slug；`_redirects` 里只有 `/blog/elopement-video-ideas` 的规则，没有 `elopement-wedding-video-guide` 的映射。
- **复现步骤**：
  1. 打开 `/zh/blog/affordable-wedding-video-ai/`
  1. 点击指向 `/blog/elopement-wedding-video-guide/` 的链接
- **证据**：全局内链体检 171 个目标，唯一死链
- **修复建议**：把链接改为 `/blog/elopement-video-ideas/`，或在 `_redirects` 增加 `/blog/elopement-wedding-video-guide/ 301 /blog/elopement-video-ideas/`。

#### UX-014 · `_redirects` 有 36 条非法规则、210 行被跳过，36 条历史链接规则实际未生效

- **严重度**：P3　**影响页面**：`_redirects`（第 677–831 行区段）　**影响面**：旧 URL / 外部链接 / Google 索引中的历史地址
- **现象**：`wrangler pages dev` 启动时输出：`Found 36 invalid redirect rules … Valid status codes are 200, 301, 302, 303, 307, or 308. Got 404.` 以及 `Maximum number of dynamic rules supported is 100. Skipping remaining 210 lines of file.`。另有 `_headers` 中 `/blog/*/*.html` 规则非法（只允许一个通配符）被跳过。
- **根因**：把“强制返回 404 页”误写成重定向规则；同时通配/占位规则数量超过平台上限。
- **复现步骤**：
  1. 启动 `wrangler pages dev`
  1. 读取启动告警
- **证据**：`qa/ux/results/dev-stdout.log` / `dev-stderr.log`
- **修复建议**：需要屏蔽的路径改用 `_redirects` 之外的机制（例如 Pages 404 页面或 Workers 内判断）；把 100 条以内的关键重定向放在文件顶部，其余收敛到 Workers 代码里处理。


### P4 级缺陷（2 项）

#### UX-015 · 成功页引用 Cloudflare 邮件混淆脚本 `/cdn-cgi/…/email-decode.min.js`

- **严重度**：P4　**影响页面**：`/success/`、`/zh/success/` … `/th/success/`　**影响面**：全部 11 个语言版本的 `/success/` 页面
- **现象**：本地 21 条记录出现同源 404 与 “Refused to execute script from …/cdn-cgi/scripts/…/email-decode.min.js”。
- **根因**：邮件地址依赖 Cloudflare Email Address Obfuscation 注入的脚本，本地 miniflare 不提供该路径。
- **复现步骤**：
  1. 打开 `/success/`
  1. 查看 Console 与 Network
- **证据**：`badResponses` 中 21 条同源 404，全部指向同一脚本
- **修复建议**：若线上正常则无需改动（见报告第 8 章生产验证）；否则改为服务端渲染邮箱或使用 `mailto:` 明文。

#### UX-016 · 语言选择器字号 13.3px，iOS 聚焦时会自动放大页面

- **严重度**：P4　**影响页面**：全站　**影响面**：所有页面的 `#wa-lang-select`
- **现象**：实测 `#wa-lang-select` 的 `font-size: 13.3333px`，低于 iOS 建议的 16px；用户在移动端聚焦语言下拉时页面会被放大且需要手动缩回。
- **根因**：`.wa-lang-select` 未设置最小字号。
- **复现步骤**：
  1. iOS Safari 打开任意页面
  1. 点击右上角语言下拉
- **证据**：交互断言 `A11Y-04`（WARN）
- **修复建议**：给 `#wa-lang-select` 设置 `font-size: 16px`（或在移动端断点下不小于 16px）。


## 4. 逐页测试结果

> 判定列含义：`HTTP` 状态码异常 · `JS` 未捕获异常 · `4xx` 同源资源失败 · `溢出` 移动端横向滚动 · `坏图` 图片无法解码 · `重复ID` DOM id 冲突 · `无标签` 表单字段缺标签 · `上传不可达` 文件控件被 CSS 隐藏 · `热区` 存在 <24px 点击目标 · `语言` 语言回落。

### 4.1 首页（1 页，1 通过 / 0 异常）

| 页面 | 状态 | 横向溢出 | console | 坏图 | 无标签字段 | <24px 热区 | 内链数 | 体积(KB) | 判定 |
|---|---|---|---|---|---|---|---:|---:|---|
| `/` | 200 | 0 | 0 | 0 | 0 | 1 | 27 | 11453 | ⚠️ 热区 |

### 4.2 定价（1 页，1 通过 / 0 异常）

| 页面 | 状态 | 横向溢出 | console | 坏图 | 无标签字段 | <24px 热区 | 内链数 | 体积(KB) | 判定 |
|---|---|---|---|---|---|---|---:|---:|---|
| `/pricing/` | 200 | 0 | 0 | 0 | 0 | 1 | 21 | 18 | ⚠️ 热区 |

### 4.3 下单/报价（1 页，1 通过 / 0 异常）

| 页面 | 状态 | 横向溢出 | console | 坏图 | 无标签字段 | <24px 热区 | 内链数 | 体积(KB) | 判定 |
|---|---|---|---|---|---|---|---:|---:|---|
| `/order/` | 200 | 0 | 0 | 0 | 0 | 1 | 21 | 38 | ⚠️ 热区 |

### 4.4 成功页（2 页，0 通过 / 2 异常）

| 页面 | 状态 | 横向溢出 | console | 坏图 | 无标签字段 | <24px 热区 | 内链数 | 体积(KB) | 判定 |
|---|---|---|---|---|---|---|---:|---:|---|
| `/success/` | 200 | 0 | 2 | 0 | 0 | 1 | 21 | 18 | ❌ 4xx |
| `/success/?id=WA-20260101-ABCD` | 200 | 0 | 2 | 0 | 0 | 1 | 21 | 18 | ❌ 4xx |

### 4.5 工具（14 页，9 通过 / 5 异常）

| 页面 | 状态 | 横向溢出 | console | 坏图 | 无标签字段 | <24px 热区 | 内链数 | 体积(KB) | 判定 |
|---|---|---|---|---|---|---|---:|---:|---|
| `/tools/` | 200 | 0 | 0 | 0 | 0 | 1 | 38 | 17 | ⚠️ 热区 |
| `/tools/add-text-to-wedding-photo/` | 200 | 180px | 0 | 0 | 0 | 3 | 30 | 22 | ❌ 溢出 |
| `/tools/compress-wedding-photos/` | 200 | 0 | 0 | 0 | 0 | 3 | 30 | 22 | ⚠️ 上传不可达/热区 |
| `/tools/crop-wedding-photo-for-reels/` | 200 | 0 | 0 | 0 | 0 | 3 | 30 | 22 | ⚠️ 上传不可达/热区 |
| `/tools/heic-to-jpg-wedding-photos/` | 200 | 207px | 0 | 0 | 0 | 3 | 28 | 22 | ❌ 溢出 |
| `/tools/remove-background-wedding-portrait/` | 200 | 0 | 0 | 0 | 0 | 3 | 30 | 22 | ⚠️ 上传不可达/热区 |
| `/tools/save-the-date-maker/` | 200 | 0 | 0 | 0 | 0 | 3 | 31 | 22 | ⚠️ 上传不可达/热区 |
| `/tools/wedding-budget-calculator/` | 200 | 84px | 0 | 0 | 0 | 4 | 35 | 22 | ❌ 溢出 |
| `/tools/wedding-hashtag-generator/` | 200 | 215px | 0 | 0 | 0 | 3 | 32 | 22 | ❌ 溢出 |
| `/tools/wedding-invitation-maker/` | 200 | 201px | 0 | 0 | 0 | 3 | 34 | 22 | ❌ 溢出 |
| `/tools/wedding-photo-book-planner/` | 200 | 0 | 0 | 0 | 0 | 4 | 35 | 22 | ⚠️ 热区 |
| `/tools/wedding-photo-collage/` | 200 | 0 | 1 | 0 | 0 | 3 | 30 | 22 | ⚠️ 上传不可达/热区 |
| `/tools/wedding-seating-chart-maker/` | 200 | 0 | 0 | 0 | 0 | 9 | 35 | 22 | ⚠️ 热区 |
| `/tools/wedding-video-invitation-maker/` | 200 | 0 | 0 | 0 | 0 | 3 | 33 | 22 | ⚠️ 上传不可达/热区 |

### 4.6 案例库（1 页，1 通过 / 0 异常）

| 页面 | 状态 | 横向溢出 | console | 坏图 | 无标签字段 | <24px 热区 | 内链数 | 体积(KB) | 判定 |
|---|---|---|---|---|---|---|---:|---:|---|
| `/gallery/` | 200 | 0 | 0 | 0 | 0 | 2 | 21 | 44678 | ⚠️ 热区 |

### 4.7 博客（101 页，89 通过 / 12 异常）

| 页面 | 状态 | 横向溢出 | console | 坏图 | 无标签字段 | <24px 热区 | 内链数 | 体积(KB) | 判定 |
|---|---|---|---|---|---|---|---:|---:|---|
| `/blog/` | 200 | 0 | 0 | 0 | 0 | 2 | 121 | 205 | ⚠️ 热区 |
| `/blog/affordable-wedding-video-ai/` | 200 | 0 | 0 | 0 | 0 | 1 | 26 | 118 | ❌ 重复ID |
| `/blog/ai-editor-vs-traditional-editing/` | 200 | 0 | 0 | 0 | 0 | 1 | 21 | 81 | ❌ 重复ID |
| `/blog/ai-photos-to-wedding-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 25 | 75 | ⚠️ 热区 |
| `/blog/ai-proposal-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 22 | 121 | ⚠️ 热区 |
| `/blog/ai-tools-for-photographers/` | 200 | 0 | 0 | 0 | 0 | 1 | 24 | 172 | ⚠️ 热区 |
| `/blog/ai-video-maker-vs-videographer/` | 200 | 0 | 0 | 0 | 0 | 1 | 21 | 121 | ⚠️ 热区 |
| `/blog/ai-vs-human-wedding-editing/` | 200 | 54px | 0 | 0 | 0 | 1 | 25 | 112 | ❌ 溢出 |
| `/blog/ai-wedding-video-generator-guide/` | 200 | 0 | 0 | 0 | 0 | 1 | 28 | 88 | ⚠️ 热区 |
| `/blog/ai-wedding-video-industry/` | 200 | 0 | 0 | 0 | 0 | 1 | 26 | 106 | ⚠️ 热区 |
| `/blog/ai-wedding-video-privacy/` | 200 | 0 | 0 | 0 | 0 | 1 | 23 | 123 | ⚠️ 热区 |
| `/blog/ai-wedding-video-workflow/` | 200 | 15px | 0 | 0 | 0 | 1 | 21 | 93 | ❌ 溢出 |
| `/blog/ai-wont-replace-photographers/` | 200 | 0 | 0 | 0 | 0 | 1 | 24 | 112 | ⚠️ 热区 |
| `/blog/automatic-wedding-video-editing/` | 200 | 0 | 0 | 0 | 0 | 1 | 22 | 113 | ⚠️ 热区 |
| `/blog/best-ai-wedding-video-tools-2026/` | 200 | 0 | 0 | 0 | 0 | 1 | 21 | 168 | ⚠️ 热区 |
| `/blog/bride-wedding-video-checklist/` | 200 | 0 | 0 | 0 | 0 | 1 | 27 | 126 | ⚠️ 热区 |
| `/blog/budget-wedding-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 28 | 85 | ⚠️ 热区 |
| `/blog/canva-vs-ai-wedding-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 21 | 98 | ⚠️ 热区 |
| `/blog/cartoon-anime-wedding-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 21 | 95 | ⚠️ 热区 |
| `/blog/cartoon-wedding-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 25 | 154 | ⚠️ 热区 |
| `/blog/choose-wedding-videographer/` | 200 | 0 | 0 | 0 | 0 | 1 | 28 | 153 | ⚠️ 热区 |
| `/blog/christmas-wedding-video/` | 200 | 0 | 0 | 0 | 0 | 2 | 27 | 181 | ⚠️ 热区 |
| `/blog/cinematic-wedding-trailer-guide/` | 200 | 0 | 0 | 0 | 0 | 1 | 26 | 85 | ⚠️ 热区 |
| `/blog/couple-slideshow-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 23 | 126 | ⚠️ 热区 |
| `/blog/destination-wedding-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 26 | 168 | ⚠️ 热区 |
| `/blog/digitize-parents-wedding-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 26 | 93 | ⚠️ 热区 |
| `/blog/diy-wedding-video-phone/` | 200 | 0 | 0 | 0 | 0 | 1 | 22 | 129 | ⚠️ 热区 |
| `/blog/elopement-video-ideas/` | 200 | 0 | 0 | 0 | 0 | 1 | 26 | 113 | ⚠️ 热区 |
| `/blog/family-tribute-video-wedding/` | 200 | 51px | 0 | 0 | 0 | 1 | 21 | 76 | ❌ 溢出 |
| `/blog/fix-shaky-wedding-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 25 | 88 | ⚠️ 热区 |
| `/blog/free-wedding-video-maker/` | 200 | 0 | 0 | 0 | 0 | 1 | 23 | 123 | ⚠️ 热区 |
| `/blog/honor-deceased-parent-wedding/` | 200 | 0 | 0 | 0 | 0 | 1 | 27 | 81 | ⚠️ 热区 |
| `/blog/how-long-should-wedding-video-be/` | 200 | 0 | 0 | 0 | 0 | 1 | 28 | 136 | ⚠️ 热区 |
| `/blog/how-to-make-wedding-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 25 | 102 | ⚠️ 热区 |
| `/blog/include-remote-family-wedding-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 26 | 120 | ⚠️ 热区 |
| `/blog/lgbtq-wedding-video-ideas/` | 200 | 0 | 0 | 0 | 0 | 1 | 22 | 186 | ⚠️ 热区 |
| `/blog/make-first-ai-wedding-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 23 | 147 | ⚠️ 热区 |
| `/blog/micro-wedding-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 28 | 103 | ⚠️ 热区 |
| `/blog/multilingual-wedding-video/` | 200 | 7px | 0 | 0 | 0 | 1 | 21 | 66 | ❌ 溢出 |
| `/blog/multilingual-wedding-videos/` | 200 | 0 | 0 | 0 | 0 | 1 | 26 | 109 | ⚠️ 热区 |
| `/blog/pet-wedding-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 21 | 176 | ⚠️ 热区 |
| `/blog/pet-wedding-videos/` | 200 | 0 | 0 | 0 | 0 | 1 | 26 | 129 | ⚠️ 热区 |
| `/blog/photographer-upsell-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 26 | 137 | ⚠️ 热区 |
| `/blog/proposal-video-ideas/` | 200 | 0 | 0 | 0 | 0 | 1 | 25 | 160 | ⚠️ 热区 |
| `/blog/raw-wedding-footage-ideas/` | 200 | 0 | 0 | 0 | 0 | 1 | 27 | 105 | ⚠️ 热区 |
| `/blog/restore-old-wedding-photos/` | 200 | 0 | 0 | 0 | 0 | 1 | 28 | 117 | ⚠️ 热区 |
| `/blog/restore-vhs-wedding-footage/` | 200 | 0 | 0 | 0 | 0 | 1 | 26 | 117 | ⚠️ 热区 |
| `/blog/same-sex-wedding-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 30 | 128 | ⚠️ 热区 |
| `/blog/send-large-wedding-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 26 | 105 | ⚠️ 热区 |
| `/blog/share-wedding-video-with-family/` | 200 | 0 | 0 | 0 | 0 | 1 | 27 | 87 | ⚠️ 热区 |
| `/blog/skip-wedding-videographer/` | 200 | 0 | 0 | 0 | 0 | 1 | 30 | 105 | ⚠️ 热区 |
| `/blog/slow-motion-wedding-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 22 | 163 | ⚠️ 热区 |
| `/blog/spring-wedding-video-trends/` | 200 | 0 | 0 | 0 | 0 | 1 | 28 | 164 | ⚠️ 热区 |
| `/blog/summer-wedding-video-tips/` | 200 | 0 | 0 | 0 | 0 | 1 | 26 | 148 | ⚠️ 热区 |
| `/blog/unique-wedding-video-ideas/` | 200 | 0 | 0 | 0 | 0 | 1 | 26 | 96 | ⚠️ 热区 |
| `/blog/vhs-to-digital-wedding-cost/` | 200 | 0 | 0 | 0 | 0 | 1 | 26 | 71 | ⚠️ 热区 |
| `/blog/video-wedding-invitation/` | 200 | 0 | 0 | 0 | 0 | 1 | 22 | 120 | ⚠️ 热区 |
| `/blog/vintage-wedding-video-restoration/` | 200 | 0 | 0 | 0 | 0 | 1 | 21 | 95 | ⚠️ 热区 |
| `/blog/vow-renewal-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 28 | 120 | ⚠️ 热区 |
| `/blog/wedding-anniversary-video-ideas/` | 200 | 0 | 0 | 0 | 0 | 1 | 27 | 188 | ⚠️ 热区 |
| `/blog/wedding-countdown-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 23 | 141 | ⚠️ 热区 |
| `/blog/wedding-highlight-reel/` | 200 | 0 | 0 | 0 | 0 | 1 | 25 | 77 | ⚠️ 热区 |
| `/blog/wedding-highlight-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 22 | 132 | ⚠️ 热区 |
| `/blog/wedding-invitation-video-guide/` | 200 | 0 | 0 | 0 | 0 | 1 | 23 | 113 | ⚠️ 热区 |
| `/blog/wedding-memes/` | 200 | 0 | 0 | 0 | 0 | 1 | 26 | 171 | ⚠️ 热区 |
| `/blog/wedding-photo-slideshow/` | 200 | 0 | 0 | 0 | 0 | 1 | 28 | 131 | ⚠️ 热区 |
| `/blog/wedding-photos-vs-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 25 | 115 | ⚠️ 热区 |
| `/blog/wedding-slideshow-guide/` | 200 | 0 | 0 | 0 | 0 | 1 | 23 | 139 | ⚠️ 热区 |
| `/blog/wedding-slow-motion-effect/` | 200 | 0 | 0 | 0 | 0 | 1 | 26 | 102 | ⚠️ 热区 |
| `/blog/wedding-trailer-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 22 | 150 | ⚠️ 热区 |
| `/blog/wedding-video-audio-fix/` | 200 | 0 | 0 | 0 | 0 | 1 | 26 | 95 | ⚠️ 热区 |
| `/blog/wedding-video-captions/` | 200 | 145px | 0 | 0 | 0 | 1 | 23 | 129 | ❌ 溢出 |
| `/blog/wedding-video-cost-2026-new/` | 200 | 0 | 0 | 0 | 0 | 1 | 26 | 108 | ⚠️ 热区 |
| `/blog/wedding-video-cost-2026/` | 200 | 0 | 0 | 0 | 0 | 1 | 27 | 118 | ⚠️ 热区 |
| `/blog/wedding-video-for-parents/` | 200 | 0 | 0 | 0 | 0 | 1 | 27 | 90 | ⚠️ 热区 |
| `/blog/wedding-video-formats/` | 200 | 0 | 0 | 0 | 0 | 1 | 29 | 144 | ⚠️ 热区 |
| `/blog/wedding-video-from-photos/` | 200 | 0 | 0 | 0 | 0 | 1 | 27 | 104 | ⚠️ 热区 |
| `/blog/wedding-video-gift-ideas/` | 200 | 0 | 0 | 0 | 0 | 1 | 27 | 116 | ⚠️ 热区 |
| `/blog/wedding-video-inspiration/` | 200 | 0 | 0 | 0 | 0 | 1 | 25 | 84 | ⚠️ 热区 |
| `/blog/wedding-video-length-guide/` | 200 | 0 | 0 | 0 | 0 | 1 | 21 | 106 | ⚠️ 热区 |
| `/blog/wedding-video-music-guide-new/` | 200 | 117px | 0 | 0 | 0 | 1 | 23 | 150 | ❌ 溢出 |
| `/blog/wedding-video-music-guide/` | 200 | 0 | 0 | 0 | 0 | 1 | 27 | 95 | ⚠️ 热区 |
| `/blog/wedding-video-music/` | 200 | 0 | 0 | 0 | 0 | 1 | 26 | 71 | ⚠️ 热区 |
| `/blog/wedding-video-no-editing-skills/` | 200 | 0 | 0 | 0 | 0 | 1 | 24 | 99 | ⚠️ 热区 |
| `/blog/wedding-video-photo-checklist/` | 200 | 0 | 0 | 0 | 0 | 1 | 22 | 106 | ⚠️ 热区 |
| `/blog/wedding-video-social-media/` | 200 | 0 | 0 | 0 | 0 | 1 | 27 | 129 | ⚠️ 热区 |
| `/blog/wedding-video-subtitles/` | 200 | 0 | 0 | 0 | 0 | 1 | 26 | 112 | ⚠️ 热区 |
| `/blog/wedding-video-timeline/` | 200 | 0 | 0 | 0 | 0 | 1 | 27 | 133 | ⚠️ 热区 |
| `/blog/wedding-video-trends-2026/` | 200 | 72px | 0 | 0 | 0 | 1 | 21 | 49 | ❌ 溢出 |
| `/blog/wedding-video-types-guide/` | 200 | 32px | 0 | 0 | 0 | 1 | 21 | 99 | ❌ 溢出 |
| `/blog/wedding-video-vs-photos/` | 200 | 0 | 0 | 0 | 0 | 1 | 27 | 139 | ⚠️ 热区 |
| `/blog/wedding-video-without-videographer/` | 200 | 0 | 0 | 0 | 0 | 1 | 22 | 132 | ⚠️ 热区 |
| `/blog/wedding-wishes-video/` | 200 | 8px | 0 | 0 | 0 | 1 | 21 | 71 | ❌ 溢出 |
| `/blog/weddingai-success-stories/` | 200 | 0 | 0 | 0 | 0 | 1 | 27 | 108 | ⚠️ 热区 |
| `/blog/weddingai-video-case-studies/` | 200 | 0 | 0 | 0 | 0 | 1 | 23 | 109 | ⚠️ 热区 |
| `/blog/weddingai-video-guide/` | 200 | 42px | 0 | 0 | 0 | 1 | 21 | 53 | ❌ 溢出 |
| `/blog/weddingai-video-review/` | 200 | 0 | 0 | 0 | 0 | 1 | 27 | 178 | ⚠️ 热区 |
| `/blog/what-is-ai-wedding-video-generator/` | 200 | 0 | 0 | 0 | 0 | 1 | 27 | 150 | ⚠️ 热区 |
| `/blog/what-to-do-with-wedding-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 31 | 118 | ⚠️ 热区 |
| `/blog/why-couples-choose-ai-video/` | 200 | 0 | 0 | 0 | 0 | 1 | 21 | 73 | ⚠️ 热区 |
| `/blog/why-wedding-video-important/` | 200 | 0 | 0 | 0 | 0 | 1 | 21 | 70 | ⚠️ 热区 |

### 4.8 服务页（14 页，6 通过 / 8 异常）

| 页面 | 状态 | 横向溢出 | console | 坏图 | 无标签字段 | <24px 热区 | 内链数 | 体积(KB) | 判定 |
|---|---|---|---|---|---|---|---:|---:|---|
| `/services/` | 200 | 0 | 0 | 0 | 0 | 10 | 21 | 14593 | ⚠️ 热区 |
| `/services/absence-compensation/` | 200 | 0 | 0 | 0 | 0 | 3 | 21 | 3367 | ⚠️ 热区 |
| `/services/absence-compensation/family-message/` | 200 | 249px | 0 | 0 | 0 | 2 | 22 | 954 | ❌ 溢出 |
| `/services/absence-compensation/family-tribute/` | 200 | 0 | 0 | 0 | 0 | 2 | 22 | 4881 | ⚠️ 热区 |
| `/services/personalization/` | 200 | 0 | 0 | 0 | 0 | 8 | 21 | 11292 | ⚠️ 热区 |
| `/services/personalization/ai-video-generator/` | 200 | 223px | 0 | 0 | 0 | 2 | 22 | 5805 | ❌ 溢出 |
| `/services/personalization/cartoon-style/` | 200 | 168px | 0 | 0 | 0 | 2 | 22 | 4737 | ❌ 溢出 |
| `/services/personalization/meme-generator/` | 200 | 144px | 0 | 0 | 0 | 2 | 22 | 3527 | ❌ 溢出 |
| `/services/personalization/multilingual/` | 200 | 0 | 0 | 0 | 0 | 2 | 22 | 4247 | ⚠️ 热区 |
| `/services/personalization/pet-wedding/` | 200 | 247px | 0 | 0 | 0 | 2 | 22 | 1825 | ❌ 溢出 |
| `/services/personalization/wedding-trailer/` | 200 | 263px | 0 | 0 | 0 | 2 | 22 | 3751 | ❌ 溢出 |
| `/services/video-enhancement/` | 200 | 203px | 0 | 0 | 0 | 3 | 21 | 1245 | ❌ 溢出 |
| `/services/video-enhancement/slow-motion/` | 200 | 0 | 0 | 0 | 0 | 2 | 22 | 3237 | ⚠️ 热区 |
| `/services/video-enhancement/vintage-restoration/` | 200 | 254px | 0 | 0 | 0 | 4 | 22 | 1679 | ❌ 溢出 |

### 4.9 关于（1 页，1 通过 / 0 异常）

| 页面 | 状态 | 横向溢出 | console | 坏图 | 无标签字段 | <24px 热区 | 内链数 | 体积(KB) | 判定 |
|---|---|---|---|---|---|---|---:|---:|---|
| `/about/` | 200 | 0 | 0 | 0 | 0 | 2 | 21 | 48 | ⚠️ 热区 |

### 4.10 资源（1 页，0 通过 / 1 异常）

| 页面 | 状态 | 横向溢出 | console | 坏图 | 无标签字段 | <24px 热区 | 内链数 | 体积(KB) | 判定 |
|---|---|---|---|---|---|---|---:|---:|---|
| `/resources/` | 200 | 32px | 0 | 0 | 0 | 1 | 21 | 69 | ❌ 溢出 |

### 4.11 AI 生成器落地页（1 页，0 通过 / 1 异常）

| 页面 | 状态 | 横向溢出 | console | 坏图 | 无标签字段 | <24px 热区 | 内链数 | 体积(KB) | 判定 |
|---|---|---|---|---|---|---|---:|---:|---|
| `/ai-wedding-video-generator/` | 200 | 666px | 0 | 0 | 0 | 1 | 21 | 69 | ❌ 溢出 |

### 4.12 隐私（1 页，1 通过 / 0 异常）

| 页面 | 状态 | 横向溢出 | console | 坏图 | 无标签字段 | <24px 热区 | 内链数 | 体积(KB) | 判定 |
|---|---|---|---|---|---|---|---:|---:|---|
| `/privacy/` | 200 | 0 | 0 | 0 | 0 | 1 | 21 | 18 | ⚠️ 热区 |

### 4.13 条款（1 页，1 通过 / 0 异常）

| 页面 | 状态 | 横向溢出 | console | 坏图 | 无标签字段 | <24px 热区 | 内链数 | 体积(KB) | 判定 |
|---|---|---|---|---|---|---|---:|---:|---|
| `/terms/` | 200 | 0 | 0 | 0 | 0 | 1 | 21 | 18 | ⚠️ 热区 |

### 4.14 搜索（1 页，1 通过 / 0 异常）

| 页面 | 状态 | 横向溢出 | console | 坏图 | 无标签字段 | <24px 热区 | 内链数 | 体积(KB) | 判定 |
|---|---|---|---|---|---|---|---:|---:|---|
| `/search/` | 200 | 0 | 0 | 0 | 0 | 1 | 22 | 18 | ⚠️ 热区 |

### 4.15 其他语言页面（移动视口）

| 页面 | 状态 | 语言回落 | 横向溢出 | console | 判定 |
|---|---|---|---|---|---|
| `/ar/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/ar/about/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/ar/ai-wedding-video-generator/` | 200 | 否 | 284px | 0 | ❌ 溢出 |
| `/ar/blog/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/ar/blog/affordable-wedding-video-ai/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/ar/gallery/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/ar/order/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/ar/pricing/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/ar/resources/` | 200 | 否 | 5px | 0 | ❌ 溢出 |
| `/ar/services/` | 200 | 否 | 39px | 0 | ❌ 溢出 |
| `/ar/success/` | 200 | 否 | 0 | 2 | ❌ 4xx |
| `/ar/tools/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/ar/tools/compress-wedding-photos/` | 200 | 否 | 221px | 0 | ❌ 溢出 |
| `/ar/tools/wedding-hashtag-generator/` | 200 | 否 | 182px | 0 | ❌ 溢出 |
| `/de/` | 200 | 否 | 50px | 0 | ❌ 溢出 |
| `/de/about/` | 200 | 否 | 41px | 0 | ❌ 溢出 |
| `/de/ai-wedding-video-generator/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/de/blog/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/de/blog/affordable-wedding-video-ai/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/de/gallery/` | 200 | 否 | 132px | 0 | ❌ 溢出 |
| `/de/order/` | 200 | 否 | 18px | 0 | ❌ 溢出 |
| `/de/pricing/` | 200 | 否 | 150px | 0 | ❌ 溢出 |
| `/de/resources/` | 200 | 否 | 73px | 0 | ❌ 溢出 |
| `/de/services/` | 200 | 否 | 150px | 0 | ❌ 溢出 |
| `/de/success/` | 200 | 否 | 0 | 2 | ❌ 4xx |
| `/de/tools/` | 200 | 否 | 23px | 0 | ❌ 溢出 |
| `/de/tools/compress-wedding-photos/` | 200 | 否 | 0 | 0 | ⚠️ 上传不可达/热区 |
| `/de/tools/wedding-hashtag-generator/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/es/` | 200 | 否 | 7px | 0 | ❌ 溢出 |
| `/es/about/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/es/ai-wedding-video-generator/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/es/blog/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/es/blog/affordable-wedding-video-ai/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/es/gallery/` | 200 | 否 | 343px | 0 | ❌ 溢出 |
| `/es/order/` | 200 | 否 | 0 | 5 | ⚠️ 热区 |
| `/es/pricing/` | 200 | 否 | 47px | 0 | ❌ 溢出 |
| `/es/resources/` | 200 | 否 | 60px | 0 | ❌ 溢出 |
| `/es/services/` | 200 | 否 | 77px | 0 | ❌ 溢出 |
| `/es/success/` | 200 | 否 | 0 | 2 | ❌ 4xx |
| `/es/tools/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/es/tools/compress-wedding-photos/` | 200 | 否 | 292px | 0 | ❌ 溢出 |
| `/es/tools/wedding-hashtag-generator/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/fr/` | 200 | 否 | 34px | 0 | ❌ 溢出 |
| `/fr/about/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/fr/ai-wedding-video-generator/` | 200 | 否 | 629px | 0 | ❌ 溢出 |
| `/fr/blog/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/fr/blog/affordable-wedding-video-ai/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/fr/gallery/` | 200 | 否 | 341px | 0 | ❌ 溢出 |
| `/fr/order/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/fr/pricing/` | 200 | 否 | 54px | 0 | ❌ 溢出 |
| `/fr/resources/` | 200 | 否 | 154px | 0 | ❌ 溢出 |
| `/fr/services/` | 200 | 否 | 82px | 0 | ❌ 溢出 |
| `/fr/success/` | 200 | 否 | 0 | 2 | ❌ 4xx |
| `/fr/tools/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/fr/tools/compress-wedding-photos/` | None | 否 | 0 | 0 | ❌ HTTP |
| `/fr/tools/wedding-hashtag-generator/` | 200 | 否 | 288px | 0 | ❌ 溢出 |
| `/hi/` | 200 | 否 | 22px | 0 | ❌ 溢出 |
| `/hi/about/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/hi/ai-wedding-video-generator/` | 200 | 否 | 278px | 0 | ❌ 溢出 |
| `/hi/blog/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/hi/blog/affordable-wedding-video-ai/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/hi/gallery/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/hi/order/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/hi/pricing/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/hi/resources/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/hi/services/` | 200 | 否 | 42px | 0 | ❌ 溢出 |
| `/hi/success/` | 200 | 否 | 0 | 2 | ❌ 4xx |
| `/hi/tools/` | None | 否 | 0 | 0 | ❌ HTTP |
| `/hi/tools/compress-wedding-photos/` | 200 | 否 | 187px | 0 | ❌ 溢出 |
| `/hi/tools/wedding-hashtag-generator/` | 200 | 否 | 199px | 0 | ❌ 溢出 |
| `/ja/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/ja/about/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/ja/ai-wedding-video-generator/` | 200 | 否 | 241px | 0 | ❌ 溢出 |
| `/ja/blog/` | 200 | 是 ⚠️ | 0 | 0 | ❌ 语言 |
| `/ja/blog/affordable-wedding-video-ai/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/ja/gallery/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/ja/order/` | 200 | 否 | 0 | 1 | ⚠️ 热区 |
| `/ja/pricing/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/ja/resources/` | 200 | 否 | 44px | 0 | ❌ 溢出 |
| `/ja/services/` | 200 | 否 | 13px | 0 | ❌ 溢出 |
| `/ja/success/` | 200 | 否 | 0 | 2 | ❌ 4xx |
| `/ja/tools/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/ja/tools/compress-wedding-photos/` | 200 | 否 | 148px | 0 | ❌ 溢出 |
| `/ja/tools/wedding-hashtag-generator/` | 200 | 是 ⚠️ | 244px | 0 | ❌ 溢出/语言 |
| `/pt/` | 200 | 否 | 36px | 0 | ❌ 溢出 |
| `/pt/about/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/pt/ai-wedding-video-generator/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/pt/blog/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/pt/blog/affordable-wedding-video-ai/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/pt/gallery/` | 200 | 否 | 327px | 0 | ❌ 溢出 |
| `/pt/order/` | 200 | 否 | 0 | 2 | ⚠️ 热区 |
| `/pt/pricing/` | 200 | 否 | 63px | 0 | ❌ 溢出 |
| `/pt/resources/` | None | 否 | 0 | 0 | ❌ HTTP |
| `/pt/services/` | 200 | 否 | 74px | 0 | ❌ 溢出 |
| `/pt/success/` | 200 | 否 | 0 | 2 | ❌ 4xx |
| `/pt/tools/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/pt/tools/compress-wedding-photos/` | None | 否 | 0 | 0 | ❌ HTTP |
| `/pt/tools/wedding-hashtag-generator/` | 200 | 否 | 304px | 0 | ❌ 溢出 |
| `/ru/` | 200 | 是 ⚠️ | 54px | 0 | ❌ 溢出/语言 |
| `/ru/about/` | 200 | 是 ⚠️ | 0 | 0 | ❌ 语言 |
| `/ru/ai-wedding-video-generator/` | 200 | 否 | 626px | 0 | ❌ 溢出 |
| `/ru/blog/` | 200 | 是 ⚠️ | 0 | 0 | ❌ 语言 |
| `/ru/blog/affordable-wedding-video-ai/` | 200 | 是 ⚠️ | 0 | 0 | ❌ 重复ID/语言 |
| `/ru/gallery/` | 200 | 是 ⚠️ | 17px | 0 | ❌ 溢出/语言 |
| `/ru/order/` | 200 | 是 ⚠️ | 0 | 6 | ❌ 语言 |
| `/ru/pricing/` | 200 | 是 ⚠️ | 11px | 0 | ❌ 溢出/语言 |
| `/ru/resources/` | 200 | 是 ⚠️ | 32px | 0 | ❌ 溢出/语言 |
| `/ru/services/` | 200 | 是 ⚠️ | 74px | 0 | ❌ 溢出/语言 |
| `/ru/success/` | 200 | 是 ⚠️ | 0 | 2 | ❌ 4xx/语言 |
| `/ru/tools/` | 200 | 是 ⚠️ | 0 | 0 | ❌ 语言 |
| `/ru/tools/compress-wedding-photos/` | 200 | 否 | 291px | 0 | ❌ 溢出 |
| `/ru/tools/wedding-hashtag-generator/` | 200 | 是 ⚠️ | 0 | 0 | ❌ 语言 |
| `/th/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/th/about/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/th/ai-wedding-video-generator/` | 200 | 否 | 285px | 0 | ❌ 溢出 |
| `/th/blog/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/th/blog/affordable-wedding-video-ai/` | None | 否 | 0 | 0 | ❌ HTTP |
| `/th/gallery/` | 200 | 是 ⚠️ | 17px | 0 | ❌ 溢出/语言 |
| `/th/order/` | 200 | 是 ⚠️ | 0 | 0 | ❌ 语言 |
| `/th/pricing/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/th/resources/` | 200 | 否 | 46px | 0 | ❌ 溢出 |
| `/th/services/` | 200 | 否 | 18px | 0 | ❌ 溢出 |
| `/th/success/` | None | 否 | 0 | 0 | ❌ HTTP |
| `/th/tools/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/th/tools/compress-wedding-photos/` | 200 | 否 | 159px | 0 | ❌ 溢出 |
| `/th/tools/wedding-hashtag-generator/` | 200 | 否 | 198px | 0 | ❌ 溢出 |
| `/zh/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/zh/about/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/zh/ai-wedding-video-generator/` | 200 | 否 | 249px | 0 | ❌ 溢出 |
| `/zh/blog/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/zh/blog/affordable-wedding-video-ai/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/zh/gallery/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/zh/order/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/zh/pricing/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/zh/resources/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/zh/services/` | 200 | 否 | 31px | 0 | ❌ 溢出 |
| `/zh/success/` | 200 | 是 ⚠️ | 0 | 2 | ❌ 4xx/语言 |
| `/zh/tools/` | 200 | 否 | 0 | 0 | ⚠️ 热区 |
| `/zh/tools/compress-wedding-photos/` | 200 | 否 | 167px | 0 | ❌ 溢出 |
| `/zh/tools/wedding-hashtag-generator/` | 200 | 是 ⚠️ | 179px | 0 | ❌ 溢出/语言 |

### 4.16 13 个免费工具的功能实测（上传真实照片 → 点击主按钮）

| 工具 | 上传后图片解码 | 主按钮 | 实测结论 |
|---|---|---|---|
| `/tools/add-text-to-wedding-photo/` | ✅ 正常 | `run-btn` | OK (0 dl / 1 blob) |
| `/tools/compress-wedding-photos/` | ✅ 正常 | `run-btn` | OK (0 dl / 1 blob) |
| `/tools/crop-wedding-photo-for-reels/` | ✅ 正常 | `run-btn` | OK (0 dl / 1 blob) |
| `/tools/heic-to-jpg-wedding-photos/` | —（无文件输入） | 无可用主按钮 | no enabled primary button |
| `/tools/remove-background-wedding-portrait/` | ✅ 正常 | `run-btn` | OK (0 dl / 1 blob) |
| `/tools/save-the-date-maker/` | ✅ 画布已绘制 | 无可用主按钮 | no enabled primary button |
| `/tools/wedding-budget-calculator/` | —（无文件输入） | 无可用主按钮 | no upload (generator/calculator) |
| `/tools/wedding-hashtag-generator/` | —（无文件输入） | 无可用主按钮 | no upload (generator/calculator) |
| `/tools/wedding-invitation-maker/` | ✅ 画布已绘制 | 无可用主按钮 | no enabled primary button |
| `/tools/wedding-photo-book-planner/` | ✅ 画布已绘制 | 无可用主按钮 | no enabled primary button |
| `/tools/wedding-photo-collage/` | ✅ 正常 | 无可用主按钮 | no enabled primary button |
| `/tools/wedding-seating-chart-maker/` | —（无文件输入） | 无可用主按钮 | no upload (generator/calculator) |
| `/tools/wedding-video-invitation-maker/` | ✅ 画布已绘制 | 无可用主按钮 | no enabled primary button |

## 5. 交互测试结果

共执行 179 条交互断言。通过 140，失败 33，警告 5，阻塞 1。

### 5.1 COOKIE（4 条：通过 4 / 失败 0 / 警告 0 / 阻塞 0）

| 断言 ID | 用例 | 页面 | 视口 | 结果 | 观测 |
|---|---|---|---|---|---|
| `COOKIE-01` | Cookie banner shows on first visit | `/` | mobile | ✅ | banner rendered |
| `COOKIE-02` | 'Accept all' dismisses the banner | `/` | mobile | ✅ | banner removed |
| `COOKIE-03` | Choice is remembered across reload (180-day consent) | `/` | mobile | ✅ | localStorage='all', banner after reload=hidden |
| `COOKIE-04` | 'Essential only' stores the rejection | `/` | mobile | ✅ | localStorage='essential' |

### 5.2 NAV（10 条：通过 7 / 失败 3 / 警告 0 / 阻塞 0）

| 断言 ID | 用例 | 页面 | 视口 | 结果 | 观测 |
|---|---|---|---|---|---|
| `NAV-01` | Hamburger visible / nav collapsed on mobile | `/` | mobile | ✅ | toggle_visible=True, nav_visible=False |
| `NAV-02` | Tap hamburger opens the nav | `/` | mobile | ✅ | aria-expanded=true, panel height=999px, in viewport=False |
| `NAV-03` | Open panel fits the mobile viewport (no clipped items) | `/` | mobile | ❌ | panel bottom vs viewport: inViewport=False |
| `NAV-04` | Focus moves into the menu when it opens | `/` | mobile | ✅ | activeElement=A:Services ▾ |
| `NAV-05` | Escape closes the menu and returns focus | `/` | mobile | ✅ | open=False, aria-expanded=false |
| `NAV-06` | Focus returns to the hamburger after Escape | `/` | mobile | ✅ | focusOnToggle=True |
| `NAV-07` | Tapping outside closes the menu | `/` | mobile | ❌ | closed=False |
| `NAV-08` | Focus stays trapped inside the open menu | `/` | mobile | ❌ | tabbed 25 times over 19 nav links without escaping |
| `NAV-09` | Every header nav link resolves | `/` | mobile | ✅ | 19 links all OK |
| `NAV-10` | Desktop shows the full nav, not the hamburger | `/` | desktop | ✅ | nav_visible=True, hamburger_visible=False |

### 5.3 A11Y（5 条：通过 4 / 失败 0 / 警告 1 / 阻塞 0）

| 断言 ID | 用例 | 页面 | 视口 | 结果 | 观测 |
|---|---|---|---|---|---|
| `A11Y-01` | First Tab reveals a skip-to-content link | `/` | desktop | ✅ | focused A 'Skip to main content' -> #main-content visible=True |
| `A11Y-02` | Skip link target exists in the DOM | `/` | desktop | ✅ | target #main-content exists=True |
| `A11Y-03` | Keyboard focus is visually indicated on nav links | `/` | desktop | ✅ | focus style changes: True |
| `A11Y-04` | Form fields are >=16px (iOS auto-zoom on focus) | `/` | desktop | ⚠️ | 1 fields <16px: [{'id': 'wa-lang-select', 'fs': 13.3333}] |
| `A11Y-05` | Viewport meta does not block pinch-zoom | `/` | desktop | ✅ | content="width=device-width, initial-scale=1.0, viewport-fit=cover" |

### 5.4 SEC（1 条：通过 1 / 失败 0 / 警告 0 / 阻塞 0）

| 断言 ID | 用例 | 页面 | 视口 | 结果 | 观测 |
|---|---|---|---|---|---|
| `SEC-01` | target=_blank links carry rel=noopener | `/` | desktop | ✅ | all _blank links hardened |

### 5.5 I18N（24 条：通过 12 / 失败 12 / 警告 0 / 阻塞 0）

| 断言 ID | 用例 | 页面 | 视口 | 结果 | 观测 |
|---|---|---|---|---|---|
| `I18N-SW-00` | Language selector lists all 11 languages | `/` | desktop | ✅ | 11 options: ['en', 'zh', 'es', 'fr', 'de', 'pt', 'ja', 'ru', 'ar', 'th', 'hi'] |
| `I18N-zh-FORM` | ZH validation messages are localized | `/zh/order/` | desktop | ✅ | message='Please fix the following: 您的名字 is required; 电子邮箱 is required; 您对哪项服务感兴趣？ is required; 预算 is required' |
| `I18N-zh-KEYS` | ZH renders its translated strings | `/ (site-wide sample)` | desktop | ❌ | 63 of 60402 keys missing on sampled pages (0 identical to English) e.g. ['/:index.p_text.trusted_by_9400_couples_in_11_languages.32124339', '/:index.span_text.local_equivalent.zzzzzz1', '/:i |
| `I18N-es-FORM` | ES validation messages are localized | `/es/order/` | desktop | ✅ | message='Please fix the following: Nombre is required; Correo Electrónico is required; ¿Cuál le interesa? is ' |
| `I18N-es-KEYS` | ES renders its translated strings | `/ (site-wide sample)` | desktop | ❌ | 82 of 61414 keys missing on sampled pages (0 identical to English) e.g. ['/:index.p_text.trusted_by_9400_couples_in_11_languages.32124339', '/:index.span_text.local_equivalent.zzzzzz1', '/:i |
| `I18N-fr-FORM` | FR validation messages are localized | `/fr/order/` | desktop | ✅ | message='Please fix the following: Votre nom is required; E-mail is required; Quel service vous intéresse? is' |
| `I18N-fr-KEYS` | FR renders its translated strings | `/ (site-wide sample)` | desktop | ❌ | 51 of 61379 keys missing on sampled pages (0 identical to English) e.g. ['/:index.p_text.trusted_by_9400_couples_in_11_languages.32124339', '/:index.th_text.metric.1a2b3c4d', '/:index.td_tex |
| `I18N-de-FORM` | DE validation messages are localized | `/de/order/` | desktop | ✅ | message='Please fix the following: Ihr Name is required; Email is required; Welche wählst du für dich? is req' |
| `I18N-de-KEYS` | DE renders its translated strings | `/ (site-wide sample)` | desktop | ❌ | 52 of 60995 keys missing on sampled pages (1 identical to English) e.g. ['/:index.p_text.trusted_by_9400_couples_in_11_languages.32124339', '/:index.th_text.metric.1a2b3c4d', '/:index.th_tex |
| `I18N-pt-FORM` | PT validation messages are localized | `/pt/order/` | desktop | ✅ | message='Please fix the following: Seu nome is required; E-mail is required; Em qual serviço você está intere' |
| `I18N-pt-KEYS` | PT renders its translated strings | `/ (site-wide sample)` | desktop | ❌ | 53 of 61301 keys missing on sampled pages (0 identical to English) e.g. ['/:index.p_text.trusted_by_9400_couples_in_11_languages.32124339', '/:index.th_text.metric.1a2b3c4d', '/:index.td_tex |
| `I18N-ja-FORM` | JA validation messages are localized | `/ja/order/` | desktop | ✅ | message='Please fix the following: お名前 is required; メールアドレス is required; どのサービスに興味がありますか？ is required; 予算 is ' |
| `I18N-ja-KEYS` | JA renders its translated strings | `/ (site-wide sample)` | desktop | ❌ | 56 of 60394 keys missing on sampled pages (1 identical to English) e.g. ['/:index.p_text.trusted_by_9400_couples_in_11_languages.32124339', '/:index.span_text.local_equivalent.zzzzzz1', '/:i |
| `I18N-ru-FORM` | RU validation messages are localized | `/ru/order/` | desktop | ✅ | message='Please fix the following: Your Name is required; Email is required; Which service are you interested' |
| `I18N-ru-KEYS` | RU renders its translated strings | `/ (site-wide sample)` | desktop | ❌ | 1177 of 3235 keys missing on sampled pages (0 identical to English) e.g. ['/:index.title_text.ai_powered_wedding_video_services_weddin.58583865', '/:404.a_text.skip_to_main_content.85143743' |
| `I18N-ar-FORM` | AR validation messages are localized | `/ar/order/` | desktop | ✅ | message='Please fix the following: اسمك is required; بريد إلكتروني is required; ما الخدمة التي تهتم بها ؟ is ' |
| `I18N-ar-KEYS` | AR renders its translated strings | `/ (site-wide sample)` | desktop | ❌ | 51 of 60436 keys missing on sampled pages (1 identical to English) e.g. ['/:index.p_text.trusted_by_9400_couples_in_11_languages.32124339', '/:index.th_text.metric.1a2b3c4d', '/:index.th_tex |
| `I18N-th-FORM` | TH validation messages are localized | `/th/order/` | desktop | ✅ | message='Please fix the following: ชื่อของคุณ is required; ส่งอีเมล is required; คุณสนใจบริการใด? is required' |
| `I18N-th` | TH pages load | `/th/gallery/` | desktop | ❌ | TimeoutError: Page.goto: Timeout 40000ms exceeded. Call log: navigating to "http://127.0.0.1:8788/th/gallery/", waiting  |
| `I18N-th-KEYS` | TH renders its translated strings | `/ (site-wide sample)` | desktop | ❌ | 65 of 60776 keys missing on sampled pages (1 identical to English) e.g. ['/:index.p_text.trusted_by_9400_couples_in_11_languages.32124339', '/:index.span_text.local_equivalent.zzzzzz1', '/:i |
| `I18N-hi` | HI pages load | `/hi/tools/wedding-hashtag-generator/` | desktop | ❌ | TimeoutError: Page.goto: Timeout 40000ms exceeded. Call log: navigating to "http://127.0.0.1:8788/hi/tools/wedding-hasht |
| `I18N-hi-KEYS` | HI renders its translated strings | `/ (site-wide sample)` | desktop | ❌ | 33 of 61040 keys missing on sampled pages (1 identical to English) e.g. ['/:index.p_text.trusted_by_9400_couples_in_11_languages.32124339', '/:index.th_text.metric.1a2b3c4d', '/:index.td_tex |
| `I18N-ar-MENU` | AR mobile menu opens | `/ar/` | mobile | ✅ | open=True height=999px direction=rtl |
| `I18N-SW-01` | Switching to ZH lands on the translated page | `/` | desktop | ✅ | path=/zh/ html lang=zh h1='AI 婚礼视频 — 让每一刻都令人难忘' |

### 5.6 SUITE（3 条：通过 0 / 失败 3 / 警告 0 / 阻塞 0）

| 断言 ID | 用例 | 页面 | 视口 | 结果 | 观测 |
|---|---|---|---|---|---|
| `SUITE-chrome` | suite chrome crashed | `-` |  | ❌ | TimeoutError: Timeout 25000ms exceeded. =========================== logs =========================== waiting for navigation until 'load' ======================= @ File "C:\Users\qiaoshan\.op |
| `SUITE-home` | suite home crashed | `-` |  | ❌ | TimeoutError: Page.click: Timeout 30000ms exceeded. Call log: waiting for locator("a[href=\"/order/\"]")   -   locator resolved to 4 elements. Proceeding with t @ File "C:\Users\qiaoshan\.op |
| `SUITE-i18n` | suite i18n crashed | `-` |  | ❌ | TimeoutError: Page.goto: Timeout 30000ms exceeded. Call log: navigating to "http://127.0.0.1:8788/zh/", waiting until "load"  |

### 5.7 HOME（2 条：通过 1 / 失败 0 / 警告 0 / 阻塞 1）

| 断言 ID | 用例 | 页面 | 视口 | 结果 | 观测 |
|---|---|---|---|---|---|
| `HOME-01` | Above-the-fold CTAs are present and visible | `/` | mobile | ✅ | 5 visible CTAs: ['Get a Free Quote →', 'Explore Our Services', 'View All 25 Case Studies →', 'Browse All 13 Free Tools →', 'Get a Free Quote →'] |
| `HOME-02` | Primary CTA navigates to a working conversion page | `/` | mobile | ⛔ | TimeoutError: Locator.click: Timeout 30000ms exceeded. Call log: waiting for locator("a[href=\"/order/\"]").first   -   locator resolved to  |

### 5.8 PRICE（2 条：通过 1 / 失败 1 / 警告 0 / 阻塞 0）

| 断言 ID | 用例 | 页面 | 视口 | 结果 | 观测 |
|---|---|---|---|---|---|
| `PRICE-01` | Pricing page does not scroll sideways (desktop) | `/pricing/` | desktop | ✅ | document overflow=0px, table width=1152px, scrollable wrapper=None |
| `PRICE-02` | Pricing page shows plan cards + order CTAs (desktop) | `/pricing/` | desktop | ❌ | 0 plan cards, 5 order links |

### 5.9 TOOLS（2 条：通过 2 / 失败 0 / 警告 0 / 阻塞 0）

| 断言 ID | 用例 | 页面 | 视口 | 结果 | 观测 |
|---|---|---|---|---|---|
| `TOOLS-01` | Tools hub links all 13 tools | `/tools/` | mobile | ✅ | 13 tool links found; missing=[] |
| `TOOLS-02` | Every tool page opens (HTTP 200) | `/tools/` | mobile | ✅ | all 13 tools 200 |

### 5.10 TOOL（69 条：通过 58 / 失败 7 / 警告 4 / 阻塞 0）

| 断言 ID | 用例 | 页面 | 视口 | 结果 | 观测 |
|---|---|---|---|---|---|
| `TOOL-add-text-to-wedding-photo-KBD` | Upload control is reachable by keyboard | `/tools/add-text-to-wedding-photo/` | desktop | ✅ | file input display=none focusable=False, dropzone tabindex=0 role='button' focusable=True, input labelled=False |
| `TOOL-add-text-to-wedding-photo-01` | Primary action is disabled until a file is chosen | `/tools/add-text-to-wedding-photo/` | desktop | ✅ | primary={'id': 'run-btn', 'text': 'Apply to all', 'disabled': True} |
| `TOOL-add-text-to-wedding-photo-02` | Rejecting a non-image file shows a friendly message | `/tools/add-text-to-wedding-photo/` | desktop | ✅ | message="JPG, PNG, WebP • Multiple OK (same text applies to all) • Up to your browser's memory" jsErrors=[] |
| `TOOL-add-text-to-wedding-photo-03` | Choosing a valid photo enables the run action / shows a preview | `/tools/add-text-to-wedding-photo/` | desktop | ✅ | run_disabled=True, preview nodes=4 |
| `TOOL-add-text-to-wedding-photo-05` | 'Clear' resets the tool state | `/tools/add-text-to-wedding-photo/` | desktop | ✅ | files=0 run_disabled=True |
| `TOOL-add-text-to-wedding-photo-ERR` | No uncaught JS errors during the tool flow | `/tools/add-text-to-wedding-photo/` | desktop | ✅ | errors=[] |
| `TOOL-compress-wedding-photos-KBD` | Upload control is reachable by keyboard | `/tools/compress-wedding-photos/` | desktop | ✅ | file input display=none focusable=False, dropzone tabindex=0 role='button' focusable=True, input labelled=False |
| `TOOL-compress-wedding-photos-01` | Primary action is disabled until a file is chosen | `/tools/compress-wedding-photos/` | desktop | ✅ | primary={'id': 'run-btn', 'text': 'Compress', 'disabled': True} |
| `TOOL-compress-wedding-photos-02` | Rejecting a non-image file shows a friendly message | `/tools/compress-wedding-photos/` | desktop | ✅ | message='JPG, PNG, and WebP wedding photos by 60–85% before uploading to your album, sharing with fami' jsErrors=[] |
| `TOOL-compress-wedding-photos-03` | Choosing a valid photo enables the run action / shows a preview | `/tools/compress-wedding-photos/` | desktop | ✅ | run_disabled=False, preview nodes=1 |
| `TOOL-compress-wedding-photos-04` | Running the tool produces output without JS errors | `/tools/compress-wedding-photos/` | desktop | ❌ | errors=[] status='couple.jpgOriginal: 23.7 KBCould not decode this file. Try a JPG, PNG, or WebP.R' blobImages=1 canvases=[] result='' |
| `TOOL-compress-wedding-photos-05` | 'Clear' resets the tool state | `/tools/compress-wedding-photos/` | desktop | ✅ | files=0 run_disabled=True |
| `TOOL-compress-wedding-photos-ERR` | No uncaught JS errors during the tool flow | `/tools/compress-wedding-photos/` | desktop | ✅ | errors=[] |
| `TOOL-crop-wedding-photo-for-reels-KBD` | Upload control is reachable by keyboard | `/tools/crop-wedding-photo-for-reels/` | desktop | ✅ | file input display=none focusable=False, dropzone tabindex=0 role='button' focusable=True, input labelled=False |
| `TOOL-crop-wedding-photo-for-reels-01` | Primary action is disabled until a file is chosen | `/tools/crop-wedding-photo-for-reels/` | desktop | ✅ | primary={'id': 'run-btn', 'text': 'Crop', 'disabled': True} |
| `TOOL-crop-wedding-photo-for-reels-02` | Rejecting a non-image file shows a friendly message | `/tools/crop-wedding-photo-for-reels/` | desktop | ✅ | message="JPG, PNG, WebP • Batch-friendly • Up to your browser's memory" jsErrors=[] |
| `TOOL-crop-wedding-photo-for-reels-03` | Choosing a valid photo enables the run action / shows a preview | `/tools/crop-wedding-photo-for-reels/` | desktop | ✅ | run_disabled=False, preview nodes=1 |
| `TOOL-crop-wedding-photo-for-reels-04` | Running the tool produces output without JS errors | `/tools/crop-wedding-photo-for-reels/` | desktop | ❌ | errors=[] status='couple.jpgOriginal: 23.7 KBCould not decode this file. Try a JPG, PNG, or WebP.R' blobImages=1 canvases=[] result='' |
| `TOOL-crop-wedding-photo-for-reels-05` | 'Clear' resets the tool state | `/tools/crop-wedding-photo-for-reels/` | desktop | ✅ | files=0 run_disabled=True |
| `TOOL-crop-wedding-photo-for-reels-ERR` | No uncaught JS errors during the tool flow | `/tools/crop-wedding-photo-for-reels/` | desktop | ✅ | errors=[] |
| `TOOL-heic-to-jpg-wedding-photos-KBD` | Upload control is reachable by keyboard | `/tools/heic-to-jpg-wedding-photos/` | desktop | ✅ | file input display=none focusable=False, dropzone tabindex=0 role='button' focusable=True, input labelled=False |
| `TOOL-heic-to-jpg-wedding-photos-01` | Primary action is disabled until a file is chosen | `/tools/heic-to-jpg-wedding-photos/` | desktop | ✅ | primary={'id': 'run-btn', 'text': 'Convert to JPG', 'disabled': True} |
| `TOOL-heic-to-jpg-wedding-photos-02` | Rejecting a non-image file shows a friendly message | `/tools/heic-to-jpg-wedding-photos/` | desktop | ✅ | message='HEIC to JPG Wedding Photos: In-Browser Free + AI Video $9.9' jsErrors=[] |
| `TOOL-heic-to-jpg-wedding-photos-03` | Choosing a valid photo enables the run action / shows a preview | `/tools/heic-to-jpg-wedding-photos/` | desktop | ❌ | run_disabled=True, preview nodes=0 |
| `TOOL-heic-to-jpg-wedding-photos-05` | 'Clear' resets the tool state | `/tools/heic-to-jpg-wedding-photos/` | desktop | ✅ | files=0 run_disabled=True |
| `TOOL-heic-to-jpg-wedding-photos-ERR` | No uncaught JS errors during the tool flow | `/tools/heic-to-jpg-wedding-photos/` | desktop | ✅ | errors=[] |
| `TOOL-remove-background-wedding-portrait-KBD` | Upload control is reachable by keyboard | `/tools/remove-background-wedding-portrait/` | desktop | ✅ | file input display=none focusable=False, dropzone tabindex=0 role='button' focusable=True, input labelled=False |
| `TOOL-remove-background-wedding-portrait-01` | Primary action is disabled until a file is chosen | `/tools/remove-background-wedding-portrait/` | desktop | ✅ | primary={'id': 'run-btn', 'text': 'Remove background', 'disabled': True} |
| `TOOL-remove-background-wedding-portrait-02` | Rejecting a non-image file shows a friendly message | `/tools/remove-background-wedding-portrait/` | desktop | ✅ | message="JPG, PNG, WebP • Single portrait works best • Up to your browser's memory" jsErrors=[] |
| `TOOL-remove-background-wedding-portrait-03` | Choosing a valid photo enables the run action / shows a preview | `/tools/remove-background-wedding-portrait/` | desktop | ✅ | run_disabled=False, preview nodes=1 |
| `TOOL-remove-background-wedding-portrait-04` | Running the tool produces output without JS errors | `/tools/remove-background-wedding-portrait/` | desktop | ❌ | errors=[] status='couple.jpgOriginal: 23.7 KBCould not decode this file. Try a JPG, PNG, or WebP.R' blobImages=1 canvases=[] result='' |
| `TOOL-remove-background-wedding-portrait-05` | 'Clear' resets the tool state | `/tools/remove-background-wedding-portrait/` | desktop | ✅ | files=0 run_disabled=True |
| `TOOL-remove-background-wedding-portrait-ERR` | No uncaught JS errors during the tool flow | `/tools/remove-background-wedding-portrait/` | desktop | ✅ | errors=[] |
| `TOOL-save-the-date-maker-KBD` | Upload control is reachable by keyboard | `/tools/save-the-date-maker/` | desktop | ❌ | file input display=none focusable=False, dropzone tabindex=None role='' focusable=False, input labelled=True |
| `TOOL-save-the-date-maker-01` | Primary action is disabled until a file is chosen | `/tools/save-the-date-maker/` | desktop | ⚠️ | primary={'id': '', 'text': 'A & BJune 14, 2026Save the Dat', 'disabled': False} |
| `TOOL-save-the-date-maker-02` | Rejecting a non-image file shows a friendly message | `/tools/save-the-date-maker/` | desktop | ✅ | message='PNG ready for Instagram, WhatsApp, and 5×7 print.' jsErrors=[] |
| `TOOL-save-the-date-maker-03` | Choosing a valid photo enables the run action / shows a preview | `/tools/save-the-date-maker/` | desktop | ✅ | run_disabled=None, preview nodes=6 |
| `TOOL-save-the-date-maker-05` | 'Clear' resets the tool state | `/tools/save-the-date-maker/` | desktop | ⚠️ | files=1 run_disabled=None |
| `TOOL-save-the-date-maker-ERR` | No uncaught JS errors during the tool flow | `/tools/save-the-date-maker/` | desktop | ✅ | errors=[] |
| `TOOL-wedding-budget-calculator-00` | Tool exposes usable inputs and actions | `/tools/wedding-budget-calculator/` | desktop | ✅ | 31 inputs, 8 buttons |
| `TOOL-wedding-budget-calculator-ERR` | No uncaught JS errors during the tool flow | `/tools/wedding-budget-calculator/` | desktop | ✅ | errors=[] |
| `TOOL-wedding-hashtag-generator-00` | Tool exposes usable inputs and actions | `/tools/wedding-hashtag-generator/` | desktop | ✅ | 6 inputs, 24 buttons |
| `TOOL-wedding-hashtag-generator-ERR` | No uncaught JS errors during the tool flow | `/tools/wedding-hashtag-generator/` | desktop | ✅ | errors=[] |
| `TOOL-wedding-invitation-maker-KBD` | Upload control is reachable by keyboard | `/tools/wedding-invitation-maker/` | desktop | ✅ | file input display=none focusable=False, dropzone tabindex=0 role='button' focusable=True, input labelled=True |
| `TOOL-wedding-invitation-maker-01` | Primary action is disabled until a file is chosen | `/tools/wedding-invitation-maker/` | desktop | ⚠️ | primary={'id': 'download-print', 'text': 'Download 5×7 print (1500×2100)', 'disabled': False} |
| `TOOL-wedding-invitation-maker-02` | Rejecting a non-image file shows a friendly message | `/tools/wedding-invitation-maker/` | desktop | ✅ | message='PNG ready for professional print or WhatsApp.' jsErrors=[] |
| `TOOL-wedding-invitation-maker-03` | Choosing a valid photo enables the run action / shows a preview | `/tools/wedding-invitation-maker/` | desktop | ✅ | run_disabled=None, preview nodes=5 |
| `TOOL-wedding-invitation-maker-05` | 'Clear' resets the tool state | `/tools/wedding-invitation-maker/` | desktop | ✅ | files=0 run_disabled=None |
| `TOOL-wedding-invitation-maker-ERR` | No uncaught JS errors during the tool flow | `/tools/wedding-invitation-maker/` | desktop | ✅ | errors=[] |
| `TOOL-wedding-photo-book-planner-KBD` | Upload control is reachable by keyboard | `/tools/wedding-photo-book-planner/` | desktop | ❌ | file input display=none focusable=False, dropzone tabindex=None role=None focusable=None, input labelled=True |
| `TOOL-wedding-photo-book-planner-01` | Primary action is disabled until a file is chosen | `/tools/wedding-photo-book-planner/` | desktop | ❌ | primary=None |
| `TOOL-wedding-photo-book-planner-02` | Rejecting a non-image file shows a friendly message | `/tools/wedding-photo-book-planner/` | desktop | ✅ | message='PNGs ready to print. Free, no signup, no upload.' jsErrors=[] |
| `TOOL-wedding-photo-book-planner-03` | Choosing a valid photo enables the run action / shows a preview | `/tools/wedding-photo-book-planner/` | desktop | ✅ | run_disabled=None, preview nodes=81 |
| `TOOL-wedding-photo-book-planner-05` | 'Clear' resets the tool state | `/tools/wedding-photo-book-planner/` | desktop | ✅ | files=0 run_disabled=None |
| `TOOL-wedding-photo-book-planner-ERR` | No uncaught JS errors during the tool flow | `/tools/wedding-photo-book-planner/` | desktop | ✅ | errors=[] |
| `TOOL-wedding-photo-collage-KBD` | Upload control is reachable by keyboard | `/tools/wedding-photo-collage/` | desktop | ✅ | file input display=none focusable=False, dropzone tabindex=0 role='button' focusable=True, input labelled=False |
| `TOOL-wedding-photo-collage-01` | Primary action is disabled until a file is chosen | `/tools/wedding-photo-collage/` | desktop | ✅ | primary={'id': 'run-btn', 'text': 'Build collage', 'disabled': True} |
| `TOOL-wedding-photo-collage-02` | Rejecting a non-image file shows a friendly message | `/tools/wedding-photo-collage/` | desktop | ✅ | message='PNG in under 30 seconds.' jsErrors=[] |
| `TOOL-wedding-photo-collage-03` | Choosing a valid photo enables the run action / shows a preview | `/tools/wedding-photo-collage/` | desktop | ✅ | run_disabled=True, preview nodes=4 |
| `TOOL-wedding-photo-collage-05` | 'Clear' resets the tool state | `/tools/wedding-photo-collage/` | desktop | ✅ | files=0 run_disabled=True |
| `TOOL-wedding-photo-collage-ERR` | No uncaught JS errors during the tool flow | `/tools/wedding-photo-collage/` | desktop | ✅ | errors=[] |
| `TOOL-wedding-seating-chart-maker-00` | Tool exposes usable inputs and actions | `/tools/wedding-seating-chart-maker/` | desktop | ✅ | 4 inputs, 16 buttons |
| `TOOL-wedding-seating-chart-maker-ERR` | No uncaught JS errors during the tool flow | `/tools/wedding-seating-chart-maker/` | desktop | ✅ | errors=[] |
| `TOOL-wedding-video-invitation-maker-KBD` | Upload control is reachable by keyboard | `/tools/wedding-video-invitation-maker/` | desktop | ✅ | file input display=none focusable=False, dropzone tabindex=0 role='button' focusable=True, input labelled=True |
| `TOOL-wedding-video-invitation-maker-01` | Primary action is disabled until a file is chosen | `/tools/wedding-video-invitation-maker/` | desktop | ⚠️ | primary={'id': 'download-btn', 'text': 'Download 5 PNG frames (1080×19', 'disabled': False} |
| `TOOL-wedding-video-invitation-maker-02` | Rejecting a non-image file shows a friendly message | `/tools/wedding-video-invitation-maker/` | desktop | ✅ | message='PNG sequence — drop into CapCut or iMovie to make a 5-second Reel, or hand the design to our' jsErrors=[] |
| `TOOL-wedding-video-invitation-maker-03` | Choosing a valid photo enables the run action / shows a preview | `/tools/wedding-video-invitation-maker/` | desktop | ✅ | run_disabled=None, preview nodes=11 |
| `TOOL-wedding-video-invitation-maker-05` | 'Clear' resets the tool state | `/tools/wedding-video-invitation-maker/` | desktop | ✅ | files=0 run_disabled=None |
| `TOOL-wedding-video-invitation-maker-ERR` | No uncaught JS errors during the tool flow | `/tools/wedding-video-invitation-maker/` | desktop | ✅ | errors=[] |

### 5.11 GAL（24 条：通过 24 / 失败 0 / 警告 0 / 阻塞 0）

| 断言 ID | 用例 | 页面 | 视口 | 结果 | 观测 |
|---|---|---|---|---|---|
| `GAL-mobile-01` | Gallery renders its case-study cards | `/gallery/` | mobile | ✅ | 23 cards, 10 filter buttons |
| `GAL-mobile-F-all` | Filter 'All' shows the right cards | `/gallery/` | mobile | ✅ | 23/23 cards visible, active buttons=1 |
| `GAL-mobile-F-slow-motion` | Filter 'Slow Motion' shows the right cards | `/gallery/` | mobile | ✅ | 3/23 cards visible, active buttons=1 |
| `GAL-mobile-F-family-tribute` | Filter 'Family Tribute' shows the right cards | `/gallery/` | mobile | ✅ | 3/23 cards visible, active buttons=1 |
| `GAL-mobile-F-family-message` | Filter 'Family Message' shows the right cards | `/gallery/` | mobile | ✅ | 2/23 cards visible, active buttons=1 |
| `GAL-mobile-F-ai-video-generator` | Filter 'AI Films' shows the right cards | `/gallery/` | mobile | ✅ | 3/23 cards visible, active buttons=1 |
| `GAL-mobile-F-wedding-trailer` | Filter 'Trailers' shows the right cards | `/gallery/` | mobile | ✅ | 3/23 cards visible, active buttons=1 |
| `GAL-mobile-F-pet-wedding` | Filter 'Pet Videos' shows the right cards | `/gallery/` | mobile | ✅ | 3/23 cards visible, active buttons=1 |
| `GAL-mobile-F-multilingual` | Filter 'Multilingual' shows the right cards | `/gallery/` | mobile | ✅ | 2/23 cards visible, active buttons=1 |
| `GAL-mobile-F-cartoon-style` | Filter 'Animated Style' shows the right cards | `/gallery/` | mobile | ✅ | 2/23 cards visible, active buttons=1 |
| `GAL-mobile-F-meme-generator` | Filter 'Memes & GIFs' shows the right cards | `/gallery/` | mobile | ✅ | 2/23 cards visible, active buttons=1 |
| `GAL-mobile-02` | No filter category is empty | `/gallery/` | mobile | ✅ | every category has cards |
| `GAL-desktop-01` | Gallery renders its case-study cards | `/gallery/` | desktop | ✅ | 23 cards, 10 filter buttons |
| `GAL-desktop-F-all` | Filter 'All' shows the right cards | `/gallery/` | desktop | ✅ | 23/23 cards visible, active buttons=1 |
| `GAL-desktop-F-slow-motion` | Filter 'Slow Motion' shows the right cards | `/gallery/` | desktop | ✅ | 3/23 cards visible, active buttons=1 |
| `GAL-desktop-F-family-tribute` | Filter 'Family Tribute' shows the right cards | `/gallery/` | desktop | ✅ | 3/23 cards visible, active buttons=1 |
| `GAL-desktop-F-family-message` | Filter 'Family Message' shows the right cards | `/gallery/` | desktop | ✅ | 2/23 cards visible, active buttons=1 |
| `GAL-desktop-F-ai-video-generator` | Filter 'AI Films' shows the right cards | `/gallery/` | desktop | ✅ | 3/23 cards visible, active buttons=1 |
| `GAL-desktop-F-wedding-trailer` | Filter 'Trailers' shows the right cards | `/gallery/` | desktop | ✅ | 3/23 cards visible, active buttons=1 |
| `GAL-desktop-F-pet-wedding` | Filter 'Pet Videos' shows the right cards | `/gallery/` | desktop | ✅ | 3/23 cards visible, active buttons=1 |
| `GAL-desktop-F-multilingual` | Filter 'Multilingual' shows the right cards | `/gallery/` | desktop | ✅ | 2/23 cards visible, active buttons=1 |
| `GAL-desktop-F-cartoon-style` | Filter 'Animated Style' shows the right cards | `/gallery/` | desktop | ✅ | 2/23 cards visible, active buttons=1 |
| `GAL-desktop-F-meme-generator` | Filter 'Memes & GIFs' shows the right cards | `/gallery/` | desktop | ✅ | 2/23 cards visible, active buttons=1 |
| `GAL-desktop-02` | No filter category is empty | `/gallery/` | desktop | ✅ | every category has cards |

### 5.12 ORDER（11 条：通过 9 / 失败 2 / 警告 0 / 阻塞 0）

| 断言 ID | 用例 | 页面 | 视口 | 结果 | 观测 |
|---|---|---|---|---|---|
| `ORDER-01` | Quote form exists with labelled fields | `/order/` | desktop | ❌ | 8 fields, unlabelled=[''] |
| `ORDER-02` | Native validation does not pre-empt the custom messages | `/order/` | desktop | ✅ | novalidate=yes |
| `ORDER-03` | Mandatory fields are marked required | `/order/` | desktop | ✅ | required fields: ['name', 'email', 'service', 'budget', 'details'] |
| `ORDER-04` | Submitting an empty form blocks submission and flags every empty required field | `/order/` | desktop | ✅ | flagged=['name', 'email', 'service', 'budget', 'details'] status='Please fix the following: Your Name is required; Email is required; Which service are you interested in? is required; Budget |
| `ORDER-05` | Error summary message is shown to the user | `/order/` | desktop | ✅ | #form-status: 'Please fix the following: Your Name is required; Email is required; Which service are you interested in? is required; Budget is required; Te' |
| `ORDER-06` | Focus moves to the first invalid field | `/order/` | desktop | ✅ | activeElement=#name |
| `ORDER-07` | Malformed e-mail is rejected with an inline message | `/order/` | desktop | ✅ | aria-invalid=true class='error' status='Please fix the following: Your Name is required; Which service are you interested in? is required; Budget is required; T' |
| `ORDER-08` | Error state clears as the user corrects the field | `/order/` | desktop | ✅ | aria-invalid after typing=None |
| `ORDER-09` | A complete submission can be composed | `/order/` | desktop | ✅ | filled: ['name', 'email', 'service', 'budget', 'details'] |
| `ORDER-10` | Valid submission reaches the success page with a reference ID | `/order/` | desktop | ❌ | final=http://127.0.0.1:8788/api/quote reference='' copyButton=False |
| `ORDER-ERR` | No uncaught JS errors during the whole order flow | `/order/` | desktop | ✅ | errors=[] |

### 5.13 SUCCESS（1 条：通过 1 / 失败 0 / 警告 0 / 阻塞 0）

| 断言 ID | 用例 | 页面 | 视口 | 结果 | 观测 |
|---|---|---|---|---|---|
| `SUCCESS-01` | Success page renders cleanly with a malformed reference | `/success/` | desktop | ✅ | ref='—' copyHidden=True errors=[] |

### 5.14 SEARCH（5 条：通过 4 / 失败 1 / 警告 0 / 阻塞 0）

| 断言 ID | 用例 | 页面 | 视口 | 结果 | 观测 |
|---|---|---|---|---|---|
| `SEARCH-01` | Search page exposes a query field | `/search/` | desktop | ✅ | input=#q name=q |
| `SEARCH-02` | Enter submits the query and returns results | `/search/` | desktop | ✅ | url=http://127.0.0.1:8788/search/?q=wedding+video links=1 snippet='Skip to main content Services ▾ Gallery Blog Resources Free Tools About Pricing Get a Quot' |
| `SEARCH-03` | A no-result query explains itself instead of showing a blank page | `/search/` | desktop | ❌ | links=1 empty-state-text=True snippet='Skip to main content Services ▾ Gallery Blog Resources Free Tools About Pricing Get a Quot' |
| `SEARCH-04` | Empty query is handled without an error page | `/search/` | desktop | ✅ | url=/search/ navigated=False |
| `SEARCH-05` | Query survives the round-trip (input is repopulated) | `/search/` | desktop | ✅ | input value after search='wedding video' |

### 5.15 BLOG（8 条：通过 8 / 失败 0 / 警告 0 / 阻塞 0）

| 断言 ID | 用例 | 页面 | 视口 | 结果 | 观测 |
|---|---|---|---|---|---|
| `BLOG-01` | Blog index lists its articles | `/blog/` | mobile | ✅ | 101 distinct article links, 100 card-like nodes, 0 pagination links, h1='Wedding Video Blog: 100+ Articles in 11 Languages ' |
| `BLOG-02` | First article link resolves | `/blog/` | mobile | ✅ | /blog/ -> 200 |
| `BLOG-mobile-03` | Table of contents anchors all resolve | `/blog/` | mobile | ✅ | 0 TOC links, [] dead: [] |
| `BLOG-mobile-04` | Article has substance and related-navigation | `/blog/` | mobile | ✅ | ~3975 words, reading-time label='11 min read', related links=0 |
| `BLOG-mobile-05` | No uncaught JS errors on the article | `/blog/` | mobile | ✅ | errors=[] |
| `BLOG-desktop-03` | Table of contents anchors all resolve | `/blog/` | desktop | ✅ | 0 TOC links, [] dead: [] |
| `BLOG-desktop-04` | Article has substance and related-navigation | `/blog/` | desktop | ✅ | ~3998 words, reading-time label='11 min read', related links=0 |
| `BLOG-desktop-05` | No uncaught JS errors on the article | `/blog/` | desktop | ✅ | errors=[] |

### 5.16 404（2 条：通过 1 / 失败 1 / 警告 0 / 阻塞 0）

| 断言 ID | 用例 | 页面 | 视口 | 结果 | 观测 |
|---|---|---|---|---|---|
| `404-01` | Unknown URLs return a real 404 status | `/definitely-not-a-real-page-ux-test/` | mobile | ✅ | status=404 |
| `404-02` | 404 page keeps users on-site with guidance | `/definitely-not-a-real-page-ux-test/` | mobile | ❌ | body starts: "Skip to main content 404 — Try AI Wedding Video from $9.9 (11 Services) The page you're looking for doesn't ex" |

### 5.17 NAVFLOW（6 条：通过 3 / 失败 3 / 警告 0 / 阻塞 0）

| 断言 ID | 用例 | 页面 | 视口 | 结果 | 观测 |
|---|---|---|---|---|---|
| `NAVFLOW-01` | Every header/footer link returns 200 | `/` | desktop | ✅ | 22 distinct links clicked-checked, failures=[] |
| `NAVFLOW-02-1` | Header link 'Services ▾' lands on its own page | `/` | desktop | ❌ | clicked /#services -> / · h1='AI Wedding Video Generator from Photos' |
| `NAVFLOW-02-2` | Header link 'Slow Motion' lands on its own page | `/` | desktop | ❌ | TimeoutError: Page.click: Timeout 30000ms exceeded. Call log: waiting for locator(".main-nav a[href=\"/services/video-enhancement/slow-motio |
| `NAVFLOW-02-3` | Header link 'Vintage Restoration' lands on its own page | `/` | desktop | ❌ | TimeoutError: Page.click: Timeout 30000ms exceeded. Call log: waiting for locator(".main-nav a[href=\"/services/video-enhancement/vintage-re |
| `NAVFLOW-03` | Browser Back returns to the previous page | `/` | desktop | ✅ | after back: / |
| `NAVFLOW-04` | Deep pages expose a breadcrumb trail | `/blog/` | desktop | ✅ | {'present': True, 'text': 'Home› Blog', 'links': 1} |

## 6. 站内链接体检

- 检查目标数：**171**
- 4xx/5xx 或不可达：**1**
- 发生重定向：**0**（内部链接不应产生额外跳数）

| 目标 | 状态 | 被哪些页面引用 |
|---|---:|---|
| `/blog/elopement-wedding-video-guide/` | 404 | `/zh/blog/affordable-wedding-video-ai/` |

## 7. 缺陷取证截图

| 页面 | 横向溢出 | 截图 |
|---|---:|---|
| `/ai-wedding-video-generator/` | 666px | `qa/ux/results/shots/overflow-ai-wedding-video-generator-390.png` |
| `/tools/wedding-seating-chart-maker/` | 592px | `qa/ux/results/shots/overflow-tools_wedding-seating-chart-maker-390.png` |
| `/tools/compress-wedding-photos/` | 291px | `qa/ux/results/shots/overflow-tools_compress-wedding-photos-390.png` |
| `/pricing/` | 11px | `qa/ux/results/shots/overflow-pricing-390.png` |
| `/services/absence-compensation/family-tribute/` | 293px | `qa/ux/results/shots/overflow-services_absence-compensation_family-tribute-390.png` |
| `/tools/wedding-video-invitation-maker/` | 287px | `qa/ux/results/shots/overflow-tools_wedding-video-invitation-maker-390.png` |

## 8. 生产环境交叉验证

为区分“本地环境特有”与“线上真实缺陷”，对生产站点做了少量限速探测：

| URL | 状态 | 内容编码 | 传输字节 | CF 缓存 |
|---|---:|---|---:|---|
| `https://weddingai.video/` | 200 | br | 20093 | DYNAMIC |
| `https://weddingai.video/pricing/` | 200 | br | 12875 | DYNAMIC |
| `https://weddingai.video/ai-wedding-video-generator/` | 200 | br | 9837 | DYNAMIC |
| `https://weddingai.video/success/` | 200 | br | 7621 | DYNAMIC |
| `https://weddingai.video/zh/` | 200 | br | 19726 | DYNAMIC |
| `https://weddingai.video/blog/` | 200 | br | 30907 | DYNAMIC |
| `https://weddingai.video/cdn-cgi/scripts/5c5dd728/cloudflare-static/email-decode.min.js` | 200 | - | - | - |

**如何读这张表**：线上 HTML 全部经 brotli 压缩，传输体积只有 7.6–30.9 KB，第 4 章页面矩阵里的“体积(KB)”是本地未压缩、无边缘缓存的数值（含图片与视频），两者不可直接比较；本页只用于确认线上可达、压缩开启、CF 缓存状态为 DYNAMIC（由 Worker 动态响应）。唯一的结论是：`/cdn-cgi/…/email-decode.min.js` 在线上返回 200，因此成功页那条本地 404 属环境差异，无需修复。

## 9. 已核实的误报（不计入缺陷）

测试过程中有以下断言报警，经逐条复核为测试方法或本地环境造成，**不计为站点缺陷**，记录在此以免复测时重复排查：

| 报警 | 为什么是误报 | 复核方式 |
|---|---|---|
| 11 个站内链接 404（`/zh/`、`/pt/order/` 等） | 中间件只重写 **GET** 请求，用 HEAD 探测时返回 404；同一 URL 用 GET 探测均为 200 | 已改用 GET 复测：171 个目标中仅 1 个真死链 |
| `NAV-08` 焦点逃出菜单（24/24 次 Tab 逃逸） | 测试脚本在菜单已展开时又点了一次汉堡，把菜单**关闭**后再 Tab。在菜单确认处于展开状态下重测：5 种机型均 **0/23 次逃逸**，焦点循环正常 | `qa/ux/nav_probe2.py` |
| `ORDER-01` 存在无标签字段 | 唯一“无标签”的字段是反垃圾蜜罐 `#botcheck`，它位于 `display:none` 的容器内且 `tabindex=-1`，本就不暴露给辅助技术；8 个真实字段全部有 label | `qa/ux/verify_bugs.py` |
| `PRICE-02` 定价页没有套餐卡 | 测试选择器写的是 `[class*="pricing-card"]`，而实际类名是 `.pricing-tier`；页面本身 5 个下单入口正常 | 源码核对 + 运行时 class 列表 |
| `SEARCH-02/03` 搜索无结果 | 统计口径错用了 `a[href*="/blog/"]`，而搜索结果指向 `/services/*`。实际渲染 12 条结果，空查询有 “No matches” 提示（真正的缺陷是链接指向，见 UX-002） | `qa/ux/verify_bugs.py` |
| `404-02` 404 页缺少引导 | 断言要求页面文本包含 `/` 字符；404 页本身文案完整（含返回首页与下单入口） | 运行时 DOM 复核 |
| `/success/` 加载 `/cdn-cgi/…/email-decode.min.js` 404 | 本地 miniflare 不提供该 Cloudflare 边缘脚本；**线上返回 200**，属本地环境特有 | 生产探测（见第 8 章） |
| `NAVFLOW-02-1` 点击「Services ▾」落地路径不符 | 该链接是 `/#services` 页内锚点，落地路径本就是 `/`；实测首页确实存在 `#services` 锚点，功能正常 | 源码 id 清单核对 |
| `NAVFLOW-02-2/3` 点击服务子菜单超时 | 这些链接位于需要悬停展开的下拉里，未展开时不可见，自动化点击自然超时；`NAVFLOW-01` 已确认这 22 个链接全部返回 200 | 批量 HTTP 校验 |

另说明：本地 miniflare 在长时间高并发扫描下会崩溃退出，已用守护进程（`qa/ux/serve-watch.ps1`）自动重启，崩溃期间的记录全部作废重跑，未混入本报告数据。

## 10. 附录：复测方法

```powershell
# 1) 启动本地同构环境（守护进程，崩溃自动重启）
powershell -ExecutionPolicy Bypass -File qa\ux\serve-watch.ps1 -Port 8788

# 2) 页面级扫描（EN 全站 / 多语言原型 / 特殊页）
cd qa\ux
python sweep.py --set en --viewports mobile --out sweep-en.json
python sweep.py --set lang-archetypes --viewports mobile,desktop --out sweep-archetypes.json
python sweep.py --set special --viewports mobile --out sweep-special.json
python sweep.py --links-only

# 3) 交互测试套件
python interactions.py

# 4) 取证截图 + 生产交叉验证
python evidence.py

# 5) 重新生成本报告
python report.py
```

原始数据：`qa/ux/results/*.json`；截图：`qa/ux/results/shots/`。
