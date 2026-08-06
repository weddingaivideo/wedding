# WeddingAI.video — CSP Nonce-Only 修复报告

**日期:** 2026-08-04
**审计来源:** Semrush / 类似 SEO+安全审计工具
**原审计问题:** `script-src` 含 `'unsafe-inline'`，nonce 保护形同虚设，XSS 可直接绕过（**高**）
**生产域名:** https://weddingai.video
**部署 URL (preview):** https://77282dba.weddingai-video.pages.dev

---

## 1. 修复方案：从 middleware 注入 `<meta http-equiv="Content-Security-Policy">`

**为什么不是简单从 _headers 收紧？**

CF Pages 的 middleware 改不动 response header（之前 2026-08-04 已验证多种 pattern 都失败）。
但 middleware **能改 HTML body**。所以正确做法是把 per-request nonce 写进 HTML 而非 header。

```html
<head>
    <meta http-equiv="Content-Security-Policy"
          content="default-src 'self';
                   script-src 'self' 'nonce-XXX' 'strict-dynamic' https://www.googletagmanager.com ...;
                   style-src 'self' 'unsafe-inline';
                   ...; report-to csp-endpoint">
    <meta charset="UTF-8">
    ...
```

浏览器对 meta-delivered CSP 的支持是完善的（Chrome 40+, Firefox 45+, Safari 15.4+），modern browsers
会**交集** meta 和 header 的 CSP。配合 CSP3 规则「nonce 存在时忽略 'unsafe-inline'」→ 实际生效策略
是 nonce-only。

## 2. 文件改动

| 文件 | 改动 |
|------|------|
| `functions/_middleware.js` | 新增 `injectMetaCsp()`，在 `withCspHeaders()` 末尾向 HTML head 注入 meta 标签。`buildCsp()` 注释更新，移除 `script-src-attr` 关于 print-media onload trick 的过时说明（已 0 个 inline event handler） |
| `_headers` | 新增 `Reporting-Endpoints: csp-endpoint="https://weddingai.video/__csp_report"`，让 meta 的 `report-to` 指令有目的地。重写 `Content-Security-Policy` 上方的注释块说明新架构 |
| `internal-tools/pre-deploy-check.ps1` | 新增 `[1d/9] Inline event handlers` 回归 check（防以后有人加回 `<element on*=...>` 触发 CSP block） |

**预存 Sitemap 没变**，sitemap 不需要 nonce。

## 3. 部署验证

### 3.1 Pre-deploy check (10 项全过)

```
[PASS] HTML <title> tag integrity
[PASS] Hard-coded CSP nonces in HTML
[PASS] No <h1>/first-<h2> duplicates in 528 deployed pages
[PASS] No inline event handlers in 528 deployed pages  ← 新增 check
[PASS] All service page images resolve
[PASS] All srcset/picture tags use absolute paths and proper structure
[PASS] No empty CSS rules detected
[PASS] index.html / about / gallery / order / success / privacy / terms / styles.css / wrangler.toml / js/main.js 存在
[PASS] No dead Privacy/Terms links
[PASS] All pages use the lazy-load gtag pattern
[PASS] 614 HTML files present
[PASS] All page titles ≤ 60 chars and descriptions ≤ 160 chars
[PASS] Cloudflare Functions: 6 endpoint(s)
[PASS] order form posts to /api/quote
[PASS] No Netlify-specific form attributes
[PASS] No hardcoded API keys/tokens in functions/
[PASS] All <script src> are absolute
[PASS] Blog 301 retention check OK
Errors: 0
```

### 3.2 CDN 同步后实拉（prod）

每个请求 meta CSP nonce 都跟所有 `<script>` 标签 nonce 完美匹配：

| 路径 | meta CSP nonce | 第一个 script nonce | 匹配 |
|------|---------------|--------------------|----|
| `/` | `mvHl26ilqKGPVxZqNZq+...` | `mvHl26ilqKGPVxZqNZq+...` | ✅ |
| `/zh/` | `hvQ9lr2qvlXU34bQVoKm...` | `hvQ9lr2qvlXU34bQVoKm...` | ✅ |
| `/de/blog/wedding-video-music-guide-new/` | `H7fr289nW2PYhyn/L/Eu...` | `H7fr289nW2PYhyn/L/Eu...` | ✅ |
| `/ar/blog/wedding-video-inspiration/` | `cTHPYztEyUGWvCXUOTyJ...` | `cTHPYztEyUGWvCXUOTyJ...` | ✅ |

