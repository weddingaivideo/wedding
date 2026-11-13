#!/usr/bin/env python3
"""Add a fourth-option /planning-tools/ hub: a NEW entry page, zero URL moves.

Product decision (2026-11-13): primary KPI = maximise organic traffic.
Splitting the 14 planning tools out of /tools/<slug>/ would mean migrating
154 URLs x ~15 hard-coded URL literals each, 11 hreflang clusters and 11
sitemaps, with no GSC baseline to prove the gain. Instead we keep every tool
page exactly where it is and add a second, editorially distinct landing page
that links TO those existing URLs.

What this script produces (idempotent):
  planning-tools/index.html + <lang>/planning-tools/index.html   (11 pages)
  one <url> entry in each of the 11 sitemaps
  24 new planning.hub.* keys in each of the 11 dictionaries (append-only)
  a localised CTA on /tools/ and a backlink on the 14 tool pages (11 langs)
  "planning-tools" added to the middleware hub-link allowlist

The 14 tool cards bind to the EXISTING tools.card.* keys, whose 11-language
values are already shipped. Only the editorial wrapper is new copy. The
translation endpoints were rate-limited (HTTP 429) during this build, so the
new copy is hand-written per language rather than machine translated.

Run:  python scripts/add-planning-tools-hub.py
Then: python .tmp/rebuild-shards-inplace.py
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
ALL = ["en"] + LANGS
LOCALE = {"en": "en_US", "zh": "zh_CN", "es": "es_ES", "fr": "fr_FR",
          "de": "de_DE", "pt": "pt_BR", "ja": "ja_JP", "ru": "ru_RU",
          "ar": "ar_AE", "th": "th_TH", "hi": "hi_IN"}
BASE = "https://weddingai.video"
SLUG = "planning-tools"
NS = "planning.hub"
TEMPLATE = ROOT / "blog" / "wedding-dress-code-guide" / "index.html"
HUB = ROOT / "tools" / "index.html"
MIDDLEWARE = ROOT / "functions" / "_middleware.js"
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# --------------------------------------------------------------------------
# Editorial copy. Every language carries exactly the same key set.
# --------------------------------------------------------------------------
COPY = {
    "en": {
        "title_text": "Free Wedding Planning Tools by Timeline | No Signup",
        "meta_description": "14 free wedding planning tools in the order you need them: checklist, guest count, drinks, cake, timeline, vows and thank-you notes. No signup.",
        "h1": "Free Wedding Planning Tools, in the Order You'll Need Them",
        "lead": "Most tool lists are grouped by feature. Planning a wedding is grouped by date. Here are 14 free browser tools arranged from the first big decisions to the last thank-you note — nothing to install, nothing to sign up for.",
        "badge": "✓ 14 free tools · 11 languages · no signup",
        "how_h2": "How to use this planning toolkit",
        "step1": "Start with your date and guest count — the calculators scale everything else from those two numbers.",
        "step2": "Work one stage at a time. Each tool keeps its state in your browser, so you can close the tab and come back.",
        "step3": "Nothing is uploaded. Print or export each result before you move to the next stage.",
        "timeline_h2": "Every tool, in the order you'll need it",
        "stage1": "12+ months before — set the frame (3)",
        "stage2": "6–12 months — money and vendors (5)",
        "stage3": "The last month — words and the day (4)",
        "stage4": "After the wedding — notes and admin (2)",
        "faq_h2": "Wedding planning tools: common questions",
        "q1": "Are these planning tools really free?",
        "a1": "Yes. All 14 tools are free, run in your browser and need no account. Your entries stay on this device.",
        "q2": "Which tool should I start with?",
        "a2": "Start with the planning checklist and the guest count. Your date and headcount drive the drinks, cake, budget and seating decisions.",
        "q3": "Do these work for small or destination weddings?",
        "a3": "Yes. The calculators accept any guest count, and the timeline, checklist and wording tools work for elopements and destination weddings too.",
        "all_tools": "Browse all 32 free wedding tools →",
        "hub_cta": "Planning a wedding? See 14 free tools in date order →",
        "backlink": "See all 14 planning tools in date order",
    },
    "zh": {
        "title_text": "按时间线整理的免费婚礼策划工具｜无需注册",
        "meta_description": "14 个免费婚礼策划工具，按使用顺序排列：筹备清单、宾客人数、酒水、蛋糕、当日流程、誓词与感谢卡。全部在浏览器中运行，无需注册。",
        "h1": "免费婚礼策划工具，按你需要它们的顺序排列",
        "lead": "大多数工具清单按功能分类，而筹备婚礼是按日期推进的。这里把 14 个免费浏览器工具从最早的大决定排到最后一张感谢卡——无需安装，也无需注册。",
        "badge": "✓ 14 个免费工具 · 11 种语言 · 无需注册",
        "how_h2": "如何使用这套筹备工具",
        "step1": "先定日期和宾客人数——其余计算都由这两个数字推导。",
        "step2": "一次推进一个阶段。每个工具的状态保存在浏览器中，关掉页面也能回来继续。",
        "step3": "不会上传任何内容。进入下一阶段前，把当前结果打印或导出即可。",
        "timeline_h2": "按筹备顺序查看全部工具",
        "stage1": "婚前 12 个月以上 — 定下框架 (3)",
        "stage2": "婚前 6–12 个月 — 预算与供应商 (5)",
        "stage3": "最后一个月 — 文案与当天 (4)",
        "stage4": "婚礼之后 — 感谢与手续 (2)",
        "faq_h2": "婚礼筹备工具常见问题",
        "q1": "这些筹备工具真的免费吗？",
        "a1": "是的。14 个工具全部免费，在浏览器中运行，无需账号。你填写的内容只保存在本机。",
        "q2": "应该从哪个工具开始？",
        "a2": "先从筹备清单和宾客人数开始。日期和人数决定酒水、蛋糕、预算和座位安排。",
        "q3": "小型婚礼或目的地婚礼也适用吗？",
        "a3": "适用。计算器接受任意宾客人数，流程表、清单和文案工具同样适合私奔婚礼与目的地婚礼。",
        "all_tools": "浏览全部 32 个免费婚礼工具 →",
        "hub_cta": "正在筹备婚礼？按日期查看 14 个免费工具 →",
        "backlink": "按日期查看全部 14 个筹备工具",
    },
    "es": {
        "title_text": "Herramientas gratuitas para planificar tu boda por etapas",
        "meta_description": "14 herramientas gratis de planificación de boda en orden de uso: checklist, invitados, bebidas, tarta, cronograma, votos y gracias. Sin registro.",
        "h1": "Herramientas gratuitas para planificar tu boda, en el orden en que las necesitas",
        "lead": "La mayoría de los listados agrupan las herramientas por función. Planificar una boda se organiza por fechas. Aquí tienes 14 herramientas gratuitas, desde las primeras decisiones hasta la última nota de agradecimiento, sin instalar nada ni registrarte.",
        "badge": "✓ 14 herramientas gratis · 11 idiomas · sin registro",
        "how_h2": "Cómo usar este kit de planificación",
        "step1": "Empieza por la fecha y el número de invitados: las calculadoras derivan todo lo demás de esos dos datos.",
        "step2": "Avanza una etapa cada vez. Cada herramienta guarda su estado en tu navegador, así que puedes cerrar la pestaña y volver.",
        "step3": "No se sube nada. Imprime o exporta cada resultado antes de pasar a la siguiente etapa.",
        "timeline_h2": "Todas las herramientas, en orden de uso",
        "stage1": "Más de 12 meses antes — definir las bases (3)",
        "stage2": "De 6 a 12 meses antes — dinero y proveedores (5)",
        "stage3": "El último mes — palabras y el gran día (4)",
        "stage4": "Después de la boda — notas y trámites (2)",
        "faq_h2": "Preguntas frecuentes sobre las herramientas de planificación",
        "q1": "¿Son realmente gratuitas estas herramientas?",
        "a1": "Sí. Las 14 herramientas son gratuitas, funcionan en tu navegador y no requieren cuenta. Tus datos permanecen en este dispositivo.",
        "q2": "¿Por qué herramienta debería empezar?",
        "a2": "Empieza por la lista de tareas y el cálculo de invitados. La fecha y el número de asistentes determinan las bebidas, la tarta, el presupuesto y los asientos.",
        "q3": "¿Sirven para bodas pequeñas o de destino?",
        "a3": "Sí. Las calculadoras aceptan cualquier número de invitados, y el cronograma, la lista y las herramientas de texto también funcionan para elopements y bodas de destino.",
        "all_tools": "Ver las 32 herramientas gratuitas para bodas →",
        "hub_cta": "¿Planeas tu boda? Ver 14 herramientas gratis por fecha →",
        "backlink": "Ver las 14 herramientas de planificación por fecha",
    },
    "fr": {
        "title_text": "Outils gratuits de préparation de mariage, étape par étape",
        "meta_description": "14 outils gratuits de préparation de mariage dans l'ordre : tâches, invités, boissons, gâteau, planning, vœux et remerciements. Sans inscription.",
        "h1": "Outils gratuits pour organiser votre mariage, dans l'ordre où vous en aurez besoin",
        "lead": "La plupart des listes classent les outils par fonction. Organiser un mariage, c'est avancer par dates. Voici 14 outils gratuits, des premières grandes décisions au dernier mot de remerciement, sans rien installer ni créer de compte.",
        "badge": "✓ 14 outils gratuits · 11 langues · sans inscription",
        "how_h2": "Comment utiliser ce kit de préparation",
        "step1": "Commencez par la date et le nombre d'invités : les calculateurs en déduisent tout le reste.",
        "step2": "Avancez étape par étape. Chaque outil conserve son état dans votre navigateur, vous pouvez fermer l'onglet et revenir.",
        "step3": "Rien n'est téléversé. Imprimez ou exportez chaque résultat avant de passer à l'étape suivante.",
        "timeline_h2": "Tous les outils, dans l'ordre",
        "stage1": "Plus de 12 mois avant — poser le cadre (3)",
        "stage2": "De 6 à 12 mois avant — budget et prestataires (5)",
        "stage3": "Le dernier mois — les mots et le jour J (4)",
        "stage4": "Après le mariage — remerciements et démarches (2)",
        "faq_h2": "Questions fréquentes sur les outils de préparation",
        "q1": "Ces outils sont-ils vraiment gratuits ?",
        "a1": "Oui. Les 14 outils sont gratuits, fonctionnent dans votre navigateur et ne demandent aucun compte. Vos saisies restent sur cet appareil.",
        "q2": "Par quel outil commencer ?",
        "a2": "Commencez par la liste de tâches et le nombre d'invités. La date et l'effectif déterminent les boissons, le gâteau, le budget et le plan de table.",
        "q3": "Conviennent-ils aux petits mariages et aux mariages à l'étranger ?",
        "a3": "Oui. Les calculateurs acceptent n'importe quel nombre d'invités, et le planning, la liste et les outils de rédaction conviennent aussi aux elopements et mariages à destination.",
        "all_tools": "Voir les 32 outils gratuits pour le mariage →",
        "hub_cta": "Vous préparez un mariage ? Voir 14 outils gratuits par date →",
        "backlink": "Voir les 14 outils de préparation par date",
    },
    "de": {
        "title_text": "Kostenlose Hochzeitsplaner nach Zeitplan | Ohne Anmeldung",
        "meta_description": "14 kostenlose Hochzeitsplanungs-Tools in der richtigen Reihenfolge: Checkliste, Gäste, Getränke, Torte, Zeitplan, Gelübde, Danksagungen. Ohne Anmeldung.",
        "h1": "Kostenlose Hochzeitsplanungs-Tools in der Reihenfolge, in der du sie brauchst",
        "lead": "Die meisten Tool-Listen sortieren nach Funktion. Eine Hochzeit plant man aber nach Datum. Hier sind 14 kostenlose Browser-Tools von den ersten großen Entscheidungen bis zur letzten Danksagung – ohne Installation und ohne Registrierung.",
        "badge": "✓ 14 kostenlose Tools · 11 Sprachen · ohne Anmeldung",
        "how_h2": "So nutzt du dieses Planungs-Kit",
        "step1": "Beginne mit Datum und Gästezahl – alle Rechner leiten den Rest aus diesen beiden Werten ab.",
        "step2": "Arbeite eine Phase nach der anderen. Jedes Tool speichert seinen Stand im Browser, du kannst den Tab schließen und später weitermachen.",
        "step3": "Es wird nichts hochgeladen. Drucke oder exportiere jedes Ergebnis, bevor du zur nächsten Phase gehst.",
        "timeline_h2": "Alle Tools in der Reihenfolge ihrer Verwendung",
        "stage1": "Mehr als 12 Monate vorher — den Rahmen setzen (3)",
        "stage2": "6–12 Monate vorher — Geld und Dienstleister (5)",
        "stage3": "Der letzte Monat — Worte und der große Tag (4)",
        "stage4": "Nach der Hochzeit — Dank und Formalitäten (2)",
        "faq_h2": "Häufige Fragen zu den Planungs-Tools",
        "q1": "Sind diese Planungs-Tools wirklich kostenlos?",
        "a1": "Ja. Alle 14 Tools sind kostenlos, laufen im Browser und brauchen kein Konto. Deine Eingaben bleiben auf diesem Gerät.",
        "q2": "Mit welchem Tool sollte ich beginnen?",
        "a2": "Beginne mit der Checkliste und der Gästezahl. Datum und Personenzahl bestimmen Getränke, Torte, Budget und Sitzplan.",
        "q3": "Funktionieren sie auch für kleine Hochzeiten oder Hochzeiten im Ausland?",
        "a3": "Ja. Die Rechner akzeptieren jede Gästezahl, und Zeitplan, Checkliste und Text-Tools eignen sich auch für Elopements und Destination Weddings.",
        "all_tools": "Alle 32 kostenlosen Hochzeits-Tools ansehen →",
        "hub_cta": "Du planst eine Hochzeit? 14 kostenlose Tools nach Datum →",
        "backlink": "Alle 14 Planungs-Tools nach Datum ansehen",
    },
    "pt": {
        "title_text": "Ferramentas grátis de planejamento de casamento por etapa",
        "meta_description": "14 ferramentas grátis para planejar o casamento na ordem de uso: checklist, convidados, bebidas, bolo, cronograma, votos e agradecimentos. Sem cadastro.",
        "h1": "Ferramentas gratuitas de planejamento de casamento, na ordem em que você vai precisar",
        "lead": "A maioria das listas agrupa ferramentas por função. Planejar um casamento segue o calendário. Aqui estão 14 ferramentas gratuitas, das primeiras grandes decisões até o último bilhete de agradecimento, sem instalar nada e sem criar conta.",
        "badge": "✓ 14 ferramentas grátis · 11 idiomas · sem cadastro",
        "how_h2": "Como usar este kit de planejamento",
        "step1": "Comece pela data e pelo número de convidados — as calculadoras derivam todo o resto desses dois números.",
        "step2": "Avance uma etapa por vez. Cada ferramenta guarda seu estado no navegador, então você pode fechar a aba e voltar.",
        "step3": "Nada é enviado. Imprima ou exporte cada resultado antes de passar para a próxima etapa.",
        "timeline_h2": "Todas as ferramentas, na ordem de uso",
        "stage1": "Mais de 12 meses antes — definir a base (3)",
        "stage2": "De 6 a 12 meses antes — dinheiro e fornecedores (5)",
        "stage3": "O último mês — palavras e o grande dia (4)",
        "stage4": "Depois do casamento — notas e burocracia (2)",
        "faq_h2": "Perguntas frequentes sobre as ferramentas de planejamento",
        "q1": "Essas ferramentas são realmente gratuitas?",
        "a1": "Sim. As 14 ferramentas são gratuitas, funcionam no navegador e não exigem conta. Seus dados ficam neste dispositivo.",
        "q2": "Por qual ferramenta devo começar?",
        "a2": "Comece pelo checklist e pelo número de convidados. A data e a quantidade de pessoas determinam bebidas, bolo, orçamento e disposição das mesas.",
        "q3": "Funcionam para casamentos pequenos ou de destino?",
        "a3": "Sim. As calculadoras aceitam qualquer número de convidados, e o cronograma, o checklist e as ferramentas de texto também servem para elopements e casamentos de destino.",
        "all_tools": "Ver todas as 32 ferramentas gratuitas de casamento →",
        "hub_cta": "Planejando um casamento? Veja 14 ferramentas grátis por data →",
        "backlink": "Ver as 14 ferramentas de planejamento por data",
    },
    "ja": {
        "title_text": "結婚式の準備を時系列で進められる無料ツール｜登録不要",
        "meta_description": "必要な順に並べた14の無料ウェディング準備ツール：やることリスト、招待人数、ドリンク、ケーキ、当日のタイムライン、誓いの言葉、お礼状。ブラウザだけで完結、登録不要。",
        "h1": "無料の結婚式準備ツールを、必要になる順番に",
        "lead": "多くのツール一覧は機能別に分類されていますが、結婚式の準備は日付に沿って進みます。ここでは最初の大きな決定から最後のお礼状まで、14の無料ツールを時系列に並べました。インストールも登録も不要です。",
        "badge": "✓ 14の無料ツール · 11言語 · 登録不要",
        "how_h2": "この準備キットの使い方",
        "step1": "まず日付と招待人数を決めます。他の計算はすべてこの2つの数字から導き出されます。",
        "step2": "一度にひとつの段階を進めましょう。各ツールの状態はブラウザに保存されるので、タブを閉じて戻ってきても大丈夫です。",
        "step3": "データはアップロードされません。次の段階に進む前に、結果を印刷または書き出してください。",
        "timeline_h2": "すべてのツールを使う順番に",
        "stage1": "12か月以上前 — 全体の枠組みを決める (3)",
        "stage2": "6〜12か月前 — 予算と業者 (5)",
        "stage3": "最後の1か月 — 言葉と当日 (4)",
        "stage4": "結婚式の後 — お礼と手続き (2)",
        "faq_h2": "結婚式準備ツールに関するよくある質問",
        "q1": "これらの準備ツールは本当に無料ですか？",
        "a1": "はい。14のツールはすべて無料で、ブラウザ内で動作し、アカウントは不要です。入力内容はこの端末にだけ保存されます。",
        "q2": "どのツールから始めればよいですか？",
        "a2": "やることリストと招待人数の計算から始めましょう。日付と人数がドリンク、ケーキ、予算、席次を左右します。",
        "q3": "少人数婚礼やリゾートウェディングにも使えますか？",
        "a3": "はい。計算ツールはどんな人数にも対応し、タイムライン・リスト・文章作成ツールは二人だけの結婚式やリゾートウェディングでも使えます。",
        "all_tools": "無料の婚礼ツール32種をすべて見る →",
        "hub_cta": "結婚式を準備中ですか？日付順の無料ツール14種 →",
        "backlink": "準備ツール14種を日付順に見る",
    },
    "ru": {
        "title_text": "Бесплатные инструменты для планирования свадьбы по этапам",
        "meta_description": "14 бесплатных инструментов для планирования свадьбы по порядку: чек-лист, гости, напитки, торт, расписание, клятвы, благодарности. Без регистрации.",
        "h1": "Бесплатные инструменты для планирования свадьбы в порядке их использования",
        "lead": "Большинство списков группируют инструменты по функциям. Подготовка свадьбы идёт по датам. Здесь 14 бесплатных инструментов — от первых крупных решений до последней открытки с благодарностью. Ничего не нужно устанавливать или регистрировать.",
        "badge": "✓ 14 бесплатных инструментов · 11 языков · без регистрации",
        "how_h2": "Как пользоваться этим набором",
        "step1": "Начните с даты и числа гостей — остальные расчёты строятся на этих двух числах.",
        "step2": "Проходите по одному этапу. Каждый инструмент сохраняет состояние в браузере, поэтому можно закрыть вкладку и вернуться.",
        "step3": "Ничего не загружается на сервер. Распечатайте или экспортируйте результат перед следующим этапом.",
        "timeline_h2": "Все инструменты в порядке использования",
        "stage1": "Более чем за 12 месяцев — основа (3)",
        "stage2": "За 6–12 месяцев — деньги и подрядчики (5)",
        "stage3": "Последний месяц — слова и день свадьбы (4)",
        "stage4": "После свадьбы — благодарности и документы (2)",
        "faq_h2": "Частые вопросы об инструментах планирования",
        "q1": "Эти инструменты действительно бесплатны?",
        "a1": "Да. Все 14 инструментов бесплатны, работают в браузере и не требуют аккаунта. Ваши данные остаются на этом устройстве.",
        "q2": "С какого инструмента начать?",
        "a2": "Начните с чек-листа и расчёта числа гостей. Дата и количество гостей определяют напитки, торт, бюджет и рассадку.",
        "q3": "Подойдут ли они для небольшой или выездной свадьбы?",
        "a3": "Да. Калькуляторы принимают любое число гостей, а расписание, чек-лист и текстовые инструменты подходят и для камерных, и для выездных свадеб.",
        "all_tools": "Все 32 бесплатных свадебных инструмента →",
        "hub_cta": "Планируете свадьбу? 14 бесплатных инструментов по датам →",
        "backlink": "Все 14 инструментов планирования по датам",
    },
    "ar": {
        "title_text": "أدوات مجانية لتخطيط حفلات الزفاف حسب المرحلة",
        "meta_description": "14 أداة مجانية لتخطيط الزفاف حسب الترتيب: قائمة المهام، عدد الضيوف، المشروبات، الكعكة، جدول اليوم، الوعود وبطاقات الشكر. دون تسجيل.",
        "h1": "أدوات مجانية لتخطيط حفل الزفاف، بالترتيب الذي ستحتاجها فيه",
        "lead": "تُصنّف معظم قوائم الأدوات حسب الوظيفة، لكن التخطيط لحفل زفاف يسير حسب التاريخ. إليك 14 أداة مجانية تعمل في المتصفح، من القرارات الأولى الكبرى حتى آخر بطاقة شكر، دون تثبيت أو تسجيل.",
        "badge": "✓ 14 أداة مجانية · 11 لغة · دون تسجيل",
        "how_h2": "كيف تستخدم هذه المجموعة",
        "step1": "ابدأ بالتاريخ وعدد الضيوف، فبقية الحسابات تُشتق من هذين الرقمين.",
        "step2": "اعمل على مرحلة واحدة في كل مرة. تحفظ كل أداة حالتها في متصفحك، لذا يمكنك إغلاق الصفحة والعودة لاحقاً.",
        "step3": "لا يُرفع أي شيء إلى الخادم. اطبع كل نتيجة أو صدّرها قبل الانتقال إلى المرحلة التالية.",
        "timeline_h2": "كل الأدوات بترتيب استخدامها",
        "stage1": "قبل أكثر من 12 شهراً — وضع الإطار (3)",
        "stage2": "قبل 6 إلى 12 شهراً — الميزانية والموردون (5)",
        "stage3": "الشهر الأخير — الكلمات ويوم الحفل (4)",
        "stage4": "بعد الزفاف — الشكر والمعاملات (2)",
        "faq_h2": "أسئلة شائعة حول أدوات التخطيط",
        "q1": "هل أدوات التخطيط هذه مجانية حقاً؟",
        "a1": "نعم. الأدوات الـ14 مجانية بالكامل، وتعمل في متصفحك دون الحاجة إلى حساب. تبقى بياناتك على هذا الجهاز فقط.",
        "q2": "بأي أداة أبدأ؟",
        "a2": "ابدأ بقائمة المهام وحساب عدد الضيوف. فالتاريخ وعدد الحضور يحددان المشروبات والكعكة والميزانية وتوزيع المقاعد.",
        "q3": "هل تناسب حفلات الزفاف الصغيرة أو المقامة في الخارج؟",
        "a3": "نعم. تقبل الحاسبات أي عدد من الضيوف، كما يعمل جدول اليوم وقائمة المهام وأدوات الكتابة مع الزفافات المصغّرة وحفلات الزفاف في الوجهات السياحية.",
        "all_tools": "تصفح جميع أدوات الزفاف الـ32 المجانية →",
        "hub_cta": "تخطط لحفل زفاف؟ 14 أداة مجانية مرتبة بالتاريخ →",
        "backlink": "عرض أدوات التخطيط الـ14 مرتبة بالتاريخ",
    },
    "th": {
        "title_text": "เครื่องมือวางแผนงานแต่งงานฟรีตามลำดับเวลา | ไม่ต้องสมัคร",
        "meta_description": "เครื่องมือวางแผนงานแต่งงานฟรี 14 อย่างตามลำดับใช้งาน: เช็กลิสต์ แขก เครื่องดื่ม เค้ก ตารางวันงาน คำปฏิญาณ บัตรขอบคุณ ไม่ต้องสมัคร",
        "h1": "เครื่องมือวางแผนงานแต่งงานฟรี เรียงตามลำดับที่คุณจะต้องใช้",
        "lead": "รายการเครื่องมือส่วนใหญ่จัดกลุ่มตามฟังก์ชัน แต่งานแต่งจะเดินตามวันและเวลา ที่นี่เราเรียงเครื่องมือฟรี 14 อย่างตั้งแต่การตัดสินใจใหญ่ครั้งแรกไปจนถึงบัตรขอบคุณใบสุดท้าย ไม่ต้องติดตั้ง ไม่ต้องสมัครสมาชิก",
        "badge": "✓ เครื่องมือฟรี 14 อย่าง · 11 ภาษา · ไม่ต้องสมัคร",
        "how_h2": "วิธีใช้ชุดเครื่องมือนี้",
        "step1": "เริ่มจากวันงานและจำนวนแขก เครื่องคำนวณอื่น ๆ ทั้งหมดอิงจากตัวเลขสองค่านี้",
        "step2": "ทำทีละขั้นตอน แต่ละเครื่องมือบันทึกสถานะไว้ในเบราว์เซอร์ จึงปิดแท็บแล้วกลับมาต่อได้",
        "step3": "ไม่มีการอัปโหลดข้อมูล พิมพ์หรือส่งออกผลลัพธ์ก่อนไปขั้นตอนถัดไป",
        "timeline_h2": "เครื่องมือทั้งหมดเรียงตามลำดับการใช้งาน",
        "stage1": "มากกว่า 12 เดือนก่อนงาน — วางกรอบ (3)",
        "stage2": "6–12 เดือนก่อนงาน — งบและผู้ให้บริการ (5)",
        "stage3": "เดือนสุดท้าย — ถ้อยคำและวันงาน (4)",
        "stage4": "หลังงานแต่ง — บัตรขอบคุณและเอกสาร (2)",
        "faq_h2": "คำถามที่พบบ่อยเกี่ยวกับเครื่องมือวางแผน",
        "q1": "เครื่องมือวางแผนเหล่านี้ฟรีจริงหรือไม่?",
        "a1": "ฟรีจริง เครื่องมือทั้ง 14 อย่างทำงานในเบราว์เซอร์ ไม่ต้องสร้างบัญชี และข้อมูลที่กรอกจะอยู่ในอุปกรณ์นี้เท่านั้น",
        "q2": "ควรเริ่มจากเครื่องมือไหน?",
        "a2": "เริ่มจากเช็กลิสต์และการคำนวณจำนวนแขก วันงานและจำนวนคนเป็นตัวกำหนดเครื่องดื่ม เค้ก งบประมาณ และผังที่นั่ง",
        "q3": "ใช้กับงานแต่งเล็ก ๆ หรือจัดต่างประเทศได้ไหม?",
        "a3": "ได้ เครื่องคำนวณรองรับจำนวนแขกเท่าใดก็ได้ และตารางวันงาน เช็กลิสต์ และเครื่องมือเขียนข้อความก็ใช้ได้กับงานแต่งแบบส่วนตัวและงานจัดต่างประเทศ",
        "all_tools": "ดูเครื่องมือแต่งงานฟรีทั้ง 32 อย่าง →",
        "hub_cta": "กำลังวางแผนงานแต่ง? ดูเครื่องมือฟรี 14 อย่างตามลำดับวัน →",
        "backlink": "ดูเครื่องมือวางแผนทั้ง 14 อย่างตามลำดับวัน",
    },
    "hi": {
        "title_text": "टाइमलाइन के अनुसार मुफ़्त शादी की योजना उपकरण | बिना साइनअप",
        "meta_description": "शादी की योजना के 14 मुफ़्त उपकरण, उपयोग के क्रम में: चेकलिस्ट, मेहमान, पेय, केक, शेड्यूल, वचन और धन्यवाद कार्ड। ब्राउज़र में, बिना खाता बनाए।",
        "h1": "शादी की योजना के मुफ़्त उपकरण, उसी क्रम में जिसमें आपको इनकी ज़रूरत होगी",
        "lead": "ज़्यादातर सूचियाँ उपकरणों को सुविधा के अनुसार बाँटती हैं, लेकिन शादी की तैयारी तारीख़ के अनुसार आगे बढ़ती है। यहाँ 14 मुफ़्त ब्राउज़र उपकरण पहले बड़े फ़ैसले से लेकर आख़िरी धन्यवाद कार्ड तक क्रम में रखे हैं — कुछ इंस्टॉल या साइनअप नहीं करना।",
        "badge": "✓ 14 मुफ़्त उपकरण · 11 भाषाएँ · बिना साइनअप",
        "how_h2": "इस प्लानिंग किट का उपयोग कैसे करें",
        "step1": "तारीख़ और मेहमानों की संख्या से शुरू करें — बाक़ी सभी गणनाएँ इन्हीं दो आँकड़ों से निकलती हैं।",
        "step2": "एक समय में एक चरण पूरा करें। हर उपकरण अपनी स्थिति ब्राउज़र में सहेजता है, इसलिए टैब बंद कर के वापस आ सकते हैं।",
        "step3": "कुछ भी अपलोड नहीं होता। अगले चरण पर जाने से पहले हर परिणाम प्रिंट या निर्यात कर लें।",
        "timeline_h2": "सभी उपकरण, उपयोग के क्रम में",
        "stage1": "शादी से 12+ महीने पहले — आधार तय करें (3)",
        "stage2": "6–12 महीने पहले — बजट और विक्रेता (5)",
        "stage3": "आख़िरी महीना — शब्द और विवाह का दिन (4)",
        "stage4": "शादी के बाद — धन्यवाद और कागज़ी काम (2)",
        "faq_h2": "प्लानिंग उपकरणों से जुड़े सामान्य प्रश्न",
        "q1": "क्या ये प्लानिंग उपकरण सच में मुफ़्त हैं?",
        "a1": "हाँ। सभी 14 उपकरण मुफ़्त हैं, ब्राउज़र में चलते हैं और खाते की ज़रूरत नहीं है। आपकी जानकारी इसी डिवाइस में रहती है।",
        "q2": "मुझे किस उपकरण से शुरू करना चाहिए?",
        "a2": "चेकलिस्ट और मेहमानों की संख्या से शुरू करें। तारीख़ और मेहमानों की संख्या से पेय, केक, बजट और बैठने की व्यवस्था तय होती है।",
        "q3": "क्या ये छोटी या डेस्टिनेशन शादी के लिए काम करते हैं?",
        "a3": "हाँ। कैलकुलेटर किसी भी संख्या में मेहमान स्वीकार करते हैं, और शेड्यूल, चेकलिस्ट तथा लेखन उपकरण छोटी और डेस्टिनेशन शादियों के लिए भी उपयुक्त हैं।",
        "all_tools": "सभी 32 मुफ़्त शादी उपकरण देखें →",
        "hub_cta": "शादी की तैयारी कर रहे हैं? तारीख़ के क्रम में 14 मुफ़्त उपकरण →",
        "backlink": "सभी 14 प्लानिंग उपकरण तारीख़ के क्रम में देखें",
    },
}

# Timeline groups. These 14 slugs are the research report's planning batch.
STAGES = [
    ("stage1", ["wedding-checklist-generator", "wedding-guest-count-calculator",
                "wedding-countdown-widget"]),
    ("stage2", ["wedding-vendor-questions-checklist", "wedding-alcohol-calculator",
                "wedding-cake-serving-calculator", "wedding-gift-calculator",
                "wedding-vendor-tipping-calculator"]),
    ("stage3", ["wedding-vow-writer", "wedding-speech-writer",
                "wedding-day-timeline-generator", "wedding-dress-code-decoder"]),
    ("stage4", ["wedding-thank-you-note-generator", "name-change-checklist"]),
]
ALL_SLUGS = [s for _, slugs in STAGES for s in slugs]

FAQS = [("q1", "a1"), ("q2", "a2"), ("q3", "a3")]


def esc(t: str) -> str:
    return html.escape(t, quote=True)


def k(name: str) -> str:
    return NS + "." + name


def bound(name: str, lang: str, tag: str = "span", cls: str = "") -> str:
    c = ' class="%s"' % cls if cls else ""
    return "<%s%s data-i18n=\"%s\">%s</%s>" % (
        tag, c, k(name), esc(COPY[lang][name]), tag)


def fit(text: str, limit: int, label: str) -> str:
    """Fail loudly instead of silently truncating a hand-written translation."""
    if len(text) > limit:
        raise SystemExit("[FAIL] %s is %d chars (limit %d): %s" %
                         (label, len(text), limit, text))
    return text


def url(lang: str, path: str = "") -> str:
    prefix = "" if lang == "en" else "/" + lang
    return BASE + prefix + path


# --------------------------------------------------------------------------
# Cards are lifted verbatim from /tools/: same keys, same 11-language values.
# --------------------------------------------------------------------------
def extract_cards() -> dict[str, dict]:
    src = HUB.read_text(encoding="utf-8")
    out = {}
    for href, body in re.findall(
            r'<a class="tool-card" href="([^"]+)">([\s\S]*?)</a>', src):
        slug = href.strip("/").split("/")[-1]
        if slug not in ALL_SLUGS:
            continue
        fields = {}
        for m in re.finditer(r'data-i18n="(tools\.card\.[^"]+)"[^>]*>([^<]*)<', body):
            key, text = m.group(1), m.group(2)
            if ".badge." in key:
                fields["badge"] = (key, text)
            elif ".name." in key:
                fields["name"] = (key, text)
            elif ".tag." in key:
                fields["tag"] = (key, text)
            elif ".cta." in key:
                fields["cta"] = (key, text)
        if len(fields) != 4:
            raise SystemExit("[FAIL] card %s has fields %s" % (slug, sorted(fields)))
        out[slug] = {"href": href, **fields}
    missing = set(ALL_SLUGS) - set(out)
    if missing:
        raise SystemExit("[FAIL] cards missing from /tools/: %s" % sorted(missing))
    return out


def card_html(card: dict, lang: str) -> str:
    prefix = "" if lang == "en" else "/" + lang
    href = prefix + card["href"]
    badge, badge_t = card["badge"]
    name, name_t = card["name"]
    tag, tag_t = card["tag"]
    cta, cta_t = card["cta"]
    return (
        '      <a class="pt-card" href="%s">\n'
        '        <span class="pt-badge" data-i18n="%s">%s</span>\n'
        '        <h3 class="pt-name" data-i18n="%s">%s</h3>\n'
        '        <p class="pt-tag" data-i18n="%s">%s</p>\n'
        '        <span class="pt-cta" data-i18n="%s">%s</span>\n'
        '      </a>' % (href, badge, esc(badge_t), name, esc(name_t),
                        tag, esc(tag_t), cta, esc(cta_t)))


CSS = """
.pt-wrap{max-width:1140px;margin:0 auto;padding:0 var(--spacing-md) var(--spacing-xl)}
.pt-hero{text-align:center;padding:var(--spacing-xl) 0 var(--spacing-md)}
.pt-hero h1{font-size:clamp(1.8rem,4vw,2.8rem);line-height:1.2;color:var(--color-text);margin:0 0 .85rem}
.pt-lead{max-width:780px;margin:0 auto;color:var(--color-text-light);line-height:1.75;font-size:1.02rem}
.pt-badges{display:flex;flex-wrap:wrap;gap:.5rem;justify-content:center;margin-top:1.1rem}
.pt-hero-badge{background:var(--color-surface-warm-2);border:1px solid var(--color-border);border-radius:999px;padding:.4rem .95rem;font-size:.8rem;font-weight:600;color:var(--color-text)}
.pt-section{margin-top:var(--spacing-xl)}
.pt-section>h2{font-size:1.6rem;color:var(--color-text);margin:0 0 .9rem}
.pt-steps{counter-reset:pt;list-style:none;padding:0;margin:0;display:grid;gap:.7rem}
.pt-steps li{counter-increment:pt;position:relative;padding:.85rem 1rem .85rem 3.2rem;background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-md);color:var(--color-text);line-height:1.6}
.pt-steps li::before{content:counter(pt);position:absolute;left:1rem;top:.85rem;width:1.5rem;height:1.5rem;border-radius:50%;background:var(--color-primary);color:#fff;font-weight:700;font-size:.8rem;display:flex;align-items:center;justify-content:center}
.pt-stage{border-left:3px solid var(--color-primary);padding-left:1.15rem;margin:1.7rem 0 0}
.pt-stage>h3{font-size:1.12rem;color:var(--color-text);margin:0 0 .75rem}
.pt-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(248px,1fr));gap:.9rem}
.pt-card{display:flex;flex-direction:column;gap:.4rem;background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-md);padding:1rem;text-decoration:none;color:inherit;transition:border-color .15s ease,transform .15s ease}
.pt-card:hover{border-color:var(--color-primary);transform:translateY(-2px)}
.pt-badge{align-self:flex-start;font-size:.7rem;font-weight:600;color:var(--color-primary);background:var(--color-surface-warm-2);border-radius:999px;padding:.2rem .6rem}
.pt-name{font-size:1rem;line-height:1.35;margin:0;color:var(--color-text)}
.pt-tag{font-size:.84rem;line-height:1.55;color:var(--color-text-light);margin:0;flex:1}
.pt-cta{font-size:.8rem;font-weight:600;color:var(--color-primary)}
.pt-faq details{background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-md);padding:.8rem 1rem;margin-bottom:.6rem}
.pt-faq summary{font-weight:600;color:var(--color-text);cursor:pointer}
.pt-faq p{color:var(--color-text-light);line-height:1.7;margin:.6rem 0 0}
.pt-footer-cta{text-align:center;margin-top:var(--spacing-xl);padding:1.5rem;background:var(--color-surface-warm-2);border:1px solid var(--color-border);border-radius:var(--radius-md)}
.pt-footer-cta a{color:var(--color-primary);font-weight:700;text-decoration:none}
.pt-footer-cta a:hover{text-decoration:underline}
@media(max-width:600px){.pt-grid{grid-template-columns:1fr}.pt-hero{padding:var(--spacing-lg) 0 var(--spacing-sm)}}
"""


def head(lang: str) -> str:
    c = COPY[lang]
    title = fit(c["title_text"], 60, lang + ".title_text")
    desc = fit(c["meta_description"], 155, lang + ".meta_description")
    canonical = url(lang, "/%s/" % SLUG)
    alt = []
    for l in ALL:
        alt.append('<link rel="alternate" hreflang="%s" href="%s">' %
                   (l, url(l, "/%s/" % SLUG)))
    alt.append('<link rel="alternate" hreflang="x-default" href="%s">' %
               url("en", "/%s/" % SLUG))
    return """<!DOCTYPE html>
