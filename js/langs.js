/**
 * WeddingAI.video — single source of truth for supported languages.
 *
 * This file is loaded by:
 *   - js/i18n.js (browser-side runtime, before its iife runs)
 *   - qa/gen_sitemap.py (parsed as text by Python script)
 *   - scripts/sync_langs_redirects.py (read for _redirects regeneration)
 *
 * A mirrored copy must also exist at:
 *   - functions/_lib/langs.js (CF Pages Functions cannot import
 *     files outside the functions/ directory, so a parallel copy
 *     is required. The two MUST stay byte-identical — the pre-deploy
 *     check runs scripts/check_langs_sync.py to enforce this.)
 *
 * To add/remove a language:
 *   1. Edit this file (js/langs.js)
 *   2. Mirror the change to functions/_lib/langs.js
 *   3. Run: python scripts/sync_langs_redirects.py   (regenerates _redirects)
 *   4. Run: pre-deploy-check.ps1                       (verifies sync)
 */
window.WA_LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"];
window.WA_DEFAULT_LANG = "en";
window.WA_RTL = { ar: true, hi: false };
window.WA_LANG_LABELS = {
    en: "English",
    zh: "中文",
    es: "Español",
    fr: "Français",
    de: "Deutsch",
    pt: "Português",
    ja: "日本語",
    ru: "Русский",
    ar: "العربية",
    th: "ไทย",
    hi: "हिन्दी",
};
window.WA_LANG_SHORT = {
    en: "EN",
    zh: "中文",
    es: "ES",
    fr: "FR",
    de: "DE",
    pt: "PT",
    ja: "JA",
    ru: "RU",
    ar: "AR",
    th: "TH",
    hi: "HI",
};