所有 9 个语言版本 + 关键子页面 (`/order/`, `/blog/`, `/about/`, `/pricing/`, `/success/`) HTTP 200。

### 3.3 Post-deploy smoke (Content-Type sanity)

```
[1/3] English home
  [PASS] HTTP 200
  [PASS] Content-Type: text/html; charset=utf-8
  [PASS] Body contains 'lang="en"' (56781 bytes)
[2/3] Chinese home (server-side i18n path)  (/zh/)
  [PASS] HTTP 200
  [PASS] Content-Type: text/html; charset=utf-8
  [PASS] Body contains 'lang="zh"' (56660 bytes)
[3/3] Order form (sub-page)  (/order/)
  [PASS] HTTP 200
  [PASS] Content-Type: text/html; charset=utf-8
  [PASS] Body contains '<title' (44103 bytes)

POST-DEPLOY SMOKE TEST PASSED
```

### 3.4 CSP report endpoint 仍工作

```
POST /__csp_report → 204 (expected 204)
```

---

## 4. 实际生效的 CSP 策略

**HTML 页面 (走 middleware)**:
- Meta CSP (per-request nonce) — **ACTIVE for HTML**
- Static `_headers` CSP (有 `'unsafe-inline'`) — 也到达客户端，但被交集后忽略

现代浏览器交集后 script-src 等价于：
```
script-src 'self' 'nonce-<per-request>' 'strict-dynamic' https://www.googletagmanager.com ...;
script-src-attr 'self' 'nonce-<per-request>';
```
nonce 存在时 `'unsafe-inline'` 被 CSP3 自动忽略 → **inline script 必须有正确 nonce 才能执行**。

**非 HTML 资源 (CSS/JS/images/sitemap.xml 等)**:
- 只有 static `_headers` CSP (有 `'unsafe-inline'`) — 因为这些路径 shouldSkip middleware
- 没有 inline 脚本所以 `'unsafe-inline'` 无害

---

## 5. 已知遗留 (out of scope, pre-existing)

**HTML 页面没有拿到 `_headers` 里其他头**：HSTS, X-Frame-Options, Permissions-Policy, Referrer-Policy 等
只在 `new Response(...)` rebuild 时被 middleware 覆盖丢失。CF Pages 只放行 `Content-Type`（必需），
其他 middleware-set 头都被丢。

证据：
- `/styles.min.css`（静态资源）→ 11 个 `_headers` 头全有
- `/sitemap.xml`（shouldSkip middleware）→ 11 个 `_headers` 头全有
- `/`, `/about/`, `/order/`（走 middleware rebuild）→ **只有 Content-Type**

**对审计影响**：
- 审计问的 CSP 已在 meta 层修好 ✅
- HSTS/X-Frame-Options/Permissions-Policy 在 HTML 上失效是 pre-existing gap，跟本次 audit 无关
- 要彻底修需要把 i18n 从 middleware 挪到客户端（成本太高），或换部署平台

**建议 follow-up**（不在本次修复里）：
1. 把 `Referrer-Policy` 加进 meta tag（meta delivery 是 spec 允许的）— 改 middleware 即可
2. 其他 header 短期无法在 HTML 上生效，需在 README/SECURITY 里加注

---

## 6. 总结

| 项 | 状态 |
|----|------|
| 审计问题 (`'unsafe-inline'` + nonce 失效) | ✅ 修复（meta CSP 注入） |
| 所有 `<script>` 都有 matching nonce | ✅ 15/15 on `/` |
| 9 语言 + 子页面 HTTP 200 | ✅ |
| CSP report endpoint 仍工作 | ✅ |
| Inline event handler 回归 check | ✅ pre-deploy 永久防回归 |
| Pre-deploy check | ✅ 0 errors |

`qa/_build_report.py` 没跑（脚本应该是为 i18n 报告写的，这里没必要）。

