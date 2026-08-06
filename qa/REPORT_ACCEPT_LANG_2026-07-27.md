# Accept-Language 自动语言检测

**日期:** 2026-07-27
**部署:** `3f615e80.weddingai-video.pages.dev` (preview)
**目标:** 根据浏览器语言自动选择对应语言版本

---

## 🎯 行为

| 场景 | 行为 |
|------|------|
| 首次访问（无 cookie） | 解析 `Accept-Language`，302 重定向到 `/xx/path/`，设 cookie |
| 已有 `wa_lang_auto` cookie | 不重定向（避免每次刷新都跳） |
| 已有 `wa_lang_user` cookie（用户用 switcher 选过） | 不重定向 |
| URL 已有 `/xx/` 前缀 | 不重定向 |
| 静态资源（CSS/JS/img）| 跳过 |
| API 端点 | 跳过 |
| i18n JSON | 跳过 |
| 浏览器语言是英文 | 不重定向（默认语言） |

---

## 🔧 实现

### Server (functions/_middleware.js)

```js
// 检测逻辑
function detectBrowserLang(acceptLanguage) {
    if (!acceptLanguage) return null;
    // "zh-CN,zh;q=0.9,en;q=0.8" → 按 q 值排序 → 取第一个支持的 lang
    const items = acceptLanguage.split(",").map(s => {
        const [langTag, ...params] = s.trim().split(";");
        const qParam = params.find(p => p.trim().startsWith("q="));
        const q = qParam ? parseFloat(qParam.split("=")[1]) : 1.0;
        const lang = langTag.toLowerCase().split("-")[0];
        return { lang, q: isNaN(q) ? 1.0 : q };
    }).sort((a, b) => b.q - a.q);
    for (const { lang } of items) {
        if (LANGS.includes(lang)) return lang;
    }
    return null;
}

// 在 middleware 主流程
if (!cookies[AUTO_LANG_COOKIE] && !cookies[USER_LANG_COOKIE]) {
    const detected = detectBrowserLang(headers.get("Accept-Language"));
    if (detected && detected !== "en") {
        return new Response(null, {
            status: 302,
            headers: {
                "Location": new URL(`/${detected}${path}`, origin).toString(),
                "Set-Cookie": `wa_lang_auto=1; Path=/; Max-Age=2592000; SameSite=Lax`,
            },
        });
    }
}
```

### Client (js/i18n.js setLang)

lang switcher 切换语言时同时设 `wa_lang_user` cookie：
```js
document.cookie = "wa_lang_user=" + lang + "; Path=/; Max-Age=2592000; SameSite=Lax";
```

这样用户用 switcher 选过的语言会被记住，server 不会用 Accept-Language 覆盖。

---

## ✅ 测试结果（16/16 通过）

```
✓  /                        AL=zh-CN,zh;q=0.9      → 302  /zh/
✓  /                        AL=ja,en;q=0.5          → 302  /ja/
✓  /                        AL=en-US,en;q=0.9       → 200  (英文默认不重定向)
✓  /                        AL=es-ES,es;q=0.9       → 302  /es/
✓  /about/                  AL=zh-CN                → 302  /zh/about/
✓  /about/                  AL=de-DE                → 302  /de/about/
✓  /about/                  AL=ar                   → 302  /ar/about/
✓  /                        AL=zh  +wa_lang_auto    → 200  (cookie 阻止)
✓  /                        AL=ja  +wa_lang_user    → 200  (user cookie 阻止)
✓  /zh/                     AL=en                  → 200  (URL 已有前缀)
✓  /styles.min.css          AL=zh                  → 200  (静态资源跳过)
✓  /api/quote               AL=zh                  → 405  (API 跳过)
✓  /i18n/zh.json            AL=ja                  → 200  (JSON 跳过)
✓  /order/                  AL=fr                  → 302  /fr/order/
✓  /blog/                   AL=ru                  → 302  /ru/blog/
✓  /services/personalization/wedding-trailer/  AL=th  → 302  /th/...
```

完整流程验证：
```
GET /about/ + Accept-Language: ja
  ↓ 302
  Location: https://weddingai.video/ja/about/
  Set-Cookie: wa_lang_auto=1; ...
  ↓ browser follows
GET /ja/about/
  ↓ 200
  <html lang="ja">  (function injects)
  canonical: https://weddingai.video/ja/about/
  11 hreflangs
```

---

## 📊 改动

| 文件 | 改动 |
|------|------|
| `functions/_middleware.js` | + Accept-Language 检测 + cookie 检查 + 302 重定向 |
| `js/i18n.js` | setLang 加 `wa_lang_user` cookie 写入 |
| `qa/test_accept_lang.py` | 16 个测试用例 |

**没改 HTML 文件，没改 i18n JSON。**

---

## ⚠️ 注意点

1. **首次访问的 1 次重定向**：不可避免。后续靠 cookie
2. **Cookie 有效期 30 天**（`Max-Age=2592000`）：用户清 cookie 后会重新触发自动检测
3. **用户偏好优先**：switcher 选的 lang 写 `wa_lang_user` cookie，server 不覆盖
4. **Crawler 行为**：Googlebot 等通常发 `Accept-Language: en` 或不发，不会被误重定向
5. **SEO**：Google 会同时索引 `/about/` 和 `/zh/about/` 等。hreflang 信号告诉 Google 哪个 URL 对应哪种语言

---

## 🚀 完整 URL 流程

```
用户首次访问（中文浏览器）
  GET /about/  + Accept-Language: zh-CN
  ↓ server 302
  Location: /zh/about/
  Set-Cookie: wa_lang_auto=1
  ↓ browser
  GET /zh/about/  + Cookie: wa_lang_auto=1
  ↓ function 匹配 /zh/ 前缀
  fetch /about/  → 注入 <html lang="zh"> + canonical + hreflang
  返回中文 HTML（i18n.js 加载 /i18n/zh.json 应用翻译）
  ↓
  用户看到中文 /zh/about/ 页面

用户点 lang switcher → "English"
  setLang("en") 设 wa_lang_user=en cookie + 导航到 /about/
  ↓
  GET /about/  + Cookie: wa_lang_auto=1, wa_lang_user=en
  ↓ server 检查 cookies: 有 user cookie → 不重定向
  → 返回英文页面

用户清 cookie 再访问
  GET /about/  + Accept-Language: zh-CN  (无 cookie)
  ↓ server 302 到 /zh/about/，重新设 cookie
```
