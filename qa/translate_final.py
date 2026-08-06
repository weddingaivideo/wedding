"""
Final pass: translate all remaining English fallback content to all non-English languages.
Covers index FAQ, vintage restoration page, service descriptions, gallery, etc.

Usage: python qa/translate_final.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
I18N_DIR = ROOT / "i18n"

# All translations organized by key
T = {}

# ━━━ Index page: service description cards ━━━
T["index.p_text.23_languages_dubbing.22222227"] = {
    "ar": "23 لغة — دبلجة وترجمة بالذكاء الاصطناعي للعائلة الدولية.",
    "de": "23 Sprachen — KI-Synchronisation und Untertitel für die internationale Familie.",
    "es": "23 idiomas — doblaje y subtítulos con IA para la familia internacional.",
    "fr": "23 langues — doublage et sous-titres IA pour la famille internationale.",
    "ja": "23言語 — 海外のご家族のためのAI吹き替えと字幕。",
    "pt": "23 idiomas — dublagem e legendas com IA para a família internacional.",
    "ru": "23 языка — ИИ-озвучка и субтитры для международной семьи.",
}
T["index.p_text.ai_archetype_wedding_message.22222223"] = {
    "ar": "رسالة بأسلوب المشاهير مولدة بالذكاء الاصطناعي. مفاجئة، قانونية، أخلاقية.",
    "de": "KI-generierte Promi-Nachricht. Überraschend, legal, ethisch.",
    "es": "Mensaje estilo celebridad generado por IA. Sorprendente, legal, ético.",
    "fr": "Message style célébrité généré par IA. Surprenant, légal, éthique.",
    "ja": "AIが生成する有名人風メッセージ。驚き、合法、倫理的。",
    "pt": "Mensagem estilo celebridade gerada por IA. Surpreendente, legal, ético.",
    "ru": "Сгенерированное ИИ сообщение в стиле знаменитости. Удивительно, законно, этично.",
}
T["index.p_text.cinematic_1_to_3_minute_trailer.22222225"] = {
    "ar": "إعلان تشويقي سينمائي من 1-3 دقائق لوسائل التواصل الاجتماعي والتشغيل في الحفل.",
    "de": "1-3-minütiger filmischer Trailer für soziale Medien und Empfangs-Wiedergabe.",
    "es": "Tráiler cinematográfico de 1-3 minutos para redes sociales y reproducción en la recepción.",
    "fr": "Bande-annonce cinématographique de 1 à 3 minutes pour les réseaux sociaux et la diffusion à la réception.",
    "ja": "SNSや披露宴での上映に最適な1〜3分のシネマティックトレーラー。",
    "pt": "Trailer cinematográfico de 1-3 minutos para redes sociais e exibição na recepção.",
    "ru": "1-3-минутный кинематографичный трейлер для соцсетей и показа на приеме.",
}
T["index.p_text.ghibli_pixar_anime_style.22222228"] = {
    "ar": "أسلوب جيبلي أو بيكسار أو الأنمي مطبق على لقطاتك.",
    "de": "Ghibli-, Pixar- oder Anime-Stil auf Ihre Aufnahmen angewendet.",
    "es": "Estilo Ghibli, Pixar o anime aplicado a su metraje.",
    "fr": "Style Ghibli, Pixar ou anime appliqué à vos séquences.",
    "ja": "ジブリ、ピクサー、アニメスタイルをあなたの映像に適用。",
    "pt": "Estilo Ghibli, Pixar ou anime aplicado às suas filmagens.",
    "ru": "Стиль Ghibli, Pixar или аниме, примененный к вашим кадрам.",
}
T["index.p_text.pet_wedding_video.22222226"] = {
    "ar": "بطولة حيوانك الأليف! افتتاحية ممتعة أو إعلان حفظ التاريخ.",
    "de": "Mit Ihrem Haustier in der Hauptrolle! Lustiger Opener oder Save-the-Date.",
    "es": "¡Protagonizado por su mascota! Apertura divertida o save-the-date.",
    "fr": "Avec votre animal en vedette ! Ouverture amusante ou save-the-date.",
    "ja": "ペット主演！楽しいオープニングやセーブ・ザ・デートに。",
    "pt": "Estrelando seu pet! Abertura divertida ou save-the-date.",
    "ru": "В главной роли ваш питомец! Веселый опенинг или save-the-date.",
}
T["index.p_text.recover_30_year_old_tapes_8mm_to_4k.91827364"] = {
    "ar": "استعد أشرطة VHS عمرها 30 عاماً، ارفع دقة 8mm إلى 4K، صحح الألوان وقلل ضوضاء الصوت. زفاف والديك، متجدد.",
    "de": "Stellen Sie 30 Jahre alte VHS-Bänder wieder her, skalieren Sie 8mm auf 4K hoch, Farbkorrektur und Audio-Rauschunterdrückung. Die Hochzeit Ihrer Eltern, erneuert.",
    "es": "Recupere cintas VHS de 30 años, escale 8mm a 4K, corrija el color y reduzca el ruido de audio. La boda de sus padres, renovada.",
    "fr": "Récupérez des cassettes VHS vieilles de 30 ans, convertissez du 8mm en 4K, correction des couleurs et débruitage audio. Le mariage de vos parents, renouvelé.",
    "ja": "30年前のVHSテープを復元、8mmを4Kにアップスケール、カラー補正とオーディオノイズ除去。ご両親の結婚式を新たに。",
    "pt": "Recupere fitas VHS de 30 anos, escale 8mm para 4K, corrija cores e reduza ruído de áudio. O casamento dos seus pais, renovado.",
    "ru": "Восстановите 30-летние VHS-кассеты, масштабируйте 8mm до 4K, коррекция цвета и шумоподавление звука. Свадьба ваших родителей, обновленная.",
}
T["index.p_text.remote_family_video_message.22222222"] = {
    "ar": "سجلت العائلة البعيدة رسالة وقمنا بدمجها بسلاسة في فيلمك.",
    "de": "Entfernte Familie hat eine Nachricht aufgenommen und wir betten sie nahtlos in Ihren Film ein.",
    "es": "Familiares lejanos grabaron un mensaje y lo integramos perfectamente en su película.",
    "fr": "La famille éloignée a enregistré un message et nous l'intégrons parfaitement dans votre film.",
    "ja": "遠方のご家族が録画したメッセージを、あなたの映像にシームレスに埋め込みます。",
    "pt": "Familiares distantes gravaram uma mensagem e a integramos perfeitamente ao seu filme.",
    "ru": "Удаленные родственники записали сообщение, и мы плавно встраиваем его в ваш фильм.",
}
T["index.p_text.shareable_gifs_and_memes.22222229"] = {
    "ar": "10 صور GIF وميمات قابلة للمشاركة لوسائل التواصل الاجتماعي.",
    "de": "10 teilbare GIFs und Memes für soziale Medien.",
    "es": "10 GIFs y memes compartibles para redes sociales.",
    "fr": "10 GIFs et mèmes partageables pour les réseaux sociaux.",
    "ja": "SNS向けの共有可能なGIFとミーム10点。",
    "pt": "10 GIFs e memes compartilháveis para redes sociais.",
    "ru": "10 GIF-файлов и мемов для соцсетей.",
}
T["index.p_text.tribute_for_a_deceased_loved_one.22222221"] = {
    "ar": "كرّم شخصاً عزيزاً متوفى بمونتاج فيديو تذكاري جميل.",
    "de": "Ehren Sie einen verstorbenen geliebten Menschen mit einer schönen Gedenkvideo-Montage.",
    "es": "Honre a un ser querido fallecido con un hermoso montaje de video conmemorativo.",
    "fr": "Honorez un être cher décédé avec un beau montage vidéo commémoratif.",
    "ja": "亡くなられた大切な方を美しいメモリアルビデオモンタージュで偲びます。",
    "pt": "Honre um ente querido falecido com uma bela montagem de vídeo memorial.",
    "ru": "Почтите память ушедшего близкого человека красивым памятным видеомонтажом.",
}
T["index.p_text.turn_photos_into_cinematic_film.22222224"] = {
    "ar": "حول صور زفافك إلى فيلم سينمائي مولّد بالذكاء الاصطناعي.",
    "de": "Verwandeln Sie Ihre Hochzeitsfotos in einen filmischen KI-generierten Film.",
    "es": "Convierta sus fotos de boda en una película cinematográfica generada por IA.",
    "fr": "Transformez vos photos de mariage en un film cinématographique généré par IA.",
    "ja": "結婚式の写真をAIが生成するシネマティックな映画に変換します。",
    "pt": "Transforme suas fotos de casamento em um filme cinematográfico gerado por IA.",
    "ru": "Превратите ваши свадебные фотографии в кинематографичный фильм, созданный ИИ.",
}

# ━━━ Index page: FAQ answers ━━━
T["index.p_text.ai_safety_answer.99999992"] = {
    "ar": "نستخدم نماذج ذكاء اصطناعي تجارية مع حواجز أمان. يراجع صانع أفلام بشري كل مشروع، ولا نستخدم الذكاء الاصطناعي أبداً لتغيير ملامح الوجه أو شكل الجسم دون موافقة صريحة.",
    "de": "Wir verwenden kommerzielle KI-Modelle mit Sicherheitsvorkehrungen. Ein menschlicher Filmemacher überprüft jedes Projekt, und wir setzen KI niemals ohne ausdrückliche Zustimmung zur Veränderung von Gesichtszügen oder Körperformen ein.",
    "es": "Usamos modelos de IA de nivel comercial con barreras de seguridad. Un cineasta humano revisa cada proyecto, y nunca aplicamos IA para alterar rasgos faciales o formas corporales sin consentimiento explícito.",
    "fr": "Nous utilisons des modèles d'IA de qualité commerciale avec des garde-fous de sécurité. Un cinéaste humain examine chaque projet, et nous n'utilisons jamais l'IA pour modifier les traits du visage ou les formes du corps sans consentement explicite.",
    "ja": "当社は安全対策を備えた商用グレードのAIモデルを使用しています。人間の映像制作者がすべてのプロジェクトを確認し、明示的な同意なしに顔の特徴や体型を変更するためにAIを使用することは決してありません。",
    "pt": "Usamos modelos de IA de nível comercial com barreiras de segurança. Um cineasta humano revisa cada projeto, e nunca aplicamos IA para alterar características faciais ou formas corporais sem consentimento explícito.",
    "ru": "Мы используем коммерческие ИИ-модели с защитными механизмами. Каждый проект проверяется человеком-кинематографистом, и мы никогда не применяем ИИ для изменения черт лица или форм тела без явного согласия.",
}
T["index.p_text.bundle_pricing_answer.99999995"] = {
    "ar": "تنطبق خصومات الحزمة عند حجز خدمتين أو أكثر في نفس المشروع: خصم 10% لخدمتين، 15% لـ 3، و20% لـ 4 خدمات أو أكثر.",
    "de": "Paketrabatte gelten, wenn Sie 2+ Dienste für dasselbe Projekt buchen: 10% Rabatt bei 2 Diensten, 15% bei 3 und 20% bei 4 oder mehr.",
    "es": "Se aplican descuentos por paquete al reservar 2+ servicios en el mismo proyecto: 10% de descuento por 2 servicios, 15% por 3 y 20% por 4 o más.",
    "fr": "Des remises de forfait s'appliquent lorsque vous réservez 2 services ou plus sur le même projet : 10% de remise pour 2 services, 15% pour 3 et 20% pour 4 ou plus.",
    "ja": "同じプロジェクトで2つ以上のサービスを予約するとバンドル割引が適用されます：2サービスで10%オフ、3サービスで15%オフ、4サービス以上で20%オフ。",
    "pt": "Descontos de pacote se aplicam ao reservar 2+ serviços no mesmo projeto: 10% de desconto para 2 serviços, 15% para 3 e 20% para 4 ou mais.",
    "ru": "Скидки за пакет применяются при заказе 2+ услуг в рамках одного проекта: скидка 10% за 2 услуги, 15% за 3 и 20% за 4 и более.",
}
T["index.p_text.footage_privacy_answer.99999991"] = {
    "ar": "يتم تخزين لقطاتك مشفرة على خوادم آمنة في الولايات المتحدة. يتم حذف الملفات تلقائياً بعد 30 يوماً من تسليم المشروع ما لم تطلب التخزين الأرشيفي.",
    "de": "Ihr Material wird verschlüsselt auf sicheren US-basierten Servern gespeichert. Dateien werden 30 Tage nach Projektlieferung automatisch gelöscht, es sei denn, Sie beantragen eine Archivspeicherung.",
    "es": "Su metraje se almacena cifrado en servidores seguros con sede en EE. UU. Los archivos se eliminan automáticamente 30 días después de la entrega del proyecto, a menos que solicite almacenamiento de archivo.",
    "fr": "Vos séquences sont stockées chiffrées sur des serveurs sécurisés basés aux États-Unis. Les fichiers sont automatiquement supprimés 30 jours après la livraison du projet, sauf si vous demandez un stockage d'archives.",
    "ja": "お客様の映像は、米国ベースの安全なサーバーに暗号化されて保存されます。ファイルは、アーカイブ保存をリクエストされない限り、プロジェクト納品から30日後に自動的に削除されます。",
    "pt": "Suas filmagens são armazenadas criptografadas em servidores seguros nos EUA. Os arquivos são excluídos automaticamente 30 dias após a entrega do projeto, a menos que você solicite armazenamento de arquivo.",
    "ru": "Ваши материалы хранятся в зашифрованном виде на защищенных серверах в США. Файлы автоматически удаляются через 30 дней после сдачи проекта, если вы не запросите архивное хранение.",
}
T["index.p_text.ownership_answer.99999993"] = {
    "ar": "أنت تملك الفيديو النهائي. نحتفظ بترخيص غير حصري لاستخدام مقتطفات مجهولة المصدر في محفظتنا (يمكنك إلغاء الاشتراك في أي وقت). أنت حر في استخدام الفيديو تجارياً.",
    "de": "Sie besitzen das endgültige Video. Wir behalten eine nicht-exklusive Lizenz zur Nutzung anonymisierter Auszüge in unserem Portfolio (Sie können jederzeit widersprechen). Sie können Ihr Video frei kommerziell nutzen.",
    "es": "Usted es dueño del video final. Conservamos una licencia no exclusiva para usar extractos anónimos en nuestro portafolio (puede optar por no participar en cualquier momento). Puede usar su video comercialmente.",
    "fr": "Vous êtes propriétaire de la vidéo finale. Nous conservons une licence non exclusive pour utiliser des extraits anonymisés dans notre portfolio (vous pouvez vous y opposer à tout moment). Vous êtes libre d'utiliser votre vidéo commercialement.",
    "ja": "最終的なビデオはお客様の所有物です。当社は匿名化された抜粋をポートフォリオで使用する非独占的ライセンスを保持します（いつでもオプトアウト可能）。商用利用も自由です。",
    "pt": "Você é o proprietário do vídeo final. Mantemos uma licença não exclusiva para usar trechos anônimos em nosso portfólio (você pode optar por sair a qualquer momento). Você está livre para usar seu vídeo comercialmente.",
    "ru": "Вы являетесь владельцем финального видео. Мы сохраняем неисключительную лицензию на использование анонимизированных отрывков в нашем портфолио (вы можете отказаться в любое время). Вы можете свободно использовать видео в коммерческих целях.",
}
T["index.p_text.rush_delivery_answer.99999994"] = {
    "ar": "نعم. تقدم معظم الخدمات توصيلاً سريعاً خلال 48 ساعة مقابل رسوم إضافية بنسبة 30-50%، حسب تعقيد المشروع.",
    "de": "Ja. Die meisten Dienste bieten 48-Stunden-Expresslieferung gegen einen Aufpreis von 30-50%, abhängig von der Projektkomplexität.",
    "es": "Sí. La mayoría de los servicios ofrecen entrega urgente en 48 horas por un cargo adicional del 30-50%, dependiendo de la complejidad del proyecto.",
    "fr": "Oui. La plupart des services proposent une livraison express en 48 heures moyennant un supplément de 30 à 50%, selon la complexité du projet.",
    "ja": "はい。ほとんどのサービスで、プロジェクトの複雑さに応じて30〜50%の追加料金で48時間の急ぎ配送をご利用いただけます。",
    "pt": "Sim. A maioria dos serviços oferece entrega rápida em 48 horas por uma taxa adicional de 30-50%, dependendo da complexidade do projeto.",
    "ru": "Да. Большинство услуг предлагают срочную доставку за 48 часов с дополнительной платой 30-50% в зависимости от сложности проекта.",
}

# ━━━ Index page: FAQ summary questions ━━━
T["index.summary_text.do_you_offer_rush_delivery.99999994"] = {
    "ar": "هل تقدمون توصيلاً سريعاً؟",
    "de": "Bieten Sie Expresslieferung an?",
    "es": "¿Ofrecen entrega urgente?",
    "fr": "Proposez-vous une livraison express ?",
    "ja": "急ぎの配送はありますか？",
    "pt": "Vocês oferecem entrega rápida?",
    "ru": "Предлагаете ли вы срочную доставку?",
}
T["index.summary_text.how_do_you_handle_my_personal_footage.99999991"] = {
    "ar": "كيف تتعاملون مع لقطاتي الشخصية وخصوصيتي؟",
    "de": "Wie gehen Sie mit meinem persönlichen Material und meiner Privatsphäre um?",
    "es": "¿Cómo manejan mi metraje personal y mi privacidad?",
    "fr": "Comment gérez-vous mes séquences personnelles et ma vie privée ?",
    "ja": "個人の映像とプライバシーはどのように扱われますか？",
    "pt": "Como vocês lidam com minhas filmagens pessoais e privacidade?",
    "ru": "Как вы обращаетесь с моими личными материалами и конфиденциальностью?",
}
T["index.summary_text.how_does_pricing_work.99999995"] = {
    "ar": "كيف يعمل التسعير للخدمات المتعددة؟",
    "de": "Wie funktioniert die Preisgestaltung für mehrere Dienste?",
    "es": "¿Cómo funcionan los precios para múltiples servicios?",
    "fr": "Comment fonctionne la tarification pour plusieurs services ?",
    "ja": "複数サービスの料金はどのようになりますか？",
    "pt": "Como funciona o preço para múltiplos serviços?",
    "ru": "Как работает ценообразование при заказе нескольких услуг?",
}
T["index.summary_text.what_about_ai_safety_and_bias.99999992"] = {
    "ar": "ماذا عن سلامة الذكاء الاصطناعي والتحيز في معالجتكم؟",
    "de": "Was ist mit KI-Sicherheit und Voreingenommenheit in Ihrer Verarbeitung?",
    "es": "¿Qué hay de la seguridad y el sesgo de la IA en su procesamiento?",
    "fr": "Qu'en est-il de la sécurité de l'IA et des biais dans votre traitement ?",
    "ja": "AI処理における安全性とバイアスについてはどうですか？",
    "pt": "E quanto à segurança e viés da IA no processamento de vocês?",
    "ru": "Как насчет безопасности ИИ и предвзятости при обработке?",
}
T["index.summary_text.who_owns_the_final_video.99999993"] = {
    "ar": "من يملك الفيديو النهائي وهل يمكنني استخدامه تجارياً؟",
    "de": "Wem gehört das endgültige Video und kann ich es kommerziell nutzen?",
    "es": "¿Quién es el dueño del video final y puedo usarlo comercialmente?",
    "fr": "À qui appartient la vidéo finale et puis-je l'utiliser commercialement ?",
    "ja": "最終ビデオの所有権は誰にあり、商用利用は可能ですか？",
    "pt": "Quem é o proprietário do vídeo final e posso usá-lo comercialmente?",
    "ru": "Кому принадлежит финальное видео и могу ли я использовать его в коммерческих целях?",
}

# ━━━ Vintage restoration page ━━━
T["services.vintage_restoration.h1_text.restore_your_30_year_old_wedding.91827364"] = {
    "ar": "استعد ذكريات زفافك التي عمرها 30 عاماً",
    "de": "Stellen Sie Ihre 30 Jahre alten Hochzeitserinnerungen wieder her",
    "es": "Restaure sus recuerdos de boda de hace 30 años",
    "fr": "Restaurez vos souvenirs de mariage vieux de 30 ans",
    "ja": "30年前の結婚式の思い出を復元しましょう",
    "pt": "Restaure suas memórias de casamento de 30 anos",
    "ru": "Восстановите ваши 30-летние свадебные воспоминания",
}
T["services.vintage_restoration.h2_text.how_it_works.91827364"] = {
    "ar": "كيف يعمل",
    "de": "So funktioniert's",
    "es": "Cómo funciona",
    "fr": "Comment ça marche",
    "ja": "仕組み",
    "pt": "Como funciona",
    "ru": "Как это работает",
}
T["services.vintage_restoration.h2_text.what_we_accept.91827364"] = {
    "ar": "ما نقبله",
    "de": "Was wir akzeptieren",
    "es": "Qué aceptamos",
    "fr": "Ce que nous acceptons",
    "ja": "対応可能なフォーマット",
    "pt": "O que aceitamos",
    "ru": "Что мы принимаем",
}
T["services.vintage_restoration.h2_text.why_this_matters.91827364"] = {
    "ar": "لماذا هذا مهم",
    "de": "Warum das wichtig ist",
    "es": "Por qué esto es importante",
    "fr": "Pourquoi c'est important",
    "ja": "これが重要な理由",
    "pt": "Por que isso importa",
    "ru": "Почему это важно",
}
T["services.vintage_restoration.h3_text.accept_digital.91827364"] = {
    "ar": "الملفات الرقمية",
    "de": "Digitale Dateien",
    "es": "Archivos digitales",
    "fr": "Fichiers numériques",
    "ja": "デジタルファイル",
    "pt": "Arquivos digitais",
    "ru": "Цифровые файлы",
}
T["services.vintage_restoration.h3_text.accept_film.91827364"] = {
    "ar": "بكرات الأفلام",
    "de": "Filmrollen",
    "es": "Rollos de película",
    "fr": "Bobines de film",
    "ja": "フィルムリール",
    "pt": "Rolos de filme",
    "ru": "Кинопленка",
}
T["services.vintage_restoration.h3_text.accept_tape.91827364"] = {
    "ar": "أشرطة الفيديو",
    "de": "Videoband",
    "es": "Cinta de video",
    "fr": "Bande vidéo",
    "ja": "ビデオテープ",
    "pt": "Fita de vídeo",
    "ru": "Видеокассета",
}
T["services.vintage_restoration.h3_text.step_1_send.91827364"] = {
    "ar": "أرسل لنا لقطاتك",
    "de": "Senden Sie uns Ihr Material",
    "es": "Envíenos su metraje",
    "fr": "Envoyez-nous vos séquences",
    "ja": "映像をお送りください",
    "pt": "Envie-nos suas filmagens",
    "ru": "Отправьте нам ваши материалы",
}
T["services.vintage_restoration.h3_text.step_2_diagnose.91827364"] = {
    "ar": "تشخيص وعرض سعر مجاني",
    "de": "Kostenlose Diagnose & Angebot",
    "es": "Diagnóstico y presupuesto gratuitos",
    "fr": "Diagnostic et devis gratuits",
    "ja": "無料診断とお見積もり",
    "pt": "Diagnóstico e orçamento gratuitos",
    "ru": "Бесплатная диагностика и смета",
}
T["services.vintage_restoration.h3_text.step_3_restore.91827364"] = {
    "ar": "الاستعادة والتسليم بالذكاء الاصطناعي",
    "de": "KI-Restaurierung & Lieferung",
    "es": "Restauración y entrega con IA",
    "fr": "Restauration et livraison par IA",
    "ja": "AI復元と納品",
    "pt": "Restauração e entrega com IA",
    "ru": "ИИ-реставрация и доставка",
}
T["services.vintage_restoration.p_text.ai_powered_restoration.91827364"] = {
    "ar": "استعادة مدعومة بالذكاء الاصطناعي: رقمنة VHS/8mm، رفع الدقة إلى 4K، تصحيح الألوان، تقليل ضوضاء الصوت. زفاف والديك، متجدد للجيل القادم.",
    "de": "KI-gestützte Restaurierung: VHS/8mm digitalisieren, auf 4K hochskalieren, Farbe korrigieren, Audio entrauschen. Die Hochzeit Ihrer Eltern, erneuert für die nächste Generation.",
    "es": "Restauración impulsada por IA: digitalice VHS/8mm, escale a 4K, corrija el color, reduzca el ruido de audio. La boda de sus padres, renovada para la próxima generación.",
    "fr": "Restauration assistée par IA : numérisez VHS/8mm, convertissez en 4K, corrigez les couleurs, débruitez l'audio. Le mariage de vos parents, renouvelé pour la prochaine génération.",
    "ja": "AIによる復元：VHS/8mmをデジタル化、4Kにアップスケール、色補正、音声ノイズ除去。ご両親の結婚式を次世代のために新しく。",
    "pt": "Restauração com IA: digitalize VHS/8mm, escale para 4K, corrija cores, reduza ruído de áudio. O casamento dos seus pais, renovado para a próxima geração.",
    "ru": "Реставрация с помощью ИИ: оцифровка VHS/8mm, масштабирование до 4K, коррекция цвета, шумоподавление звука. Свадьба ваших родителей, обновленная для следующего поколения.",
}
T["services.vintage_restoration.p_text.how_it_works_intro.91827364"] = {
    "ar": "ثلاث خطوات. لا حاجة إلى معرفة تقنية.",
    "de": "Drei Schritte. Keine technischen Kenntnisse erforderlich.",
    "es": "Tres pasos. No se requieren conocimientos técnicos.",
    "fr": "Trois étapes. Aucune connaissance technique requise.",
    "ja": "3ステップ。技術知識は不要です。",
    "pt": "Três etapas. Nenhum conhecimento técnico necessário.",
    "ru": "Три шага. Технические знания не требуются.",
}
T["services.vintage_restoration.p_text.what_we_accept_intro.91827364"] = {
    "ar": "شريط وفيلم ورقمي — نتعامل مع كل شيء.",
    "de": "Band, Film und digital — wir kümmern uns um alles.",
    "es": "Cinta, película y digital — lo manejamos todo.",
    "fr": "Bande, film et numérique — nous gérons tout.",
    "ja": "テープ、フィルム、デジタル — すべて対応します。",
    "pt": "Fita, filme e digital — cuidamos de tudo.",
    "ru": "Кассета, пленка и цифра — мы справимся со всем.",
}
T["services.vintage_restoration.p_text.why_this_matters_intro.91827364"] = {
    "ar": "فيديو زفاف والديك، بكرات 8mm لأجدادك، شريط VHS الوحيد الذي كنت تنوي رقمنته لسنوات — هذه ليست مجرد تسجيلات. إنها إرث عائلتك البصري.",
    "de": "Das Hochzeitsvideo Ihrer Eltern, die 8mm-Rollen Ihrer Großeltern, das eine VHS-Band, das Sie seit Jahren digitalisieren wollten — das sind nicht nur Aufnahmen. Es ist das visuelle Erbe Ihrer Familie.",
    "es": "El video de bodas de sus padres, los rollos de 8mm de sus abuelos, la única cinta VHS que ha querido digitalizar durante años — estas no son solo grabaciones. Son el legado visual de su familia.",
    "fr": "La vidéo de mariage de vos parents, les bobines 8mm de vos grands-parents, la seule cassette VHS que vous vouliez numériser depuis des années — ce ne sont pas que des enregistrements. C'est l'héritage visuel de votre famille.",
    "ja": "ご両親の結婚式ビデオ、祖父母の8mmリール、何年もデジタル化しようと思っていたあのVHSテープ — これらは単なる記録ではありません。あなたの家族の視覚的遺産です。",
    "pt": "O vídeo de casamento dos seus pais, os rolos de 8mm dos seus avós, a única fita VHS que você vem querendo digitalizar há anos — não são apenas gravações. É o legado visual da sua família.",
    "ru": "Свадебное видео ваших родителей, 8-мм катушки ваших бабушек и дедушек, та самая VHS-кассета, которую вы годами собирались оцифровать — это не просто записи. Это визуальное наследие вашей семьи.",
}
T["services.vintage_restoration.p_text.why_this_matters_outro.91827364"] = {
    "ar": "كل عام، تصبح 10% أخرى من أشرطة VHS غير قابلة للتشغيل بسبب تحلل الشريط المغناطيسي. لا تدع ذكريات عائلتك تختفي.",
    "de": "Jedes Jahr werden weitere 10% der VHS-Bänder aufgrund von Magnetbandzerfall unspielbar. Lassen Sie Ihre Familienerinnerungen nicht verschwinden.",
    "es": "Cada año, otro 10% de las cintas VHS se vuelven irreproducibles debido a la degradación de la cinta magnética. No deje que los recuerdos de su familia desaparezcan.",
    "fr": "Chaque année, 10% supplémentaires de cassettes VHS deviennent illisibles en raison de la dégradation de la bande magnétique. Ne laissez pas les souvenirs de votre famille disparaître.",
    "ja": "毎年、VHSテープのさらに10%が磁気テープの劣化により再生不能になっています。家族の思い出を失わないでください。",
    "pt": "A cada ano, outros 10% das fitas VHS se tornam impossíveis de reproduzir devido à degradação da fita magnética. Não deixe as memórias da sua família desaparecerem.",
    "ru": "Каждый год еще 10% VHS-кассет становятся невоспроизводимыми из-за разрушения магнитной ленты. Не дайте воспоминаниям вашей семьи исчезнуть.",
}
T["services.vintage_restoration.p_text.step_1_send_desc.91827364"] = {
    "ar": "حمّل الملفات الرقمية من خلال بوابتنا الآمنة، أو أرسل الأشرطة المادية أو بكرات الأفلام إلى مختبرنا. نغطي تكاليف الشحن للطلبات التي تزيد عن 200 دولار.",
    "de": "Laden Sie digitale Dateien über unser sicheres Portal hoch oder senden Sie physische Bänder oder Filmrollen an unser Labor. Wir übernehmen die Versandkosten für Bestellungen über 200 $.",
    "es": "Suba archivos digitales a través de nuestro portal seguro o envíe cintas físicas o rollos de película a nuestro laboratorio. Cubrimos los costos de envío para pedidos superiores a $200.",
    "fr": "Téléchargez des fichiers numériques via notre portail sécurisé ou expédiez des bandes physiques ou des bobines de film à notre laboratoire. Nous couvrons les frais d'expédition pour les commandes de plus de 200 $.",
    "ja": "安全なポータルからデジタルファイルをアップロードするか、物理的なテープやフィルムリールをラボにお送りください。$200以上のご注文で送料無料。",
    "pt": "Envie arquivos digitais através do nosso portal seguro ou envie fitas físicas ou rolos de filme para o nosso laboratório. Cobrimos os custos de envio para pedidos acima de $200.",
    "ru": "Загрузите цифровые файлы через наш защищенный портал или отправьте физические кассеты или кинопленку в нашу лабораторию. Мы покрываем расходы на доставку для заказов свыше $200.",
}
T["services.vintage_restoration.p_text.step_2_diagnose_desc.91827364"] = {
    "ar": "يفحص فريقنا لقطاتك، ويحدد التلف، ويرسل لك عرض سعر غير ملزم عبر البريد الإلكتروني خلال 48 ساعة. لا يتطلب الأمر دفعاً مقدماً.",
    "de": "Unser Team prüft Ihr Material, identifiziert Schäden und sendet Ihnen innerhalb von 48 Stunden ein unverbindliches Angebot per E-Mail. Keine Vorauszahlung erforderlich.",
    "es": "Nuestro equipo inspecciona su metraje, identifica daños y le envía un presupuesto sin compromiso por correo electrónico en un plazo de 48 horas. No se requiere pago por adelantado.",
    "fr": "Notre équipe inspecte vos séquences, identifie les dommages et vous envoie un devis sans engagement par e-mail dans les 48 heures. Aucun paiement initial requis.",
    "ja": "当社のチームがお客様の映像を検査し、損傷を特定して、48時間以内に無料の見積もりをメールでお送りします。前払いは不要です。",
    "pt": "Nossa equipe inspeciona suas filmagens, identifica danos e envia um orçamento sem compromisso por e-mail em até 48 horas. Nenhum pagamento antecipado necessário.",
    "ru": "Наша команда проверяет ваши материалы, выявляет повреждения и отправляет вам необязывающую смету по электронной почте в течение 48 часов. Предоплата не требуется.",
}
T["services.vintage_restoration.p_text.step_3_restore_desc.91827364"] = {
    "ar": "نستعيد لقطاتك في الباقة التي تختارها. تحصل على رابط مراجعة خاص مع علامة مائية. بعد الموافقة، نسلم الملفات النهائية. التوصيل السريع متاح.",
    "de": "Wir restaurieren Ihr Material in dem von Ihnen gewählten Paket. Sie erhalten einen privaten Link zur Überprüfung mit Wasserzeichen. Nach Freigabe liefern wir die endgültigen Dateien. Expresslieferung verfügbar.",
    "es": "Restauramos su metraje en el paquete que elija. Recibirá un enlace de revisión privado con marca de agua. Tras la aprobación, entregamos los archivos finales. Entrega urgente disponible.",
    "fr": "Nous restaurons vos séquences dans le forfait de votre choix. Vous recevez un lien de révision privé avec filigrane. Après approbation, nous livrons les fichiers finaux. Livraison express disponible.",
    "ja": "お選びいただいたパッケージで映像を復元します。ウォーターマーク付きの非公開レビューリンクをお送りします。承認後、最終ファイルをお届けします。急ぎ配送も可能です。",
    "pt": "Restauramos suas filmagens no pacote de sua escolha. Você recebe um link de revisão privado com marca d'água. Após aprovação, entregamos os arquivos finais. Entrega rápida disponível.",
    "ru": "Мы реставрируем ваши материалы в выбранном вами пакете. Вы получаете приватную ссылку для проверки с водяным знаком. После утверждения мы доставляем финальные файлы. Доступна срочная доставка.",
}
T["services.vintage_restoration.summary_text.damaged_tape_recovery.91827364"] = {
    "ar": "شريطي تالف جداً لدرجة أنه لا يعمل. هل لا يزال بإمكانكم استعادته؟",
    "de": "Mein Band ist so beschädigt, dass es nicht mehr abspielt. Können Sie es trotzdem wiederherstellen?",
    "es": "Mi cinta está tan dañada que no se reproduce. ¿Aún pueden recuperarla?",
    "fr": "Ma cassette est tellement endommagée qu'elle ne peut pas être lue. Pouvez-vous encore la récupérer ?",
    "ja": "テープがひどく損傷していて再生できません。それでも復元できますか？",
    "pt": "Minha fita está tão danificada que não reproduz. Vocês ainda conseguem recuperá-la?",
    "ru": "Моя кассета настолько повреждена, что не воспроизводится. Вы все еще можете ее восстановить?",
}
T["services.vintage_restoration.p_text.damaged_tape_recovery_answer.91827364"] = {
    "ar": "في معظم الحالات، نعم. يستخدم فريقنا أجهزة VCR احترافية مع TBC مدمج (تصحيح القاعدة الزمنية) ويمكنه لصق الأشرطة المقطوعة. حتى الأشرطة المتعفنة يمكن تنظيفها ورقمنتها غالباً. معدل النجاح: ~95% لأشرطة VHS.",
    "de": "In den meisten Fällen ja. Unser Team verwendet professionelle Videorekorder mit eingebautem TBC (Time-Base Correction) und kann gerissene Bänder spleißen. Selbst verschimmelte Bänder können oft gereinigt und digitalisiert werden. Erfolgsquote: ~95% bei VHS-Bändern.",
    "es": "En la mayoría de los casos, sí. Nuestro equipo utiliza VCR profesionales con TBC integrado (corrección de base de tiempo) y puede empalmar cintas rotas. Incluso las cintas con moho a menudo se pueden limpiar y digitalizar. Tasa de éxito: ~95% para cintas VHS.",
    "fr": "Dans la plupart des cas, oui. Notre équipe utilise des magnétoscopes professionnels avec TBC intégré (correction de base de temps) et peut réparer les bandes cassées. Même les bandes moisies peuvent souvent être nettoyées et numérisées. Taux de réussite : ~95% pour les cassettes VHS.",
    "ja": "ほとんどの場合、可能です。当社のチームはTBC（タイムベース補正）内蔵のプロ用VCRを使用し、破損したテープの接合も可能です。カビが生えたテープも多くの場合、クリーニングしてデジタル化できます。成功率：VHSテープで約95%。",
    "pt": "Na maioria dos casos, sim. Nossa equipe usa VCRs profissionais com TBC integrado (correção de base de tempo) e pode emendar fitas quebradas. Até fitas mofadas podem ser limpas e digitalizadas. Taxa de sucesso: ~95% para fitas VHS.",
    "ru": "В большинстве случаев — да. Наша команда использует профессиональные видеомагнитофоны со встроенным TBC (коррекция временной базы) и может склеивать порванные ленты. Даже заплесневелые кассеты часто можно очистить и оцифровать. Успешность: ~95% для VHS-кассет.",
}
T["services.vintage_restoration.summary_text.upscaling_4k_quality.91827364"] = {
    "ar": "هل رفع الدقة إلى 4K سيجعل لقطاتي القديمة تبدو مزيفة؟",
    "de": "Wird das Hochskalieren auf 4K mein altes Material künstlich aussehen lassen?",
    "es": "¿El escalado a 4K hará que mi metraje antiguo se vea falso?",
    "fr": "La conversion en 4K rendra-t-elle mes anciennes séquences artificielles ?",
    "ja": "4Kへのアップスケールで古い映像が不自然に見えませんか？",
    "pt": "O escalonamento para 4K fará minhas filmagens antigas parecerem falsas?",
    "ru": "Не сделает ли масштабирование до 4K мои старые кадры искусственными?",
}
T["services.vintage_restoration.p_text.upscaling_4k_quality_answer.91827364"] = {
    "ar": "لا. تم تدريب مكبر الدقة بالذكاء الاصطناعي لدينا خصيصاً على لقطات الزفاف الأرشيفية. يضيف تفاصيل واقعية دون المظهر 'البلاستيكي' للمكبرات العامة. يحافظ تصحيح الألوان على الإحساس الدافئ والحنيني للقطاتك الأصلية.",
    "de": "Nein. Unser KI-Upscaler wurde speziell auf archiviertem Hochzeitsmaterial trainiert. Er fügt realistische Details hinzu, ohne den 'plastischen' Look generischer Upscaler. Die Farbkorrektur bewahrt das warme, nostalgische Gefühl Ihres Originalmaterials.",
    "es": "No. Nuestro escalador de IA está entrenado específicamente en metraje de bodas de archivo. Agrega detalles realistas sin el aspecto 'plástico' de los escaladores genéricos. La corrección de color preserva la sensación cálida y nostálgica de su metraje original.",
    "fr": "Non. Notre upscaler IA est spécialement entraîné sur des séquences de mariage d'archives. Il ajoute des détails réalistes sans l'aspect 'plastique' des upscalers génériques. La correction des couleurs préserve la sensation chaleureuse et nostalgique de vos séquences originales.",
    "ja": "いいえ。当社のAIアップスケーラーは、アーカイブされた結婚式の映像で特別に訓練されています。一般的なアップスケーラーのような「プラスチック感」のない、リアルなディテールを追加します。色補正により、オリジナル映像の温かみのある懐かしい雰囲気を保ちます。",
    "pt": "Não. Nosso upscaler de IA é treinado especificamente em filmagens de casamento de arquivo. Ele adiciona detalhes realistas sem a aparência 'plástica' dos upscalers genéricos. A correção de cor preserva a sensação calorosa e nostálgica de suas filmagens originais.",
    "ru": "Нет. Наш ИИ-апскейлер специально обучен на архивных свадебных материалах. Он добавляет реалистичные детали без 'пластикового' вида обычных апскейлеров. Цветокоррекция сохраняет теплое, ностальгическое ощущение ваших оригинальных кадров.",
}
T["services.vintage_restoration.summary_text.what_tape_formats_accepted.91827364"] = {
    "ar": "ما هي تنسيقات الأشرطة والأفلام التي تقبلونها؟",
    "de": "Welche Band- und Filmformate akzeptieren Sie?",
    "es": "¿Qué formatos de cinta y película aceptan?",
    "fr": "Quels formats de bande et de film acceptez-vous ?",
    "ja": "どのようなテープやフィルムのフォーマットに対応していますか？",
    "pt": "Quais formatos de fita e filme vocês aceitam?",
    "ru": "Какие форматы кассет и пленки вы принимаете?",
}
T["services.vintage_restoration.p_text.what_tape_formats_accepted_answer.91827364"] = {
    "ar": "نقبل VHS و S-VHS و VHS-C و Hi8 و Digital8 و MiniDV و Betamax و MiniDVD وفيلم 8mm و Super 8 وفيلم 16mm. إذا كان لديك تنسيق غير مدرج هنا، اتصل بنا — يمكننا على الأرجح التعامل معه.",
    "de": "Wir akzeptieren VHS, S-VHS, VHS-C, Hi8, Digital8, MiniDV, Betamax, MiniDVD, 8mm-Film, Super 8 und 16mm-Film. Wenn Sie ein hier nicht aufgeführtes Format haben, kontaktieren Sie uns — wir können es wahrscheinlich verarbeiten.",
    "es": "Aceptamos VHS, S-VHS, VHS-C, Hi8, Digital8, MiniDV, Betamax, MiniDVD, película de 8mm, Super 8 y película de 16mm. Si tiene un formato no listado aquí, contáctenos — probablemente podamos manejarlo.",
    "fr": "Nous acceptons VHS, S-VHS, VHS-C, Hi8, Digital8, MiniDV, Betamax, MiniDVD, film 8mm, Super 8 et film 16mm. Si vous avez un format non répertorié ici, contactez-nous — nous pouvons probablement le traiter.",
    "ja": "VHS、S-VHS、VHS-C、Hi8、Digital8、MiniDV、Betamax、MiniDVD、8mmフィルム、Super 8、16mmフィルムに対応しています。ここに記載のないフォーマットをお持ちの場合は、お問い合わせください — ほとんどの場合対応可能です。",
    "pt": "Aceitamos VHS, S-VHS, VHS-C, Hi8, Digital8, MiniDV, Betamax, MiniDVD, filme 8mm, Super 8 e filme 16mm. Se você tiver um formato não listado aqui, entre em contato — provavelmente podemos lidar com ele.",
    "ru": "Мы принимаем VHS, S-VHS, VHS-C, Hi8, Digital8, MiniDV, Betamax, MiniDVD, 8-мм пленку, Super 8 и 16-мм пленку. Если у вас есть формат, не указанный здесь, свяжитесь с нами — мы, скорее всего, сможем с ним работать.",
}
T["services.vintage_restoration.p_text.accept_digital_desc.91827364"] = {
    "ar": "MP4 و MOV و AVI و MKV و MPG و WebM — أي دقة من 144p إلى 4K. يمكننا أيضاً قبول أقراص DVD و Blu-ray المستخرجة.",
    "de": "MP4, MOV, AVI, MKV, MPG, WebM — jede Auflösung von 144p bis 4K. Wir können auch gerippte DVDs und Blu-rays akzeptieren.",
    "es": "MP4, MOV, AVI, MKV, MPG, WebM — cualquier resolución desde 144p hasta 4K. También podemos aceptar DVD y Blu-ray ripeados.",
    "fr": "MP4, MOV, AVI, MKV, MPG, WebM — toute résolution de 144p à 4K. Nous pouvons également accepter les DVD et Blu-ray extraits.",
    "ja": "MP4、MOV、AVI、MKV、MPG、WebM — 144pから4Kまでの任意の解像度。リッピングしたDVDやBlu-rayも受け付け可能です。",
    "pt": "MP4, MOV, AVI, MKV, MPG, WebM — qualquer resolução de 144p a 4K. Também podemos aceitar DVDs e Blu-rays ripados.",
    "ru": "MP4, MOV, AVI, MKV, MPG, WebM — любое разрешение от 144p до 4K. Мы также можем принимать скопированные DVD и Blu-ray.",
}
T["services.vintage_restoration.p_text.accept_film_desc.91827364"] = {
    "ar": "فيلم 8mm و Super 8 و 16mm. نعمل مع مختبر شريك لمسح الأفلام المادية (مدرج في السعر).",
    "de": "8mm, Super 8 und 16mm Film. Wir arbeiten mit einem Partnerlabor für das physische Filmscannen (im Preis inbegriffen).",
    "es": "Película de 8mm, Super 8 y 16mm. Trabajamos con un laboratorio asociado para el escaneo de película física (incluido en el precio).",
    "fr": "Film 8mm, Super 8 et 16mm. Nous travaillons avec un laboratoire partenaire pour la numérisation de films physiques (inclus dans le prix).",
    "ja": "8mm、Super 8、16mmフィルム。物理フィルムのスキャンは提携ラボが担当します（料金に含まれています）。",
    "pt": "Filme 8mm, Super 8 e 16mm. Trabalhamos com um laboratório parceiro para digitalização de filme físico (incluído no preço).",
    "ru": "8-мм, Super 8 и 16-мм пленка. Мы работаем с партнерской лабораторией для физического сканирования пленки (включено в стоимость).",
}
T["services.vintage_restoration.p_text.accept_tape_desc.91827364"] = {
    "ar": "VHS و S-VHS و VHS-C و Hi8 و Digital8 و MiniDV و Betamax و MiniDVD. حتى الأشرطة التي لم تعد تعمل — يمكن لأدوات الاسترداد الجنائي لدينا في كثير من الأحيان استخراج إشارة الفيديو.",
    "de": "VHS, S-VHS, VHS-C, Hi8, Digital8, MiniDV, Betamax, MiniDVD. Selbst Bänder, die nicht mehr abspielen — unsere forensischen Wiederherstellungstools können oft das Videosignal extrahieren.",
    "es": "VHS, S-VHS, VHS-C, Hi8, Digital8, MiniDV, Betamax, MiniDVD. Incluso cintas que ya no se reproducen — nuestras herramientas de recuperación forense a menudo pueden extraer la señal de video.",
    "fr": "VHS, S-VHS, VHS-C, Hi8, Digital8, MiniDV, Betamax, MiniDVD. Même les bandes qui ne sont plus lisibles — nos outils de récupération forensique peuvent souvent extraire le signal vidéo.",
    "ja": "VHS、S-VHS、VHS-C、Hi8、Digital8、MiniDV、Betamax、MiniDVD。再生不能になったテープでも — 当社のフォレンジック復旧ツールでビデオ信号を抽出できることがよくあります。",
    "pt": "VHS, S-VHS, VHS-C, Hi8, Digital8, MiniDV, Betamax, MiniDVD. Até fitas que não reproduzem mais — nossas ferramentas de recuperação forense muitas vezes podem extrair o sinal de vídeo.",
    "ru": "VHS, S-VHS, VHS-C, Hi8, Digital8, MiniDV, Betamax, MiniDVD. Даже кассеты, которые больше не воспроизводятся — наши инструменты криминалистического восстановления часто могут извлечь видеосигнал.",
}

# ━━━ Gallery meta description ━━━
T["gallery.meta_description.real_before_and_after_examples_of_weddin.16218913"] = {
    "ar": "أمثلة حقيقية قبل وبعد لاستعادة فيديو الزفاف، أفلام بالذكاء الاصطناعي، ومشاريع مخصصة. شاهد ما يمكن أن يحققه WeddingAI.video.",
    "de": "Echte Vorher-Nachher-Beispiele für Hochzeitsvideo-Restaurierung, KI-Filme und individuelle Projekte. Sehen Sie, was WeddingAI.video erreichen kann.",
    "es": "Ejemplos reales de antes y después de restauración de video de bodas, películas con IA y proyectos personalizados. Vea lo que WeddingAI.video puede lograr.",
    "fr": "Exemples réels avant-après de restauration de vidéo de mariage, films IA et projets personnalisés. Voyez ce que WeddingAI.video peut accomplir.",
    "ja": "結婚式ビデオの復元、AIフィルム、カスタムプロジェクトの実際のビフォーアフター事例。WeddingAI.videoが実現できることをご覧ください。",
    "pt": "Exemplos reais de antes e depois de restauração de vídeo de casamento, filmes com IA e projetos personalizados. Veja o que o WeddingAI.video pode alcançar.",
    "ru": "Реальные примеры до и после реставрации свадебного видео, ИИ-фильмов и индивидуальных проектов. Посмотрите, чего может достичь WeddingAI.video.",
}
T["gallery.meta_description.view_before_and_after_examples_of_ai_wed.59645072"] = {
    "ar": "شاهد أمثلة قبل وبعد لاستعادة فيديو الزفاف بالذكاء الاصطناعي، الحركة البطيئة، الدبلجة متعددة اللغات، والمزيد.",
    "fr": "Voir des exemples avant-après de restauration de vidéo de mariage par IA, ralenti, doublage multilingue, et plus.",
    "pt": "Veja exemplos de antes e depois de restauração de vídeo de casamento com IA, câmera lenta, dublagem multilíngue e muito mais.",
    "ru": "Посмотрите примеры до и после реставрации свадебного видео с ИИ, замедленной съемки, многоязычного дубляжа и многого другого.",
}

# ━━━ Print ━━━
def main():
    print("=" * 70)
    print("WeddingAI.video — FINAL Translation Pass")
    print("=" * 70)

    with open(I18N_DIR / "en.json", encoding="utf-8") as f:
        en_data = json.load(f)

    # Collect all target languages from translation dicts
    all_langs = set()
    for langs in T.values():
        all_langs.update(langs.keys())

    total_translated = 0
    for lang in sorted(all_langs):
        json_path = I18N_DIR / f"{lang}.json"
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        count = 0
        for key, en_val in en_data.items():
            if key not in data:
                continue
            if key not in T:
                continue
            if lang not in T[key]:
                continue
            if data[key] == en_val:  # only if still English fallback
                data[key] = T[key][lang]
                count += 1

        if count > 0:
            sorted_data = dict(sorted(data.items()))
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(sorted_data, f, ensure_ascii=False, indent=2)
                f.write("\n")
            print(f"  {lang}: {count} keys translated")
            total_translated += count
        else:
            print(f"  {lang}: no new translations needed")

    print(f"\n  Total translated: {total_translated}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