<html lang="%(lang)s">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>%(title)s</title>
<link rel="canonical" href="%(canonical)s">
%(alt)s
<meta name="description" content="%(desc)s" />
<meta name="keywords" content="free wedding planning tools, wedding planning checklist, wedding planning timeline, wedding guest count calculator, wedding day timeline, free wedding planner, no signup wedding tools">
<meta property="og:type" content="website">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(canonical)s">
<meta property="og:site_name" content="WeddingAI.video">
<meta property="og:locale" content="%(locale)s">
<meta property="og:image" content="https://weddingai.video/images/og-image-1200x630.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%(title)s">
<meta name="twitter:description" content="%(desc)s">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<meta name="theme-color" content="#D4AF37">
<link rel="manifest" href="/manifest.json">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="stylesheet" href="/styles.min.css?v=3.42">
<link rel="stylesheet" href="/styles/i18n.css">
<script defer src="/js/main.min.js?v=3.22"></script>
<script src="/js/langs.js" defer></script>
<script src="/js/i18n.js?v=4.29" defer></script>
<style>%(css)s</style>
%(jsonld)s
</head>
""" % {"lang": lang, "title": esc(title), "desc": esc(desc),
       "canonical": canonical, "alt": "\n".join(alt),
       "locale": LOCALE[lang], "css": CSS, "jsonld": jsonld(lang)}


def jsonld(lang: str) -> str:
    c = COPY[lang]
    canonical = url(lang, "/%s/" % SLUG)
    prefix = "" if lang == "en" else "/" + lang
    items = []
    for pos, slug in enumerate(ALL_SLUGS, 1):
        items.append({
            "@type": "ListItem", "position": pos,
            "item": {"@type": "SoftwareApplication",
                     "url": BASE + prefix + "/tools/" + slug + "/"},
        })
    # Names come from the shared card keys; use the English source text so the
    # graph stays stable across languages (same approach as /tools/ ItemList).
    cards = CARDS_CACHE
    for it, slug in zip(items, ALL_SLUGS):
        it["item"]["name"] = cards[slug]["name"][1]
        it["item"]["applicationCategory"] = "BusinessApplication"
        it["item"]["operatingSystem"] = "Web Browser"
        it["item"]["offers"] = {"@type": "Offer", "price": "0", "priceCurrency": "USD"}
    collection = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": c["h1"], "description": c["meta_description"],
        "url": canonical, "inLanguage": LOCALE[lang],
        "isPartOf": {"@type": "WebSite", "name": "WeddingAI.video", "url": BASE + "/"},
        "mainEntity": {"@type": "ItemList", "numberOfItems": len(items),
                       "itemListElement": items},
    }
    faq = {
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": c[q],
             "acceptedAnswer": {"@type": "Answer", "text": c[a]}}
            for q, a in FAQS
        ],
    }
    crumbs = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1,
             "name": "WeddingAI.video", "item": BASE + prefix + "/"},
            {"@type": "ListItem", "position": 2,
             "name": "Free Tools", "item": BASE + prefix + "/tools/"},
            {"@type": "ListItem", "position": 3,
             "name": "Wedding Planning Tools", "item": canonical},
        ],
    }
    return "".join(
        '<script type="application/ld+json">\n%s\n</script>\n' %
        json.dumps(d, ensure_ascii=False, indent=2)
        for d in (collection, faq, crumbs))


def body(lang: str) -> str:
    c = COPY[lang]
    prefix = "" if lang == "en" else "/" + lang
    out = ['<main id="main-content">', '<div class="pt-wrap">']
    out.append('<section class="pt-hero">')
    out.append("  " + bound("h1", lang, "h1"))
    out.append("  " + bound("lead", lang, "p", "pt-lead"))
    out.append('  <div class="pt-badges">')
    out.append("    " + bound("badge", lang, "span", "pt-hero-badge"))
    out.append('  </div>')
    out.append('</section>')

    out.append('<section class="pt-section">')
    out.append("  " + bound("how_h2", lang, "h2"))
    out.append('  <ol class="pt-steps">')
    for step in ("step1", "step2", "step3"):
        out.append("    <li data-i18n=\"%s\">%s</li>" % (k(step), esc(c[step])))
    out.append('  </ol>')
    out.append('</section>')

    out.append('<section class="pt-section">')
    out.append("  " + bound("timeline_h2", lang, "h2"))
    for stage_key, slugs in STAGES:
        out.append('  <div class="pt-stage">')
        out.append("    " + bound(stage_key, lang, "h3"))
        out.append('    <div class="pt-grid">')
        for slug in slugs:
            out.append(card_html(CARDS_CACHE[slug], lang))
        out.append('    </div>')
        out.append('  </div>')
    out.append('</section>')

    out.append('<section class="pt-section pt-faq">')
    out.append("  " + bound("faq_h2", lang, "h2"))
    for q, a in FAQS:
        out.append('  <details>')
        out.append("    <summary data-i18n=\"%s\">%s</summary>" % (k(q), esc(c[q])))
        out.append("    <p data-i18n=\"%s\">%s</p>" % (k(a), esc(c[a])))
        out.append('  </details>')
    out.append('</section>')

    out.append('<div class="pt-footer-cta">')
    out.append('  <p><a href="%s/tools/" data-i18n="%s">%s</a></p>' %
               (prefix, k("all_tools"), esc(c["all_tools"])))
    out.append('</div>')
    out.extend(['</div>', '</main>'])
    return "\n".join(out)


def localize_chrome(text: str, lang: str) -> str:
    """Static twins carry their own localised links (see #I18N-HUBHEAD)."""
    if lang == "en":
        return text
    return re.sub(
        r'href="/(tools|blog|services|gallery|about|pricing|resources)/',
        lambda m: 'href="/%s/%s/' % (lang, m.group(1)), text)


def build_pages(cards: dict) -> None:
    global CARDS_CACHE
    CARDS_CACHE = cards
    tpl = TEMPLATE.read_text(encoding="utf-8")
    pre, rest = tpl.split('<main id="main-content">', 1)
    _, post = rest.split('</main>', 1)
    chrome_top = pre[pre.index("<body"):]
    chrome_bottom = post[:post.index("</body>")]
    for lang in ALL:
        page = (head(lang) + localize_chrome(chrome_top, lang)
                + body(lang) + localize_chrome(chrome_bottom, lang)
                + "</body>\n</html>\n")
        d = ROOT if lang == "en" else ROOT / lang
        d = d / SLUG
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(page, encoding="utf-8", newline="\n")
    print("pages: %d" % len(ALL))


def sitemap_entry(lang: str) -> str:
    lines = ["    <url>", "        <loc>%s</loc>" % url(lang, "/%s/" % SLUG),
             "        <lastmod>%s</lastmod>" % TODAY,
             "        <changefreq>weekly</changefreq>",
             "        <priority>0.8</priority>"]
    for l in ALL:
        lines.append('        <xhtml:link rel="alternate" hreflang="%s" href="%s" />' %
                     (l, url(l, "/%s/" % SLUG)))
    lines.append('        <xhtml:link rel="alternate" hreflang="x-default" href="%s" />' %
                 url("en", "/%s/" % SLUG))
    lines.append("    </url>")
    return "\n".join(lines) + "\n"


def update_sitemaps() -> None:
    n = 0
    for lang in ALL:
        p = ROOT / ("sitemap-%s.xml" % lang)
        s = p.read_text(encoding="utf-8")
        if "/%s/" % SLUG in s:
            continue
        if "</urlset>" not in s:
            raise SystemExit("[FAIL] %s has no </urlset>" % p)
        p.write_text(s.replace("</urlset>", sitemap_entry(lang) + "</urlset>", 1),
                     encoding="utf-8", newline="\n")
        n += 1
    print("sitemaps updated: %d / 11" % n)


def update_dictionaries() -> None:
    """Append the new keys; NEVER rewrite the whole file (70 万行 diff lesson)."""
    n = 0
    for lang in ALL:
        p = ROOT / "i18n" / ("%s.json" % lang)
        raw = p.read_text(encoding="utf-8")
        data = json.loads(raw)
        new = {k(name): v for name, v in COPY[lang].items()
               if k(name) not in data}
        if not new:
            continue
        eol = "\r\n" if "\r\n" in raw else "\n"
        lines = raw.splitlines(keepends=True)
        close = next(i for i in range(len(lines) - 1, -1, -1)
                     if lines[i].strip() == "}")
        # The previous last entry needs a comma; the new block ends without one.
        prev = close - 1
        while prev >= 0 and not lines[prev].strip():
            prev -= 1
        if not lines[prev].rstrip().endswith(","):
            lines[prev] = lines[prev].rstrip("\r\n") + "," + eol
        block = "".join('  %s: %s%s' % (
            json.dumps(key, ensure_ascii=False),
            json.dumps(val, ensure_ascii=False),
            ",\n" if i < len(new) - 1 else "\n")
            for i, (key, val) in enumerate(new.items()))
        lines.insert(close, block)
        out = "".join(lines)
        check = json.loads(out)
        for key, val in new.items():
            if check.get(key) != val:
                raise SystemExit("[FAIL] %s: %s did not round-trip" % (p, key))
        p.write_text(out, encoding="utf-8", newline="")
        n += 1
    print("dictionaries updated: %d / 11 (%d keys each)" % (n, len(COPY["en"])))


def add_hub_cta() -> None:
    s = HUB.read_text(encoding="utf-8")
    key = k("hub_cta")
    if key in s:
        print("hub CTA: already present")
        return
    # /tools/ has no pt-* stylesheet, so the CTA must be fully self-styled.
    block = ('\n <div style="max-width:1140px;margin:0 auto var(--spacing-xl);'
             'text-align:center;padding:1.5rem;background:var(--color-surface-warm-2);'
             'border:1px solid var(--color-border);border-radius:var(--radius-md)">'
             '\n  <p style="margin:0"><a href="/%s/" data-i18n="%s" '
             'style="color:var(--color-primary);font-weight:700;text-decoration:none">%s</a></p>'
             '\n </div>\n' % (SLUG, key, esc(COPY["en"]["hub_cta"])))
    marker = "</main>"
    if marker not in s:
        raise SystemExit("[FAIL] /tools/ has no </main>")
    s = s.replace(marker, block + marker, 1)
    HUB.write_text(s, encoding="utf-8", newline="")
    print("hub CTA: injected")


def add_backlinks() -> None:
    key = k("backlink")
    n = 0
    for lang in ALL:
        prefix = "" if lang == "en" else "/" + lang
        for slug in ALL_SLUGS:
            p = (ROOT / "tools" if lang == "en" else ROOT / lang / "tools") / slug / "index.html"
            if not p.exists():
                continue
            s = p.read_text(encoding="utf-8")
            if key in s:
                continue
            block = ('<p class="ft-serp-sources"><a href="%s/%s/" data-i18n="%s">%s</a></p>\n'
                     % (prefix, SLUG, key, esc(COPY[lang]["backlink"])))
            if "</main>" in s:
                s = s.replace("</main>", block + "</main>", 1)
            elif "<footer" in s:
                s = s.replace("<footer", block + "<footer", 1)
            else:
                continue
            p.write_text(s, encoding="utf-8", newline="\n")
            n += 1
    print("tool-page backlinks: %d" % n)


def add_middleware_allowlist() -> None:
    s = MIDDLEWARE.read_text(encoding="utf-8")
    if '"planning-tools"' in s:
        print("middleware allowlist: already present")
        return
    old = '"services", "resources", "gallery", "privacy", "terms",'
    new = '"services", "resources", "gallery", "privacy", "terms",\n    "planning-tools",'
    if old not in s:
        raise SystemExit("[FAIL] middleware allowlist anchor not found")
    MIDDLEWARE.write_text(s.replace(old, new, 1), encoding="utf-8", newline="")
    print("middleware allowlist: added planning-tools")


def main() -> None:
    keys = set(COPY["en"])
    for lang, vals in COPY.items():
        if set(vals) != keys:
            raise SystemExit("[FAIL] %s key set differs: missing=%s extra=%s" %
                             (lang, sorted(keys - set(vals)), sorted(set(vals) - keys)))
    for lang in ALL:
        fit(COPY[lang]["title_text"], 60, lang + ".title_text")
        fit(COPY[lang]["meta_description"], 155, lang + ".meta_description")
    cards = extract_cards()
    build_pages(cards)
    update_sitemaps()
    update_dictionaries()
    add_hub_cta()
    add_backlinks()
    add_middleware_allowlist()
    print("done. Next: python .tmp/rebuild-shards-inplace.py")


CARDS_CACHE: dict = {}

if __name__ == "__main__":
    main()
