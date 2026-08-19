/**
 * WeddingAI.video — single source of truth for supported languages.
 *
 * MIRROR of /js/langs.js. Cloudflare Pages Functions cannot import
 * files outside the /functions/ directory tree, so this duplicate
 * exists. The pre-deploy check runs scripts/check_langs_sync.py to
 * enforce that this file stays byte-identical to /js/langs.js.
 *
 * To add/remove a language, see /js/langs.js for the full procedure.
 */
export const LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"];
export const DEFAULT_LANG = "en";
export const RTL = { ar: true, hi: false };
export const LANG_LABELS = {
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
export const LANG_SHORT = {
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
