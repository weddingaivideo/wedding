/* =============================================
   WeddingAI.video — Client-side i18n (v2)
   All non-English pages are served via /xx/ path prefix
   and translated server-side by the middleware. Client-side
   only handles language switcher + redirect for missing prefix.
   ============================================= */
(function () {
    "use strict";

    var SUPPORTED = (window.WA_LANGS && window.WA_LANGS.length)
        ? window.WA_LANGS
        : ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th"];
    var RTL = (window.WA_RTL && Object.keys(window.WA_RTL).length)
        ? window.WA_RTL
        : { ar: true };
    var STORAGE_KEY = "wa_lang";
    var FALLBACK = window.WA_DEFAULT_LANG || "en";
    var DEFAULT = FALLBACK;
    // Cache-bust version for middleware i18n JSON caching.
    var I18N_VERSION = "4.28";

    var LANG_RE = new RegExp("^/(" + SUPPORTED.join("|") + ")(/|$)");

    function getLang() {
        try {
            var m = window.location.pathname.match(LANG_RE);
            if (m) return m[1];
        } catch (e) { /* ignore */ }
        try {
            var p = new URLSearchParams(window.location.search);
            var q = p.get("lang");
            if (q && SUPPORTED.indexOf(q) !== -1) return q;
        } catch (e) { /* ignore */ }
        try {
            var saved = localStorage.getItem(STORAGE_KEY);
            if (saved && SUPPORTED.indexOf(saved) !== -1) return saved;
        } catch (e) { /* ignore */ }
        var htmlLang = (document.documentElement.lang || "").toLowerCase().split("-")[0];
        if (SUPPORTED.indexOf(htmlLang) !== -1) return htmlLang;
        return DEFAULT;
    }

    function setLang(lang) {
        try { localStorage.setItem(STORAGE_KEY, lang); } catch (e) { /* ignore */ }
        try { document.cookie = "wa_lang_user=" + lang + "; Path=/; Max-Age=2592000; SameSite=Lax"; } catch (e) { /* ignore */ }
        var url = new URL(window.location.href);
        var path = url.pathname;
        var stripped = path.replace(LANG_RE, "/");
        if (stripped === "") stripped = "/";
        var newPath = lang === DEFAULT ? stripped : "/" + lang + stripped;
        var newSearch = url.search.replace(/[?&]lang=[^&]*/g, '').replace(/^&/, '?');
        if (newSearch === '?') newSearch = '';
        window.location.href = newPath + newSearch + url.hash;
    }

    function setDir(lang) {
        var html = document.documentElement;
        html.lang = lang;
        html.dir = RTL[lang] ? "rtl" : "ltr";
        if (RTL[lang]) {
            html.classList.add("wa-rtl");
        } else {
            html.classList.remove("wa-rtl");
        }
    }

    function bindSwitcher() {
        var sel = document.getElementById("wa-lang-select");
        if (!sel) return;
        sel.addEventListener("change", function () {
            setLang(sel.value);
        });
    }

    // Main
    var lang = getLang();

    // If user explicitly chose a non-default language but the URL has no
    // language prefix, redirect to the language-prefixed URL. This ensures
    // server-side translation runs and all content is fully translated.
    if (lang !== DEFAULT) {
        var hasPathPrefix = LANG_RE.test(window.location.pathname);
        if (!hasPathPrefix) {
            try {
                var savedLang = localStorage.getItem(STORAGE_KEY);
                if (savedLang && savedLang === lang) {
                    var redirectPath = "/" + lang + window.location.pathname;
                    window.location.replace(redirectPath + window.location.search + window.location.hash);
                }
            } catch (e) { /* redirect failed */ }
        }
    }

    setDir(lang);
    document.addEventListener("DOMContentLoaded", function () {
        bindSwitcher();
        var sel = document.getElementById("wa-lang-select");
        if (sel) sel.value = lang;
    });
})();
