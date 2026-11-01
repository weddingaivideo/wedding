#!/usr/bin/env python3
"""Write the cookie-consent strings for every language.

The cookie banner is built at runtime by js/cookie-consent.js, so the
middleware's server-side i18n pass cannot translate it: it only rewrites
data-i18n attributes inside the HTML. Until now the banner was hard-coded
English in the JS, which is why a Spanish visitor saw "🍪 We use cookies ...
privacy policy ... Essential only / Accept all" on every page.

The strings live in i18n/cookie/<lang>.json - tiny standalone files, NOT the
6-17 MB dictionaries, because the banner is the only thing that needs them
and the client fetches them once per visitor (on first visit only).

The body carries a {link} placeholder: the JS substitutes the anchor to the
privacy policy, because the href has to point at the LOCALIZED privacy page
(/es/privacy/, /zh/privacy/, ...), which only the middleware knows about.

Run from the repo root:  python scripts/build-cookie-i18n.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

OUT_DIR = os.path.join("i18n", "cookie")

BODY = ("We use essential cookies to run this site and optional analytics "
        "cookies to understand how it performs. See our {link} for details.")

STRINGS = {
    "en": {
        "heading": "🍪 We use cookies",
        "body": BODY,
        "link": "privacy policy",
        "essential": "Essential only",
        "accept": "Accept all",
        "label": "Cookie consent",
    },
    "de": {
        "heading": "🍪 Wir verwenden Cookies",
        "body": ("Wir verwenden notwendige Cookies, um diese Website zu betreiben, "
                 "und optionale Analyse-Cookies, um zu verstehen, wie sie funktioniert. "
                 "Details finden Sie in unserer {link}."),
        "link": "Datenschutzerklärung",
        "essential": "Nur notwendige",
        "accept": "Alle akzeptieren",
        "label": "Cookie-Einwilligung",
    },
    "es": {
        "heading": "🍪 Usamos cookies",
        "body": ("Usamos cookies necesarios para que este sitio funcione y cookies de "
                 "análisis opcionales para entender cómo se comporta. Consulta nuestra "
                 " {link} para más detalles."),
        "link": "política de privacidad",
        "essential": "Solo necesarios",
        "accept": "Aceptar todo",
        "label": "Consentimiento de cookies",
    },
    "fr": {
        "heading": "🍪 Nous utilisons des cookies",
        "body": ("Nous utilisons des cookies nécessaires au fonctionnement de ce site et "
                 "des cookies d'analyse facultatifs pour comprendre ses performances. "
                 "Consultez notre {link} pour plus de détails."),
        "link": "politique de confidentialité",
        "essential": "Essentiels uniquement",
        "accept": "Tout accepter",
        "label": "Consentement aux cookies",
    },
    "pt": {
        "heading": "🍪 Usamos cookies",
        "body": ("Usamos cookies essenciais para que este site funcione e cookies de "
                 "análise opcionais para entender como se comporta. Veja a nossa "
                 " {link} para mais detalhes."),
        "link": "política de privacidade",
        "essential": "Apenas essenciais",
        "accept": "Aceitar tudo",
        "label": "Consentimento de cookies",
    },
    "ja": {
        "heading": "🍪 Cookie を使用しています",
        "body": ("このサイトの運営には必須 Cookie を使用し、パフォーマンスの把握には任意の"
                 "分析 Cookie を使用します。詳細は{link}をご覧ください。"),
        "link": "Cookie ポリシー",
        "essential": "必須のみ",
        "accept": "すべて許可",
        "label": "Cookie の同意",
    },
    "ru": {
        "heading": "🍪 Мы используем cookies",
        "body": ("Мы используем обязательные cookie для работы сайта и дополнительные "
                 "аналитические cookie, чтобы понимать его эффективность. Подробнее — "
                 "в нашей {link}."),
        "link": "политике конфиденциальности",
        "essential": "Только обязательные",
        "accept": "Принять все",
        "label": "Согласие на использование cookies",
    },
    "ar": {
        "heading": "🍪 نستخدم ملفات تعريف الارتباط",
        "body": ("نستخدم ملفات تعريف الارتباط الضرورية لتشغيل هذا الموقع، وملفات "
                 "تحليلية اختيارية لفهم أدائه. راجع {link} لمزيد من التفاصيل."),
        "link": "سياسة الخصوصية",
        "essential": "الضرورية فقط",
        "accept": "قبول الكل",
        "label": "الموافقة على ملفات تعريف الارتباط",
    },
    "th": {
        "heading": "🍪 เราใช้คุกกี้",
        "body": ("เราใช้คุกกี้ที่จำเป็นเพื่อให้เว็บไซต์นี้ทำงานได้ และคุกกี้วิเคราะห์"
                 "แบบไม่บังคับเพื่อเข้าใจการทำงาน ดูรายละเอียดใน{link}ของเรา"),
        "link": "นโยบายความเป็นส่วนตัว",
        "essential": "เฉพาะที่จำเป็น",
        "accept": "ยอมรับทั้งหมด",
        "label": "การยินยอมคุกกี้",
    },
    "hi": {
        "heading": "🍪 हम कुकीज़ का उपयोग करते हैं",
        "body": ("इस साइट को चलाने के लिए हम आवश्यक कुकीज़ का उपयोग करते हैं, और यह "
                 "समझने के लिए कि साइट कैसा प्रदर्शन करता है, वैकल्पिक विश्लेषण कुकीज़ "
                 "का भी। अधिक जानकारी के लिए हमारी {link} देखें।"),
        "link": "गोपनीयता नीति",
        "essential": "केवल आवश्यक",
        "accept": "सभी स्वीकारें",
        "label": "कुकी सहमति",
    },
    "zh": {
        "heading": "🍪 我们使用 Cookie",
        "body": ("我们使用必要的 Cookie 来运行本网站，并使用可选的分析 Cookie 来了解其"
                 "表现。详情请参阅我们的{link}。"),
        "link": "隐私政策",
        "essential": "仅必要项",
        "accept": "全部接受",
        "label": "Cookie 同意",
    },
}

KEYS = ["heading", "body", "link", "essential", "accept", "label"]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for lang, strings in STRINGS.items():
        assert set(strings) == set(KEYS), f"{lang}: key set mismatch"
        assert "{link}" in strings["body"], f"{lang}: body has no {{link}} placeholder"
        path = os.path.join(OUT_DIR, f"{lang}.json")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(strings, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print(f"  wrote {path} ({os.path.getsize(path)} bytes)")


if __name__ == "__main__":
    main()
