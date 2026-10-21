"""Curated defect narratives for the UX / interaction test report.

Every entry is backed by data in qa/ux/results/*.json - the numbers quoted here
come from the runs recorded in this repository.
"""

FINDINGS = [
    # ------------------------------------------------------------------ P0
    {
        "id": "UX-001",
        "severity": "P0",
        "title": "移动端主菜单高度 999px 且不可滚动：真机上「Get a Quote」等主要入口完全够不到",
        "impact": "所有手机用户（按视口高度递增，4 款主流机型受影响）",
        "pages": "全站（任何页面的汉堡菜单）",
        "summary": "菜单面板 `overflow-y:visible` + 头部 `position:sticky`，面板底部 227–404px 落在屏幕外且无法滚动到",
        "symptom": "390×844 视口下 `.main-nav` 面板 top=72 / bottom=1071（高 999px），而视口只有 844px；"
                   "`overflow-y: visible`、`scrollHeight == clientHeight`（不可滚动）；页面本身此时也无法滚动"
                   "（实测 scrollY 恒为 0），面板被 sticky 头部锚定。实测各机型落在屏幕外、无法点击的菜单项："
                   "iPhone SE 375×667 → **9 项**（View all services、Gallery、Blog、Resources、Free Tools、About、"
                   "Pricing、**Get a Quote**、语言切换器）；Galaxy S8 360×740 → 8 项；"
                   "iPhone 12 390×844 → 5 项（Free Tools、About、Pricing、**Get a Quote**、语言切换器）；"
                   "iPhone 14 Pro Max 430×932 → 3 项；iPad mini 768×1024 → 1 项（语言切换器）。",
        "root_cause": "`.main-nav` 在移动端展开为绝对定位的全宽面板，但没有 `max-height: 100vh` / `overflow-y: auto`；"
                      "同时头部是 `position: sticky`，面板随头部固定，页面滚动无法把它带回视口内。"
                      "面板固定高度 999px 也说明其中的“服务”下拉分组（11 个子项）被强制全部展开。",
        "steps": [
            "以 375×667（iPhone SE）打开首页",
            "点击右上角汉堡菜单",
            "向下看：Gallery / Blog / Resources / Free Tools / About / Pricing / Get a Quote 均在屏幕外",
            "尝试滚动页面（scrollY 始终为 0）或在面板内滚动（overflow-y: visible）——都无法到达",
        ],
        "evidence": "`qa/ux/nav_probe2.py` 输出（5 种机型实测）；交互断言 `NAV-03`、`NAV-07`",
        "fix": "给移动端面板加 `max-height: calc(100dvh - 72px); overflow-y: auto; -webkit-overflow-scrolling: touch;`，"
               "并把“服务”子菜单改为可折叠（默认收起），使面板高度控制在 ~480px；"
               "同时保证语言切换器始终在首屏可见（可放在面板顶部固定区）。",
    },
    {
        "id": "UX-002",
        "severity": "P0",
        "title": "搜索结果链接全部指向不存在的域名（`//services/...`），搜索链路完全断裂",
        "impact": "站内搜索的全部 12 条结果",
        "pages": "`/search/`（任意查询词）",
        "summary": "模板写成 `href=\"/${item.url}\"`，而 `item.url` 本身已以 `/` 开头，拼成协议相对 URL",
        "symptom": "在 `/search/?q=wedding+video` 渲染出 12 条结果，但每条链接的 href 都是双斜杠开头，"
                   "浏览器解析为协议相对地址："
                   "`//services/personalization/ai-video-generator/` → `http://services/personalization/ai-video-generator/`、"
                   "`//about/` → `http://about/`、`//services/` → `http://services/`……"
                   "这些主机名不存在，用户点击后会跳到无法解析的地址，站内搜索的价值归零。",
        "root_cause": "`search/index.html:504` 模板字符串 `<a href=\"/${item.url}\">`，"
                      "而索引数组 `INDEX` 中的 `url` 字段本身已经是 `/services/...` 形式。",
        "steps": [
            "打开 `/search/?q=wedding+video`",
            "查看任意结果链接：`a.search-result h3 a` 的 `getAttribute('href')` 为 `//services/...`",
            "点击后会离开本站",
        ],
        "evidence": "`qa/ux/verify_bugs.py` 输出；源码 `search/index.html:504`；"
                    "同一段代码还把 `</li>` 写成了 `<li></li>`（无效标签）",
        "fix": "改为 `<a href=\"${item.url}\">`（去掉多余斜杠），并把 `INDEX` 中的 url 统一成不带前导斜杠或带斜杠的其中一种；"
               "同时修正未闭合的 `<li>`。建议把本条纳入 CI：解析搜索结果链接并断言其 origin 与页面一致。",
    },
    {
        "id": "UX-003",
        "severity": "P0",
        "title": "CSP 的 img-src 未放行 blob:，5 个工具无法解码上传的照片，3 个完全不可用",
        "impact": "13 个免费工具中的 5 个（compress / crop / remove-background 完全失效，add-text / collage 无法预览）",
        "pages": "`/tools/compress-wedding-photos/`、`/tools/crop-wedding-photo-for-reels/`、"
                 "`/tools/remove-background-wedding-portrait/`、`/tools/add-text-to-wedding-photo/`、`/tools/wedding-photo-collage/`",
        "summary": "`fileToImage()` 用 `URL.createObjectURL()` 生成 blob: 图片，被 CSP 拒绝加载后误报“文件无法解码”",
        "symptom": "上传一张合法 JPEG（1600×1200，668KB，渐进式/EXIF 旋转/PNG/WebP 均试过）："
                   "文件列表出现该文件且缩略图元素存在，但 `naturalWidth === 0`（图片被拦截）；"
                   "点击主按钮后提示 **“Could not decode this file. Try a JPG, PNG, or WebP.”**。"
                   "3 个工具的主按钮永远不会产出结果（无下载链接、无 blob 输出），另 2 个工具画布停留在默认 300×150。",
        "root_cause": "`functions/_middleware.js:65` 的 CSP 为 "
                      "`img-src 'self' data: https://hm.baidu.com ...`，**没有 `blob:`**；"
                      "而 `js/tools/common.js:51 fileToImage()` 正是 `URL.createObjectURL(file)` → `img.src = blob:...`。"
                      "浏览器拦截后触发 `img.onerror`，被翻译成“文件无法解码”的误导性提示。"
                      "对照：`wedding-photo-book-planner` 用 `FileReader.readAsDataURL`（`data:` 已被放行）因此正常。",
        "steps": [
            "打开 `/tools/compress-wedding-photos/`，上传任意 JPG",
            "缩略图区域空白（`<img src=blob:...>` 的 `naturalWidth=0`）",
            "点击“Compress” → 状态栏出现 “Could not decode this file. Try a JPG, PNG, or WebP.”",
        ],
        "evidence": "`qa/ux/results/tool-verdicts.json`（13 个工具逐个实测）、`qa/ux/decode_probe.py`、"
                    "源码 `functions/_middleware.js:65` 与 `js/tools/common.js:51`",
        "fix": "在 CSP 的 `img-src`（如需处理 canvas 导出的图片预览，同时检查 `media-src`）加入 `blob:`；"
               "改完后需复核全部工具。另建议：解码失败时区分“文件损坏”和“被策略拦截”，"
               "并把真实原因写进控制台，避免再次出现误导性提示。",
    },

    # ------------------------------------------------------------------ P1
    {
        "id": "UX-004",
        "severity": "P1",
        "title": "邮件服务缺 key 时下单接口返回 500 纯文本，用户丢失参考号且看不到成功页",
        "impact": "报价表单提交链路（转化漏斗最末端）",
        "pages": "`/order/`（POST `/api/quote`）",
        "summary": "同一函数的“其他失败”分支会 303 到 `/success/?status=pending`，唯独缺 key 分支直接 500",
        "symptom": "本地复现：POST `/api/quote` → `500`，响应体为纯文本 "
                   "“Server is not configured to send email. Please email order@weddingai.video directly.”。"
                   "浏览器停在 `/api/quote`，既没有跳到 `/success/`，也没有展示前端生成的 `WA-YYYYMMDD-XXXX` 参考号"
                   "（`#reference-copy` 不会出现），用户只会看到一个裸错误页。",
        "root_cause": "`functions/api/quote.js:327-343`：`if (!apiKey) { … return new Response(..., {status: 500}) }`。"
                      "而同函数在 Resend 返回非 2xx（第 387 行）与 fetch 抛异常时都会 "
                      "`redirect303(origin_base, successUrl(\"pending\"))`，前端 `js/main.js` 也已实现 `status=pending` 分支。"
                      "即前端已准备好降级路径，唯独缺 key 这一分支没走。",
        "steps": [
            "在未配置 `RESEND_API_KEY` 的环境打开 `/order/`，填写必填项并提交",
            "页面停在 `/api/quote`，显示纯文本 500",
        ],
        "evidence": "`qa/ux/verify_bugs.py` 的 POST 结果；源码 `functions/api/quote.js:328-343`；"
                    "对比分支 `quote.js:387`",
        "fix": "把缺 key 分支也改成 `redirect303(origin_base, successUrl(\"pending\"))`，"
               "让用户至少拿到参考号并看到“已收到、24 小时内回复”的页面（lead 已经在 KV 里，不会丢单）；"
               "运维侧用 `/api/dead-letters` 或 cron 重试补发。",
    },
    {
        "id": "UX-005",
        "severity": "P1",
        "title": "俄语站点几乎完全未翻译：12 个关键页 94%–100% 正文仍是英文",
        "impact": "俄语全部转化页（首页、定价、下单、工具、博客、关于、资源、服务、案例库、成功页）",
        "pages": "`/ru/`、`/ru/pricing/`、`/ru/order/`、`/ru/blog/`、`/ru/about/`、`/ru/gallery/`、`/ru/resources/`、`/ru/services/`、`/ru/success/`、`/ru/tools/`",
        "summary": "`i18n/ru.json` 只填充了 7.3% 的键，中间件回落英文，俄语用户看到的是英文站点",
        "symptom": "浏览器实测 `/ru/blog/` 正文 17,626 个拉丁字符、仅 157 个西里尔字符（latinRatio 0.99）；"
                   "`/ru/about/`、`/ru/success/` 为 100% 拉丁字符（完全未翻译）；`/ru/pricing/` 0.96、"
                   "`/ru/order/` 0.94、`/ru/gallery/` 0.98、`/ru/resources/` 0.99、`/ru/services/` 0.96。"
                   "另有 `/ja/blog/` 100% 拉丁、`/th/gallery/` 100%、`/th/order/` 100%。",
        "root_cause": "`i18n/ru.json` 仅 3,235 / 44,131 个键有值（7.3%），而其余语言均 ≥ 60,000 键。"
                      "`functions/_middleware.js` 找不到键时直接回落到 HTML 中的英文原文，因此页面能正常打开、"
                      "不报错，但内容是英文——这正是纯静态扫描工具看不到的失效模式。",
        "steps": [
            "打开 `http://127.0.0.1:8788/ru/blog/`",
            "统计 `document.body.innerText` 的字符构成：拉丁 17,626 / 西里尔 157",
        ],
        "evidence": "`qa/ux/results/sweep-archetypes.json` 中 24 条 ru 记录 `langOK=false`；"
                    "`qa/ux/rootcause.py`：ru 3,235/44,131 键（7.3%），其余语言均 ≥ 60,000",
        "fix": "① 短期：在语言切换器中暂时下架俄语入口，或对未翻译页面加明显提示，"
               "避免用户误以为站点只支持英语；② 按 v10 重译计划补齐 ru 词典；"
               "③ 把“实际渲染语言 vs URL 语言”做成 CI 检查（本次探针已实现，可直接复用 `qa/ux/sweep.py` 的 `langOK` 判据）。",
    },
    {
        "id": "UX-006",
        "severity": "P1",
        "title": "移动端横向溢出：42/139 个英文页面 + 11 种语言共 75 条记录出现整页左右滚动",
        "impact": "全部工具页（13/14）、全部服务页（14/14）、首页、定价、案例库、资源页、AI 生成器落地页",
        "pages": "`/ai-wedding-video-generator/`、`/tools/*`、`/services/*`、`/pricing/`、`/`、`/gallery/`、`/resources/`、10 篇文章及其多语言版本",
        "summary": "宽表格没有可横向滚动的容器，390px 视口下整页被撑宽最多 927px",
        "symptom": "在 390×844（iPhone 14）视口下打开页面，`documentElement.scrollWidth - clientWidth` 大于 2px，"
                   "整页可以左右拖动，正文与页脚被推到屏幕外。溢出最严重的页面："
                   "`/de/ai-wedding-video-generator/` 927px、`/es/ai-wedding-video-generator/` 744px、"
                   "`/pt/ai-wedding-video-generator/` 743px、`/ai-wedding-video-generator/` 666px、"
                   "`/tools/wedding-seating-chart-maker/` 592px、`/fr/tools/compress-wedding-photos/` 520px。",
        "root_cause": "三类元素撑破容器：① 对比表格 `.comparison-table`（实测 992–1293px）与定价全表 "
                      "`.full-pricing-table`（实测 626–886px）只有 `width:100%`，表格的 min-content 宽度会把容器撑开，"
                      "而外层没有 `overflow-x:auto` 的滚动容器；② `/tools/wedding-seating-chart-maker/` 的 "
                      "`.seating-panel` / `.seating-layout-wrap` 为 `position:sticky` 的固定宽度布局（958px），"
                      "在窄屏没有切换为纵向堆叠；③ `/tools/wedding-video-invitation-maker/` 的 `.wa-tool-card` 实测 426px。"
                      "非英语页面更严重，因为德语/西语/法语译文更长。",
        "steps": [
            "以 390×844 视口打开 `http://127.0.0.1:8788/ai-wedding-video-generator/`",
            "执行 `document.documentElement.scrollWidth - document.documentElement.clientWidth`",
            "观察返回值 666px，并可见横向滚动条",
        ],
        "evidence": "扫描结果 `qa/ux/results/sweep-en.json`：EN 139 页中 42 页溢出；"
                    "`sweep-archetypes.json`：11 语言 × 15 原型 × 2 视口中 75 条记录溢出；"
                    "取证截图 `qa/ux/results/shots/overflow-*.png`",
        "fix": "① 给所有宽表格套一层 `overflow-x:auto` 的滚动容器（或 `table-layout:fixed` + 允许换行）；"
               "② 窄屏（≤768px）为 `.seating-layout-wrap` 改为单列、取消 `.seating-panel` 的 sticky；"
               "③ `.wa-tool-card` 加 `max-width:100%`；"
               "④ 不建议用 `html,body{overflow-x:hidden}` 掩盖问题。",
    },
    {
        "id": "UX-007",
        "severity": "P1",
        "title": "2 个工具的上传控件对键盘与读屏用户完全不可达",
        "impact": "save-the-date-maker、wedding-photo-book-planner",
        "pages": "`/tools/save-the-date-maker/`、`/tools/wedding-photo-book-planner/`（及其 10 个语言版本）",
        "summary": "`input[type=file]` 被 `display:none`，代理元素又没有 `tabindex`/`role`",
        "symptom": "这两个页面的 `#dropzone` 没有 `tabindex`、没有 `role=\"button\"`，"
                   "同时 `styles/tools.css:62` 的 `.wa-tool-dropzone input[type=\"file\"] { display:none }` "
                   "让原生输入既不可聚焦也不被读屏播报；键盘用户 Tab 遍历全页找不到任何能打开文件选择器的控件。"
                   "（其余 8 个上传类工具已正确设置 `tabindex=0 role=button`，本项只针对这 2 个页面。）",
        "root_cause": "这两个工具的模板没有跟上其余工具的 a11y 修复：拖放区缺少可聚焦语义与键盘事件绑定。",
        "steps": [
            "打开 `/tools/save-the-date-maker/`",
            "反复按 Tab，焦点永远到不了上传区",
            "检查 `#file-input` 计算样式为 `display: none`",
        ],
        "evidence": "交互断言 `TOOL-save-the-date-maker-KBD`、`TOOL-wedding-photo-book-planner-KBD`（FAIL）；"
                    "CSS `styles/tools.css:62`",
        "fix": "与其余工具对齐：`<div id=\"dropzone\" role=\"button\" tabindex=\"0\" aria-label=\"上传照片\">` "
               "并绑定 Enter/Space；或用 `<label for=\"file-input\">` 包裹整个拖放区。",
    },

    # ------------------------------------------------------------------ P2
    {
        "id": "UX-008",
        "severity": "P2",
        "title": "全部 139 个英文页面存在小于 24×24px 的点击热区",
        "impact": "全站（页脚评分徽章、面包屑等），老年用户与运动障碍用户点击困难",
        "pages": "全部页面（139/139 英文页 + 11 种语言页面均命中）",
        "summary": "页脚徽章仅 15px 高、面包屑链接 16px，低于 WCAG 2.2 AA 最小目标尺寸",
        "symptom": "`a.footer-badge.footer-badge-secondary` 实测 181×15px（“⭐ 4.9/5 · 9,400+ couples”），"
                   "面包屑链接 `nav.breadcrumb a` 实测 37×16px。非英语页面最多可达 25 个。",
        "root_cause": "`.footer-badge` 使用较小的字号与紧凑行高，未预留最小点击区域；"
                      "面包屑通过 `font-size:0.875rem` + 行内排版实现，没有 `padding`/`min-height`。",
        "steps": [
            "390px 视口打开任意页面",
            "量取 `.footer-badge` 的 `getBoundingClientRect()`：181×15",
        ],
        "evidence": "扫描探针 `probe.tiny24`，样本见报告第 4 章页面矩阵",
        "fix": "给这两类元素加 `min-height:24px; min-width:24px; display:inline-flex; align-items:center; padding:4px 8px;`"
               "（页脚徽章建议直接提升到 44px）。",
    },
    {
        "id": "UX-009",
        "severity": "P2",
        "title": "5 个语言版本的下单页把非法 `<span>` 写进了 `<select>`，浏览器直接丢弃该节点",
        "impact": "西班牙语、日语、葡萄牙语、俄语、泰语的下单页",
        "pages": "`/es/order/`、`/ja/order/`、`/pt/order/`、`/ru/order/`、`/th/order/`",
        "summary": "控制台报 29 次 “A span tag was parsed inside of a <select>…”，`<select>` 只允许 `<option>`/`<optgroup>`",
        "symptom": "这 5 个页面的控制台稳定输出 HTML 解析告警，说明响应 HTML 中 `<select>` 内部出现了 `<span>`，"
                   "浏览器在解析阶段就把它从文档中移除。EN 版本没有该告警，说明是中间件按语言改写 `<select>` 内容时引入的。"
                   "经运行时复核，4 个 `<select>` 的选项数量与内容仍完整，用户可选，但代码路径存在隐患。",
        "root_cause": "`functions/_middleware.js` 在替换 `<option>`/`<optgroup>` 文本时保留了原 HTML 片段"
                      "（`<span data-i18n=...>`），只对部分语言生效。",
        "steps": [
            "打开 `/es/order/`，打开 DevTools Console",
            "看到 “A span tag was parsed inside of a <select> which was not inserted into the document”",
        ],
        "evidence": "`qa/ux/results/sweep-archetypes.json` consoleErrors，分类统计 29 条，命中 5 个页面",
        "fix": "中间件改写 `<select>` 内节点时只替换 `option.textContent`，不要回写包含标签的 HTML；"
               "并在构建期校验 `select` 的子元素只能是 `option`/`optgroup`。",
    },
    {
        "id": "UX-010",
        "severity": "P2",
        "title": "重型 i18n 页面本地加载超时，提示线上存在 Workers CPU 超限风险",
        "impact": "泰语/印地语/日语/葡萄牙语等重型页面（首页、工具中心、博客、资源、落地页）",
        "pages": "`/pt/resources/`、`/th/success/`、`/th/blog/…`、`/hi/tools/`、`/ja/ai-wedding-video-generator/` 等",
        "summary": "本地 miniflare 下 6 条记录超过 45s 超时；多语言页面本地 load 普遍 >5s",
        "symptom": "扫描中 6 条记录触发 `Page.goto: Timeout 45000ms exceeded`；"
                   "按语言统计本地 `load > 5s` 的页面占比：zh 28/28、hi 27/27、ar 26/28、th 24/25、ja 26/27，"
                   "而英文页仅 2/175。",
        "root_cause": "中间件需要为每个非英语页面加载 1MB 级 i18n JSON 并对整页做逐 `data-i18n` 属性替换"
                      "（`/ar/blog/wedding-video-inspiration/` 单页有 483 个 `data-i18n` 属性）。"
                      "本地无缓存且单 isolate，等价于线上首次访问的冷启动成本。",
        "steps": [
            "查看 `qa/ux/results/sweep-archetypes.json` 中 `error` 字段非空的记录",
            "按语言统计 `probe.load > 5000` 的记录数",
        ],
        "evidence": "语言健康度统计（`qa/ux/lang_report.py`）",
        "fix": "沿用已有的 `getCachedProcessedBody` 5 分钟 `caches.default` 缓存；"
               "把日期多样化等 URL 确定性逻辑移到构建期；或升级 Workers 计划提高 CPU 上限。",
    },

    # ------------------------------------------------------------------ P3
    {
        "id": "UX-011",
        "severity": "P3",
        "title": "两篇博客文章存在重复 DOM id，锚点与目录会指向错误位置",
        "impact": "`/blog/affordable-wedding-video-ai/`、`/blog/ai-editor-vs-traditional-editing/`（及俄语版）",
        "pages": "上述 2 篇 + `/ru/` 对应版本",
        "summary": "id `blog-serp-comparison-serp_comparison` 在同一页出现多次",
        "symptom": "页面内出现重复 id，读屏软件与 `getElementById` 只会命中第一个，"
                   "SERP 对比区块的锚点跳转与目录高亮会错位。",
        "root_cause": "文章模板片段被复用/复制时未对 id 加唯一后缀。",
        "steps": ["打开任一受影响页面", "统计所有 `[id]` 出现次数"],
        "evidence": "`probe.dupIds` 字段",
        "fix": "为该区块 id 加上文章 slug 或计数器后缀；并在构建期加“全站重复 id”门禁。",
    },
    {
        "id": "UX-012",
        "severity": "P3",
        "title": "一个工具页引用被 CSP 拦截的 Google Fonts，控制台报错且字体与其余 12 个工具不一致",
        "impact": "`/tools/wedding-photo-collage/`",
        "pages": "`/tools/wedding-photo-collage/`",
        "summary": "`style-src 'self' 'unsafe-inline'` 拒绝了 `fonts.googleapis.com`",
        "symptom": "控制台：“Refused to load the stylesheet 'https://fonts.googleapis.com/css2?family=Cormorant+Garamond…'”，"
                   "该页回落到本地字体栈，其余 12 个工具页没有这条外链。",
        "root_cause": "该工具页模板里残留了 Google Fonts `<link>`，而站点 CSP 只允许同源样式（其余页面使用自托管字体）。",
        "steps": ["打开 `/tools/wedding-photo-collage/`", "查看 Console 的 stylesheet 拒绝信息"],
        "evidence": "consoleErrors，仅此 1 页命中",
        "fix": "删除该页的 Google Fonts `<link>`，改用与其余工具页一致的本地字体变量；"
               "或在 CSP 中显式放行 `https://fonts.googleapis.com` 并加 `font-src https://fonts.gstatic.com`。",
    },
    {
        "id": "UX-013",
        "severity": "P3",
        "title": "站内死链：`/blog/elopement-wedding-video-guide/` 在中文博客中被引用但不存在",
        "impact": "中文博客文章 `/zh/blog/affordable-wedding-video-ai/`",
        "pages": "`/blog/elopement-wedding-video-guide/`（被 `/zh/blog/affordable-wedding-video-ai/` 引用）",
        "summary": "GET 与 HEAD 均返回 404；实际存在的文章是 `/blog/elopement-video-ideas/`",
        "symptom": "点击中文博客里的相关推荐会进入 404 页面。",
        "root_cause": "翻译时沿用了旧 slug；`_redirects` 里只有 `/blog/elopement-video-ideas` 的规则，没有 "
                      "`elopement-wedding-video-guide` 的映射。",
        "steps": ["打开 `/zh/blog/affordable-wedding-video-ai/`", "点击指向 `/blog/elopement-wedding-video-guide/` 的链接"],
        "evidence": "全局内链体检 171 个目标，唯一死链",
        "fix": "把链接改为 `/blog/elopement-video-ideas/`，或在 `_redirects` 增加 "
               "`/blog/elopement-wedding-video-guide/ 301 /blog/elopement-video-ideas/`。",
    },
    {
        "id": "UX-014",
        "severity": "P3",
        "title": "`_redirects` 有 36 条非法规则、210 行被跳过，36 条历史链接规则实际未生效",
        "impact": "旧 URL / 外部链接 / Google 索引中的历史地址",
        "pages": "`_redirects`（第 677–831 行区段）",
        "summary": "规则使用 404 作为状态码（非法），且超出 Workers 100 条动态规则上限的部分被整体丢弃",
        "symptom": "`wrangler pages dev` 启动时输出：`Found 36 invalid redirect rules … Valid status codes are 200, "
                   "301, 302, 303, 307, or 308. Got 404.` 以及 "
                   "`Maximum number of dynamic rules supported is 100. Skipping remaining 210 lines of file.`。"
                   "另有 `_headers` 中 `/blog/*/*.html` 规则非法（只允许一个通配符）被跳过。",
        "root_cause": "把“强制返回 404 页”误写成重定向规则；同时通配/占位规则数量超过平台上限。",
        "steps": ["启动 `wrangler pages dev`", "读取启动告警"],
        "evidence": "`qa/ux/results/dev-stdout.log` / `dev-stderr.log`",
        "fix": "需要屏蔽的路径改用 `_redirects` 之外的机制（例如 Pages 404 页面或 Workers 内判断）；"
               "把 100 条以内的关键重定向放在文件顶部，其余收敛到 Workers 代码里处理。",
    },

    # ------------------------------------------------------------------ P4
    {
        "id": "UX-015",
        "severity": "P4",
        "title": "成功页引用 Cloudflare 邮件混淆脚本 `/cdn-cgi/…/email-decode.min.js`",
        "impact": "全部 11 个语言版本的 `/success/` 页面",
        "pages": "`/success/`、`/zh/success/` … `/th/success/`",
        "summary": "本地返回 404 并报 CSP 拒绝执行；属本地环境特有现象还是线上缺陷需以生产验证为准",
        "symptom": "本地 21 条记录出现同源 404 与 “Refused to execute script from …/cdn-cgi/scripts/…/email-decode.min.js”。",
        "root_cause": "邮件地址依赖 Cloudflare Email Address Obfuscation 注入的脚本，本地 miniflare 不提供该路径。",
        "steps": ["打开 `/success/`", "查看 Console 与 Network"],
        "evidence": "`badResponses` 中 21 条同源 404，全部指向同一脚本",
        "fix": "若线上正常则无需改动（见报告第 8 章生产验证）；否则改为服务端渲染邮箱或使用 `mailto:` 明文。",
    },
    {
        "id": "UX-016",
        "severity": "P4",
        "title": "语言选择器字号 13.3px，iOS 聚焦时会自动放大页面",
        "impact": "所有页面的 `#wa-lang-select`",
        "pages": "全站",
        "summary": "输入类控件字号小于 16px，iOS Safari 聚焦时强制缩放",
        "symptom": "实测 `#wa-lang-select` 的 `font-size: 13.3333px`，低于 iOS 建议的 16px；"
                   "用户在移动端聚焦语言下拉时页面会被放大且需要手动缩回。",
        "root_cause": "`.wa-lang-select` 未设置最小字号。",
        "steps": ["iOS Safari 打开任意页面", "点击右上角语言下拉"],
        "evidence": "交互断言 `A11Y-04`（WARN）",
        "fix": "给 `#wa-lang-select` 设置 `font-size: 16px`（或在移动端断点下不小于 16px）。",
    },
]

