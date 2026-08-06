"""
Translate all English fallback values in non-English language JSON files.
Uses key-based matching to ensure no translations are missed.

Usage: python qa/translate_i18n.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
I18N_DIR = ROOT / "i18n"

# Key-based translations: {key_suffix: {lang: translated_text}}
# key_suffix is the last part of the key (after the last dot) for brevity
KEY_TRANSLATIONS = {
    # ── 404 page ──
    "404.meta_description.the_page_you_were_looking_for_doesn_t_ex.68869429": {
        "ar": "الصفحة التي كنت تبحث عنها غير موجودة. تصفح خدمات فيديو الزفاف لدينا أو عد إلى الصفحة الرئيسية. WeddingAI.video",
        "fr": "La page que vous recherchez n'existe pas. Parcourez nos services de vidéo de mariage ou retournez à l'accueil. WeddingAI.video",
        "pt": "A página que você procurava não existe. Navegue pelos nossos serviços de vídeo de casamento ou volte para a página inicial. WeddingAI.video",
        "ru": "Страница, которую вы искали, не существует. Просмотрите наши услуги по свадебному видео или вернитесь на главную. WeddingAI.video",
        "zh": "您要找的页面不存在。浏览我们的婚礼视频服务或返回首页。WeddingAI.video",
    },
    "404.a_text.vintage_restoration.91827364": {
        "ar": "استعادة الفيديو القديم",
        "fr": "Restauration Vintage",
        "pt": "Restauração Vintage",
        "ru": "Винтажная реставрация",
        "zh": "老视频修复",
    },
    # ── about page ──
    "about.meta_description.filmmakers_and_ai_engineers_building_ai.02782150": {
        "ar": "صانعو أفلام ومهندسو ذكاء اصطناعي يبنون خدمات فيديو زفاف مدعومة بالذكاء الاصطناعي. تعرف على فريق WeddingAI.video.",
        "fr": "Cinéastes et ingénieurs IA créant des services de vidéo de mariage alimentés par l'IA. Découvrez l'équipe derrière WeddingAI.video.",
        "pt": "Cineastas e engenheiros de IA construindo serviços de vídeo de casamento com IA. Conheça a equipe por trás do WeddingAI.video.",
        "ru": "Кинематографисты и инженеры ИИ создают сервисы свадебного видео на базе ИИ. Познакомьтесь с командой WeddingAI.video.",
    },
    "about.title_text.about_us_filmmakers_ai_engineers_wedding.68386460": {
        "ar": "من نحن | صانعو أفلام + مهندسو ذكاء اصطناعي | WeddingAI.video",
        "fr": "À propos | Cinéastes + Ingénieurs IA | WeddingAI.video",
        "pt": "Sobre Nós | Cineastas + Engenheiros de IA | WeddingAI.video",
        "ru": "О нас | Кинематографисты + Инженеры ИИ | WeddingAI.video",
    },
    # ── blog ──
    "blog.meta_description.50_in_depth_articles_on_wedding_video_re.17313271": {
        "ar": "50 مقالاً متعمقاً حول استعادة فيديو الزفاف، التحرير بالذكاء الاصطناعي، الحركة البطيئة، تكريم العائلة — للأزواج والعائلات. WeddingAI.video",
        "de": "50 ausführliche Artikel über Hochzeitsvideo-Restaurierung, KI-Bearbeitung, Zeitlupe, Familienehrungen — für Paare und Familien. WeddingAI.video",
        "es": "50 artículos detallados sobre restauración de video de bodas, edición con IA, cámara lenta, homenajes familiares — para parejas y familias. WeddingAI.video",
        "fr": "50 articles approfondis sur la restauration de vidéos de mariage, l'édition IA, le ralenti, les hommages familiaux — pour les couples et les familles. WeddingAI.video",
        "ja": "結婚式ビデオの復元、AI編集、スローモーション、家族への追悼に関する50の詳細記事 — カップルとご家族向け。WeddingAI.video",
        "pt": "50 artigos detalhados sobre restauração de vídeo de casamento, edição com IA, câmera lenta, homenagens familiares — para casais e famílias. WeddingAI.video",
        "ru": "50 подробных статей о реставрации свадебного видео, ИИ-редактировании, замедленной съемке, семейных трибьютах — для пар и семей. WeddingAI.video",
        "zh": "50篇关于婚礼视频修复、AI编辑、慢动作、家庭致敬的深度文章 — 为夫妇和家庭服务。WeddingAI.video",
    },
    # ── cart ──
    "cart.meta_description.review_and_customize_your_wedding_video.43773880": {
        "ar": "راجع وخصص خدمات فيديو الزفاف الخاصة بك — دفع بنقرة واحدة للباقات والإضافات.",
        "fr": "Examinez et personnalisez vos services de vidéo de mariage — paiement en un clic pour les forfaits et suppléments.",
        "pt": "Revise e personalize seus serviços de vídeo de casamento — checkout com um clique para pacotes e complementos.",
        "ru": "Просмотрите и настройте услуги свадебного видео — оформление заказа в один клик для пакетов и дополнений.",
    },
    # ── gallery ──
    "gallery.meta_description.view_before_and_after_examples_of_ai_wed.59645072": {
        "ar": "شاهد أمثلة قبل وبعد لاستعادة فيديو الزفاف بالذكاء الاصطناعي، الحركة البطيئة، الدبلجة متعددة اللغات، والمزيد.",
        "fr": "Voir des exemples avant-après de restauration de vidéo de mariage par IA, ralenti, doublage multilingue, et plus.",
        "pt": "Veja exemplos de antes e depois de restauração de vídeo de casamento com IA, câmera lenta, dublagem multilíngue e muito mais.",
        "ru": "Посмотрите примеры до и после реставрации свадебного видео с ИИ, замедленной съемки, многоязычного дубляжа и многого другого.",
    },
    # ── order ──
    "order.input_placeholder.e_g_sarah_johnson.45211033": {
        "ar": "مثال: سارة جونسون",
        "de": "z.B. Sarah Johnson",
        "es": "ej. Sarah Johnson",
        "fr": "ex. Sarah Johnson",
        "ja": "例：Sarah Johnson",
        "pt": "ex. Sarah Johnson",
        "ru": "напр. Sarah Johnson",
        "th": "เช่น Sarah Johnson",
    },
    "order.input_placeholder.e_g_sarah_example_com.08712572": {
        "ar": "مثال: sarah@example.com",
        "de": "z.B. sarah@example.com",
        "es": "ej. sarah@example.com",
        "fr": "ex. sarah@example.com",
        "ja": "例：sarah@example.com",
        "pt": "ex. sarah@example.com",
        "ru": "напр. sarah@example.com",
        "th": "เช่น sarah@example.com",
    },
    "order.textarea_placeholder.describe_your_vision_the_current_state_o.89880061": {
        "ar": "صف رؤيتك، الحالة الحالية للقطات (تنسيق الشريط، الحالة، المدة)، وأي طلبات محددة.",
        "de": "Beschreiben Sie Ihre Vision, den aktuellen Zustand Ihres Materials (Bandformat, Zustand, Länge) und spezifische Wünsche.",
        "es": "Describa su visión, el estado actual de su material (formato de cinta, condición, duración) y cualquier solicitud específica.",
        "fr": "Décrivez votre vision, l'état actuel de vos séquences (format de bande, état, durée) et toute demande spécifique.",
        "ja": "ご希望のイメージ、映像の現在の状態（テープ形式、状態、長さ）、特別なご要望をお聞かせください。",
        "pt": "Descreva sua visão, o estado atual do seu material (formato de fita, condição, duração) e quaisquer solicitações específicas.",
        "ru": "Опишите ваше видение, текущее состояние материала (формат пленки, состояние, продолжительность) и любые особые пожелания.",
        "th": "อธิบายวิสัยทัศน์ของคุณ สถานะปัจจุบันของฟุตเทจ (รูปแบบเทป สภาพ ความยาว) และคำขอเฉพาะใดๆ",
    },
    "order.meta_description.ready_to_restore_or_create_your_wedding.47269706": {
        "ar": "احصل على عرض سعر مجاني بدون التزام. شارك رؤيتك — سنرد بتوصية مخصصة وأسعار خلال 24 ساعة.",
        "de": "Erhalten Sie ein kostenloses, unverbindliches Angebot. Teilen Sie Ihre Vision — wir antworten innerhalb von 24 Stunden mit einer persönlichen Empfehlung und Preisangabe.",
        "es": "Obtenga un presupuesto gratuito y sin compromiso. Comparta su visión — le responderemos con una recomendación personalizada y precios en 24 horas.",
        "fr": "Obtenez un devis gratuit et sans engagement. Partagez votre vision — nous vous répondrons avec une recommandation personnalisée et un tarif sous 24 heures.",
        "ja": "無料・無義務の見積もりを入手。あなたのビジョンを共有してください — 24時間以内にパーソナライズされた提案と料金で返信します。",
        "pt": "Obtenha um orçamento gratuito e sem compromisso. Compartilhe sua visão — responderemos com uma recomendação personalizada e preços em 24 horas.",
        "ru": "Получите бесплатную смету без обязательств. Поделитесь своим видением — мы ответим с персонализированной рекомендацией и ценой в течение 24 часов.",
        "th": "รับใบเสนอราคาฟรีไม่มีข้อผูกมัด แบ่งปันวิสัยทัศน์ของคุณ — เราจะตอบกลับพร้อมคำแนะนำและราคาที่ปรับให้เหมาะกับคุณภายใน 24 ชั่วโมง",
    },
    # ── pricing ──
    "pricing.meta_description.simple_transparent_pricing_for_ai_wedd.82339639": {
        "ar": "أسعار بسيطة وشفافة لخدمات فيديو الزفاف بالذكاء الاصطناعي. لا رسوم مخفية. الباقات تبدأ من $79. WeddingAI.video",
        "de": "Einfache, transparente Preise für KI-Hochzeitsvideo-Dienste. Keine versteckten Gebühren. Pakete ab $79. WeddingAI.video",
        "es": "Precios simples y transparentes para servicios de video de bodas con IA. Sin cargos ocultos. Paquetes desde $79. WeddingAI.video",
        "fr": "Tarification simple et transparente pour les services de vidéo de mariage IA. Pas de frais cachés. Forfaits à partir de 79 $. WeddingAI.video",
        "ja": "AI結婚式ビデオサービスのシンプルで透明な料金体系。隠れた手数料なし。パッケージは$79から。WeddingAI.video",
        "pt": "Preços simples e transparentes para serviços de vídeo de casamento com IA. Sem taxas ocultas. Pacotes a partir de $79. WeddingAI.video",
        "ru": "Простые, прозрачные цены на услуги свадебного видео с ИИ. Никаких скрытых платежей. Пакеты от $79. WeddingAI.video",
        "th": "ราคาที่เรียบง่ายและโปร่งใสสำหรับบริการวิดีโอแต่งงานด้วย AI ไม่มีค่าธรรมเนียมแอบแฝง แพ็คเกจเริ่มต้นที่ $79. WeddingAI.video",
    },
    # ── privacy ──
    "privacy.meta_description.privacy_policy_for_weddingai_video_learn.48520857": {
        "de": "Datenschutzerklärung für WeddingAI.video. Erfahren Sie, wie wir Ihre Daten erfassen, verwenden und schützen.",
        "es": "Política de privacidad de WeddingAI.video. Conozca cómo recopilamos, usamos y protegemos sus datos.",
        "fr": "Politique de confidentialité de WeddingAI.video. Découvrez comment nous collectons, utilisons et protégeons vos données.",
        "ja": "WeddingAI.videoのプライバシーポリシー。お客様のデータの収集、利用、保護方法についてご説明します。",
        "pt": "Política de privacidade do WeddingAI.video. Saiba como coletamos, usamos e protegemos seus dados.",
        "ru": "Политика конфиденциальности WeddingAI.video. Узнайте, как мы собираем, используем и защищаем ваши данные.",
        "th": "นโยบายความเป็นส่วนตัวของ WeddingAI.video เรียนรู้วิธีที่เรารวบรวม ใช้ และปกป้องข้อมูลของคุณ",
        "zh": "WeddingAI.video 隐私政策。了解我们如何收集、使用和保护您的数据。",
    },
    # ── resources ──
    "resources.meta_description.in_depth_wedding_video_guides_choose_a_v.17819588": {
        "ar": "أدلة فيديو زفاف متعمقة: اختر مصور فيديو، أفلام زفاف بالذكاء الاصطناعي، استعادة الأشرطة القديمة، الدبلجة متعددة اللغات، والمزيد.",
        "de": "Ausführliche Hochzeitsvideo-Ratgeber: Wählen Sie einen Videografen, KI-Hochzeitsfilme, restaurieren Sie alte Bänder, mehrsprachige Synchronisation und mehr.",
        "es": "Guías detalladas de video de bodas: elija un videógrafo, películas de boda con IA, restaure cintas antiguas, doblaje multilingüe y más.",
        "fr": "Guides détaillés de vidéo de mariage : choisir un vidéaste, films de mariage IA, restaurer d'anciennes bandes, doublage multilingue, et plus.",
        "ja": "詳細な結婚式ビデオガイド：ビデオグラファーの選び方、AI結婚式フィルム、古いテープの復元、多言語吹き替えなど。",
        "pt": "Guias detalhados de vídeo de casamento: escolha um videógrafo, filmes de casamento com IA, restaure fitas antigas, dublagem multilíngue e muito mais.",
        "ru": "Подробные руководства по свадебному видео: выбор видеооператора, свадебные фильмы с ИИ, реставрация старых пленок, многоязычный дубляж и многое другое.",
        "th": "คู่มือวิดีโอแต่งงานเชิงลึก: เลือกช่างวิดีโอ ภาพยนตร์แต่งงานด้วย AI ฟื้นฟูเทปเก่า พากย์หลายภาษา และอื่นๆ",
        "zh": "深度婚礼视频指南：选择摄像师、AI婚礼影片、修复老旧录像带、多语言配音等。",
    },
    # ── search ──
    "search.meta_description.search_weddingai_video_for_ai_wedding_vi.18232552": {
        "ar": "ابحث في WeddingAI.video عن خدمات فيديو الزفاف بالذكاء الاصطناعي: الاستعادة، الدبلجة متعددة اللغات، الحركة البطيئة، الإعلانات التشويقية، التكريم.",
        "de": "Durchsuchen Sie WeddingAI.video nach KI-Hochzeitsvideo-Diensten: Restaurierung, mehrsprachige Synchronisation, Zeitlupe, Trailer, Ehrungen.",
        "es": "Busque en WeddingAI.video servicios de video de bodas con IA: restauración, doblaje multilingüe, cámara lenta, tráileres, homenajes.",
        "fr": "Recherchez sur WeddingAI.video des services de vidéo de mariage IA : restauration, doublage multilingue, ralenti, bandes-annonces, hommages.",
        "ja": "WeddingAI.videoでAI結婚式ビデオサービスを検索：復元、多言語吹き替え、スローモーション、トレーラー、追悼。",
        "pt": "Pesquise no WeddingAI.video por serviços de vídeo de casamento com IA: restauração, dublagem multilíngue, câmera lenta, trailers, homenagens.",
        "ru": "Поиск на WeddingAI.video услуг свадебного видео с ИИ: реставрация, многоязычный дубляж, замедленная съемка, трейлеры, трибьюты.",
        "th": "ค้นหา WeddingAI.video สำหรับบริการวิดีโอแต่งงานด้วย AI: การฟื้นฟู การพากย์หลายภาษา สโลว์โมชั่น ตัวอย่าง การรำลึก",
        "zh": "在 WeddingAI.video 搜索AI婚礼视频服务：修复、多语言配音、慢动作、预告片、致敬视频。",
    },
    "search.input_placeholder.e_g_slow_motion_multilingual_restoration.60220537": {
        "ar": "مثال: حركة بطيئة، متعدد اللغات، استعادة",
        "de": "z.B. Zeitlupe, mehrsprachig, Restaurierung",
        "es": "ej. cámara lenta, multilingüe, restauración",
        "fr": "ex. ralenti, multilingue, restauration",
        "ja": "例：スローモーション、多言語、復元",
        "pt": "ex. câmera lenta, multilíngue, restauração",
        "ru": "напр. замедленная съемка, многоязычный, реставрация",
        "th": "เช่น สโลว์โมชั่น หลายภาษา การฟื้นฟู",
    },
    # ── success ──
    "success.meta_description.your_quote_request_has_been_received_we.24769803": {
        "ar": "تم استلام طلب عرض السعر الخاص بك. سنرد خلال 24 ساعة بتوصية مخصصة وأسعار. WeddingAI.video",
        "de": "Ihre Angebotsanfrage ist eingegangen. Wir antworten innerhalb von 24 Stunden mit einer persönlichen Empfehlung und Preisangabe. WeddingAI.video",
        "es": "Su solicitud de presupuesto ha sido recibida. Le responderemos en 24 horas con una recomendación personalizada y precios. WeddingAI.video",
        "fr": "Votre demande de devis a bien été reçue. Nous vous répondrons sous 24 heures avec une recommandation personnalisée et un tarif. WeddingAI.video",
        "ja": "お見積もり依頼を受け付けました。24時間以内にパーソナライズされた提案と料金で返信します。WeddingAI.video",
        "pt": "Sua solicitação de orçamento foi recebida. Responderemos em 24 horas com uma recomendação personalizada e preços. WeddingAI.video",
        "ru": "Ваш запрос на смету получен. Мы ответим в течение 24 часов с персонализированной рекомендацией и ценой. WeddingAI.video",
        "th": "ได้รับคำขอใบเสนอราคาของคุณแล้ว เราจะตอบกลับภายใน 24 ชั่วโมงพร้อมคำแนะนำและราคาที่ปรับให้เหมาะกับคุณ WeddingAI.video",
        "zh": "您的报价请求已收到。我们会在24小时内回复个性化方案和报价。WeddingAI.video",
    },
    # ── terms ──
    "terms.meta_description.terms_of_service_for_weddingai_video_rea.52066086": {
        "ar": "شروط الخدمة لـ WeddingAI.video. اقرأ شروط الخدمة وسياسات الدفع والاتفاقيات القانونية قبل الطلب.",
        "de": "Nutzungsbedingungen für WeddingAI.video. Lesen Sie unsere Servicebedingungen, Zahlungsrichtlinien und rechtlichen Vereinbarungen vor der Bestellung.",
        "es": "Términos de servicio de WeddingAI.video. Lea nuestros términos de servicio, políticas de pago y acuerdos legales antes de ordenar.",
        "fr": "Conditions d'utilisation de WeddingAI.video. Lisez nos conditions de service, politiques de paiement et accords légaux avant de commander.",
        "ja": "WeddingAI.videoの利用規約。ご注文前にサービス条件、支払いポリシー、法的同意事項をお読みください。",
        "pt": "Termos de serviço do WeddingAI.video. Leia nossos termos de serviço, políticas de pagamento e acordos legais antes de fazer o pedido.",
        "ru": "Условия использования WeddingAI.video. Ознакомьтесь с нашими условиями обслуживания, политикой оплаты и юридическими соглашениями перед заказом.",
        "th": "ข้อกำหนดในการให้บริการของ WeddingAI.video อ่านเงื่อนไขการบริการ นโยบายการชำระเงิน และข้อตกลงทางกฎหมายก่อนสั่งซื้อ",
        "zh": "WeddingAI.video 服务条款。下单前请阅读我们的服务条款、付款政策和法律协议。",
    },
    # ── services index ──
    "services.meta_description.browse_all_weddingai_video_services_ai_f.77223006": {
        "ar": "تصفح جميع خدمات WeddingAI.video: أفلام بالذكاء الاصطناعي، فيديوهات زفاف للحيوانات الأليفة، دبلجة متعددة اللغات، رسوم متحركة. WeddingAI.video",
        "de": "Durchsuchen Sie alle WeddingAI.video-Dienste: KI-Filme, Haustier-Hochzeitsvideos, mehrsprachige Synchronisation, Animationen. WeddingAI.video",
        "es": "Explore todos los servicios de WeddingAI.video: películas con IA, videos de bodas con mascotas, doblaje multilingüe, animaciones. WeddingAI.video",
        "fr": "Parcourez tous les services WeddingAI.video : films IA, vidéos de mariage avec animaux, doublage multilingue, animations. WeddingAI.video",
        "ja": "すべてのWeddingAI.videoサービスを閲覧：AIフィルム、ペット結婚式ビデオ、多言語吹き替え、アニメーション。WeddingAI.video",
        "pt": "Navegue por todos os serviços WeddingAI.video: filmes com IA, vídeos de casamento com pets, dublagem multilíngue, animações. WeddingAI.video",
        "ru": "Просмотрите все услуги WeddingAI.video: ИИ-фильмы, свадебные видео с питомцами, многоязычный дубляж, анимация. WeddingAI.video",
        "zh": "浏览所有 WeddingAI.video 服务：AI影片、宠物婚礼视频、多语言配音、动画等。",
    },
    # ── services: vintage restoration ──
    "services.vintage_restoration.meta_description.restore_30_year_old_vhs_8mm_4k.91827364": {
        "ar": "استعد لقطات زفاف VHS و 8mm و Hi8 القديمة بدقة 4K. تصحيح ألوان بالذكاء الاصطناعي، تقليل ضوضاء الصوت. خدمة استعادة اللقطات القديمة.",
        "de": "Restaurieren Sie 30 Jahre alte VHS-, 8mm- und Hi8-Hochzeitsaufnahmen in 4K. KI-Farbkorrektur, Audio-Rauschunterdrückung. Vintage-Aufnahmen-Restaurierungsservice.",
        "es": "Restaure grabaciones de bodas VHS, 8mm y Hi8 de 30 años a 4K. Corrección de color con IA, reducción de ruido de audio. Servicio de restauración de material antiguo.",
        "fr": "Restaurez des séquences de mariage VHS, 8mm et Hi8 vieilles de 30 ans en 4K. Correction des couleurs par IA, débruitage audio. Service de restauration de séquences vintage.",
        "ja": "30年前のVHS、8mm、Hi8の結婚式映像を4Kに復元。AIカラー補正、オーディオノイズ除去。ビンテージ映像復元サービス。",
        "pt": "Restaure filmagens de casamento VHS, 8mm e Hi8 de 30 anos para 4K. Correção de cor com IA, redução de ruído de áudio. Serviço de restauração de filmagens vintage.",
        "ru": "Восстановите 30-летние свадебные записи VHS, 8mm и Hi8 до 4K. ИИ-коррекция цвета, шумоподавление звука. Услуга реставрации винтажных записей.",
        "th": "ฟื้นฟูฟุตเทจงานแต่งงาน VHS, 8mm และ Hi8 อายุ 30 ปีเป็น 4K แก้ไขสีด้วย AI ลดเสียงรบกวน บริการฟื้นฟูฟุตเทจวินเทจ",
        "zh": "将30年前的VHS、8mm和Hi8婚礼录像修复至4K。AI色彩校正、音频降噪。老视频修复服务。",
    },
    "services.vintage_restoration.title_text.vintage_footage_restoration.91827364": {
        "ar": "استعادة اللقطات القديمة — VHS إلى 4K، ألوان، صوت | WeddingAI.video",
        "fr": "Restauration de Séquences Vintage — VHS vers 4K, Couleur, Audio | WeddingAI.video",
        "pt": "Restauração de Filmagens Vintage — VHS para 4K, Cor, Áudio | WeddingAI.video",
        "ru": "Реставрация Винтажных Записей — VHS в 4K, Цвет, Звук | WeddingAI.video",
        "th": "การฟื้นฟูฟุตเทจวินเทจ — VHS เป็น 4K, สี, เสียง | WeddingAI.video",
        "zh": "老视频修复 — VHS转4K、色彩校正、音频降噪 | WeddingAI.video",
    },
    # ── services: wedding-trailer ──
    "services.personalization.wedding-trailer.meta_description.want_a_sneak_peek_of_your_wedding_we_cre.14152169": {
        "ar": "تريد نظرة خاطفة على زفافك؟ نصنع إعلانات تشويقية سينمائية من لقطاتك — مثالية لوسائل التواصل الاجتماعي والتشغيل في الحفل. WeddingAI.video",
        "fr": "Vous voulez un aperçu de votre mariage ? Nous créons des bandes-annonces cinématographiques à partir de vos séquences — parfait pour les réseaux sociaux et la diffusion à la réception. WeddingAI.video",
        "pt": "Quer uma prévia do seu casamento? Criamos trailers cinematográficos a partir de suas filmagens — perfeito para redes sociais e exibição na recepção. WeddingAI.video",
        "ru": "Хотите предпоказ вашей свадьбы? Мы создаем кинематографичные трейлеры из ваших записей — идеально для соцсетей и показа на приеме. WeddingAI.video",
        "zh": "想提前预览婚礼？我们用您的素材制作电影级预告片 — 适合社交媒体和婚宴播放。WeddingAI.video",
    },
    # ── services: meme-generator ──
    "services.personalization.meme-generator.meta_description.get_custom_wedding_gifs_memes_and_sharea.47941060": {
        "ar": "احصل على صور GIF وميمات ومقاطع قابلة للمشاركة مخصصة للزفاف — مثالية لوسائل التواصل الاجتماعي والدعوات وعروض الاستقبال.",
        "fr": "Obtenez des GIFs, mèmes et clips partageables personnalisés pour votre mariage — parfaits pour les réseaux sociaux, invitations et diaporamas de réception.",
        "pt": "Obtenha GIFs, memes e clipes compartilháveis personalizados para casamento — perfeitos para redes sociais, convites e slideshows de recepção.",
        "ru": "Получите персонализированные свадебные GIF, мемы и клипы для sharing — идеально для соцсетей, приглашений и слайд-шоу на приеме.",
        "th": "รับ GIF มีม และคลิปที่แชร์ได้สำหรับงานแต่งงานที่กำหนดเอง — เหมาะสำหรับโซเชียลมีเดีย การ์ดเชิญ และสไลด์โชว์ในงานเลี้ยง",
        "zh": "获取定制婚礼GIF、表情包和可分享短视频 — 适合社交媒体、请柬和婚宴幻灯片。",
    },
    # ── services: pet-wedding ──
    "services.personalization.pet-wedding.meta_description.your_pet_is_family_too_we_create_hilario.85690911": {
        "ar": "حيوانك الأليف من العائلة أيضاً. نصنع فيديوهات زفاف مضحكة ومؤثرة من بطولة صديقك الفروي. WeddingAI.video",
        "fr": "Votre animal fait aussi partie de la famille. Nous créons des vidéos de mariage hilarantes et touchantes mettant en vedette votre compagnon à quatre pattes. WeddingAI.video",
        "ja": "ペットも家族です。あなたの大切な毛むくじゃらの友達が主役の、面白くて心温まる結婚式ビデオを作成します。WeddingAI.video",
        "pt": "Seu pet também é família. Criamos vídeos de casamento hilários e emocionantes estrelando seu amigo peludo. WeddingAI.video",
        "ru": "Ваш питомец тоже семья. Мы создаем веселые, трогательные свадебные видео с вашим пушистым другом в главной роли. WeddingAI.video",
        "zh": "宠物也是家人。我们为您的毛孩子制作搞笑又温馨的婚礼视频。WeddingAI.video",
    },
    # ── services: family-tribute ──
    "services.absence-compensation.family-tribute.meta_description.keep_loved_ones_present_on_your_wedding.99204000": {
        "ar": "أبقِ أحباءك حاضرين في يوم زفافك. نصنع تكريمات محترمة من الصور والفيديوهات. WeddingAI.video",
        "fr": "Gardez vos proches présents le jour de votre mariage. Nous créons respectueusement des hommages à partir de photos et vidéos. WeddingAI.video",
        "pt": "Mantenha seus entes queridos presentes no dia do seu casamento. Criamos homenagens respeitosas a partir de fotos e vídeos. WeddingAI.video",
        "ru": "Сохраните присутствие близких в день вашей свадьбы. Мы с уважением создаем трибьюты из фотографий и видео. WeddingAI.video",
        "zh": "让亲人始终陪伴在您的婚礼上。我们用心制作来自照片和视频的致敬影片。WeddingAI.video",
    },
    # ── services: family-message ──
    "services.absence-compensation.family-message.meta_description.family_can_t_make_it_to_your_wedding_we.64375580": {
        "ar": "العائلة لا تستطيع الحضور إلى زفافك؟ نصور رسالتهم وندمجها في فيلم زفافك بسلاسة. WeddingAI.video",
        "fr": "Votre famille ne peut pas venir à votre mariage ? Nous filmons leur message et l'intégrons dans votre film de mariage en toute fluidité. WeddingAI.video",
        "pt": "Sua família não pode comparecer ao seu casamento? Filmamos a mensagem deles e a integramos ao seu filme de casamento perfeitamente. WeddingAI.video",
        "ru": "Семья не может приехать на вашу свадьбу? Мы снимаем их послание и плавно интегрируем его в ваш свадебный фильм. WeddingAI.video",
        "zh": "家人无法到场？我们拍摄他们的祝福并无缝融入您的婚礼影片。WeddingAI.video",
    },
    # ── services: celebrity-message ──
    "services.absence-compensation.celebrity-message.meta_description.want_a_celebrity_message_for_your_weddin.33535180": {
        "ar": "تريد رسالة من مشاهير لحفل زفافك؟ ينشئ الذكاء الاصطناعي لدينا رسائل فيديو مخصصة وواقعية وجذابة لحفل الاستقبال الخاص بك.",
        "de": "Wünschen Sie sich eine Promi-Nachricht für Ihre Hochzeit? Unsere KI erstellt personalisierte, realistische Videobotschaften für Ihren Empfang.",
        "es": "¿Quiere un mensaje de celebridad para su boda? Nuestra IA crea mensajes de video personalizados, realistas y atractivos para su recepción.",
        "fr": "Vous voulez un message de célébrité pour votre mariage ? Notre IA crée des messages vidéo personnalisés, réalistes et captivants pour votre réception.",
        "ja": "結婚式に有名人のメッセージが欲しい？私たちのAIが、披露宴用のパーソナライズされたリアルで魅力的なビデオメッセージを作成します。",
        "pt": "Quer uma mensagem de celebridade para o seu casamento? Nossa IA cria mensagens de vídeo personalizadas, realistas e envolventes para sua recepção.",
        "ru": "Хотите сообщение от знаменитости на свадьбу? Наш ИИ создает персонализированные, реалистичные, увлекательные видеообращения для вашего приема.",
        "zh": "想在婚礼上收到名人祝福？我们的AI为您生成个性化、逼真、引人入胜的视频祝福。",
    },
    # ── services: cartoon-style ──
    "services.personalization.cartoon-style.meta_description.transform_your_wedding_footage_into_a_be.34076488": {
        "ar": "حول لقطات زفافك إلى رسوم متحركة جميلة. أنماط جيبلي وبيكسار والأنمي والمزيد. فيديو زفاف فريد من نوعه.",
        "de": "Verwandeln Sie Ihre Hochzeitsaufnahmen in eine wunderschöne Animation. Ghibli-, Pixar-, Anime-Stile und mehr. Ein einzigartiges Hochzeitsvideo.",
        "es": "Transforme su metraje de boda en una hermosa animación. Estilos Ghibli, Pixar, anime y más. Un video de boda único en su tipo.",
        "fr": "Transformez vos séquences de mariage en une magnifique animation. Styles Ghibli, Pixar, anime et plus. Une vidéo de mariage unique en son genre.",
        "ja": "結婚式の映像を美しいアニメーションに変換。ジブリ、ピクサー、アニメスタイルなど。唯一無二の結婚式ビデオ。",
        "pt": "Transforme suas filmagens de casamento em uma bela animação. Estilos Ghibli, Pixar, anime e mais. Um vídeo de casamento único.",
        "ru": "Превратите ваши свадебные кадры в красивую анимацию. Стили Ghibli, Pixar, аниме и другие. Уникальное свадебное видео.",
        "zh": "将您的婚礼视频变成精美动画。吉卜力、皮克斯、动漫等多种风格。独一无二的婚礼视频。",
    },
    # ── services: ai-video-generator ──
    "services.personalization.ai-video-generator.meta_description.upload_your_photos_and_describe_your_dre.08145690": {
        "ar": "حمّل صورك ووصف فيديو زفاف أحلامك. يولد الذكاء الاصطناعي لدينا فيلماً سينمائياً من صورك وإرشاداتك.",
        "de": "Laden Sie Ihre Fotos hoch und beschreiben Sie Ihr Traumhochzeitsvideo. Unsere KI generiert einen filmischen Film aus Ihren Fotos und Anweisungen.",
        "es": "Suba sus fotos y describa el video de bodas de sus sueños. Nuestra IA genera una película cinematográfica a partir de sus fotos e indicaciones.",
        "fr": "Téléchargez vos photos et décrivez la vidéo de mariage de vos rêves. Notre IA génère un film cinématographique à partir de vos photos et instructions.",
        "ja": "写真をアップロードして、夢の結婚式ビデオを説明してください。私たちのAIがあなたの写真と指示からシネマティックな映画を生成します。",
        "pt": "Envie suas fotos e descreva o vídeo de casamento dos seus sonhos. Nossa IA gera um filme cinematográfico a partir de suas fotos e instruções.",
        "ru": "Загрузите свои фотографии и опишите видео свадьбы вашей мечты. Наш ИИ генерирует кинематографичный фильм из ваших фото и указаний.",
        "zh": "上传您的照片，描述您梦想中的婚礼视频。我们的AI根据您的照片和指引生成电影级影片。",
    },
    # ── services: multilingual ──
    "services.personalization.multilingual.meta_description.share_your_wedding_video_with_family_wor.43249185": {
        "ar": "شارك فيديو زفافك مع العائلة حول العالم. تعليقات صوتية وترجمات بالذكاء الاصطناعي بـ 23 لغة. مثالي للعائلات الدولية.",
        "de": "Teilen Sie Ihr Hochzeitsvideo mit der Familie weltweit. KI-Sprachausgabe und Untertitel in 23 Sprachen. Perfekt für internationale Familien.",
        "es": "Comparta su video de bodas con familiares en todo el mundo. Voces en off y subtítulos con IA en 23 idiomas. Perfecto para familias internacionales.",
        "fr": "Partagez votre vidéo de mariage avec votre famille dans le monde entier. Voix off et sous-titres IA en 23 langues. Parfait pour les familles internationales.",
        "ja": "結婚式のビデオを世界中の家族と共有。23言語のAIナレーションと字幕。国際的な家族に最適。",
        "pt": "Compartilhe seu vídeo de casamento com familiares em todo o mundo. Narração e legendas com IA em 23 idiomas. Perfeito para famílias internacionais.",
        "ru": "Поделитесь свадебным видео с семьей по всему миру. Озвучка и субтитры с ИИ на 23 языках. Идеально для международных семей.",
        "zh": "与全球家人分享您的婚礼视频。23种语言的AI配音和字幕。跨国婚礼的理想之选。",
    },
    # ── services: slow-motion ──
    "services.video-enhancement.slow-motion.meta_description.smooth_natural_slow_motion_for_your_wedd.04498835": {
        "ar": "حركة بطيئة سلسة وطبيعية لفيديو زفافك. يضيف استكمال الإطارات بالذكاء الاصطناعي لدينا لقطات بين الإطارات الحقيقية — بدون اهتزاز، بدون تمزق.",
        "de": "Sanfte, natürliche Zeitlupe für Ihr Hochzeitsvideo. Unsere KI-Bildinterpolation fügt Frames zwischen echten Frames ein — kein Ruckeln, kein Zerreißen.",
        "es": "Cámara lenta suave y natural para su video de bodas. Nuestra interpolación de fotogramas con IA agrega fotogramas entre los reales — sin tartamudeo, sin desgarros.",
        "fr": "Ralenti fluide et naturel pour votre vidéo de mariage. Notre interpolation d'images IA ajoute des images entre les images réelles — sans saccades, sans déchirures.",
        "ja": "結婚式ビデオの滑らかで自然なスローモーション。AIフレーム補間が実際のフレーム間にフレームを追加 — カクつきなし、破綻なし。",
        "pt": "Câmera lenta suave e natural para o seu vídeo de casamento. Nossa interpolação de quadros com IA adiciona quadros entre os reais — sem travamentos, sem rasgos.",
        "ru": "Плавное, естественное замедление для вашего свадебного видео. Наша ИИ-интерполяция кадров добавляет кадры между реальными — без рывков, без разрывов.",
        "zh": "为您的婚礼视频呈现流畅自然的慢动作效果。我们的AI帧插值技术在真实帧之间补充画面 — 无卡顿，无撕裂。",
    },
}

# Index page FAQ translations (shared across all non-EN languages)
INDEX_FAQ = {
    "index.p_text.ai_safety_answer.99999992": {
        "th": "เราใช้โมเดล AI ระดับเชิงพาณิชย์พร้อมระบบป้องกันความปลอดภัย ผู้สร้างภาพยนตร์มืออาชีพตรวจสอบทุกโปรเจกต์ และเราไม่ใช้ AI เพื่อเปลี่ยนแปลงลักษณะใบหน้าหรือรูปร่างโดยไม่ได้รับความยินยอมอย่างชัดแจ้ง",
        "zh": "我们使用商业级AI模型并配备安全防护。每个项目都由专业电影制作人审查，未经明确同意，我们不会使用AI修改面部特征或体型。",
    },
    "index.p_text.footage_privacy_answer.99999991": {
        "th": "ฟุตเทจของคุณถูกจัดเก็บแบบเข้ารหัสบนเซิร์ฟเวอร์ที่ปลอดภัยในสหรัฐอเมริกา ไฟล์จะถูกลบโดยอัตโนมัติ 30 วันหลังจากการส่งมอบโครงการ เว้นแต่คุณจะขอการจัดเก็บถาวร",
        "zh": "您的视频素材加密存储在美国安全服务器上。项目交付30天后文件自动删除，除非您申请存档保存。",
    },
    "index.p_text.ownership_answer.99999993": {
        "th": "คุณเป็นเจ้าของวิดีโอสุดท้าย เราคงสิทธิ์การใช้งานแบบไม่ผูกขาดเพื่อใช้ตัวอย่างที่ไม่ระบุตัวตนในพอร์ตโฟลิโอของเรา (คุณสามารถยกเลิกได้ตลอดเวลา) คุณมีอิสระในการใช้วิดีโอของคุณในเชิงพาณิชย์",
        "zh": "您拥有最终成片的所有权。我们保留在作品集中使用匿名片段的非独占许可（您可随时选择退出）。您可以自由将视频用于商业用途。",
    },
    "index.p_text.rush_delivery_answer.99999994": {
        "th": "ได้ บริการส่วนใหญ่มีบริการจัดส่งด่วน 48 ชั่วโมงโดยมีค่าธรรมเนียมเพิ่มเติม 30-50% ขึ้นอยู่กับความซับซ้อนของโครงการ",
        "zh": "是的。大多数服务提供48小时加急交付，根据项目复杂度收取30-50%的附加费用。",
    },
    "index.p_text.bundle_pricing_answer.99999995": {
        "th": "ส่วนลดแพ็คเกจเมื่อคุณจอง 2 บริการขึ้นไปในโครงการเดียวกัน: ลด 10% สำหรับ 2 บริการ, ลด 15% สำหรับ 3 บริการ, และลด 20% สำหรับ 4 บริการขึ้นไป",
        "zh": "同一项目预订2项及以上服务可享套餐折扣：2项9折，3项85折，4项及以上8折。",
    },
    "index.summary_text.do_you_offer_rush_delivery.99999994": {
        "th": "มีบริการจัดส่งด่วนไหม?",
        "zh": "你们提供加急服务吗？",
    },
    "index.summary_text.how_do_you_handle_my_personal_footage.99999991": {
        "th": "คุณจัดการฟุตเทจส่วนตัวและความเป็นส่วนตัวของฉันอย่างไร?",
        "zh": "你们如何处理我的个人视频素材和隐私？",
    },
    "index.summary_text.how_does_pricing_work.99999995": {
        "th": "ราคาสำหรับหลายบริการทำงานอย่างไร?",
        "zh": "多项服务的价格怎么算？",
    },
    "index.summary_text.what_about_ai_safety_and_bias.99999992": {
        "th": "แล้วความปลอดภัยและอคติของ AI ในการประมวลผลล่ะ?",
        "zh": "AI处理过程中的安全和偏见问题怎么保障？",
    },
    "index.summary_text.who_owns_the_final_video.99999993": {
        "th": "ใครเป็นเจ้าของวิดีโอสุดท้ายและฉันสามารถใช้ในเชิงพาณิชย์ได้ไหม?",
        "zh": "ใครเป็นเจ้าของวิดีโอสุดท้ายและฉันสามารถใช้ในเชิงพาณิชย์ได้ไหม?",
    },
    # index service description cards (zh & th)
    "index.p_text.pet_wedding_video.22222226": {
        "th": "นำแสดงโดยสัตว์เลี้ยงของคุณ! เปิดตัวอย่างสนุกหรือการ์ด save-the-date",
        "zh": "宠物主演！有趣的片头或婚礼预告。",
    },
    "index.p_text.cinematic_1_to_3_minute_trailer.22222225": {
        "th": "ตัวอย่างภาพยนตร์ 1-3 นาทีสำหรับโซเชียลและการฉายในงานเลี้ยง",
        "zh": "1-3分钟电影级预告片，适合社交媒体和婚宴播放。",
    },
    "index.p_text.shareable_gifs_and_memes.22222229": {
        "th": "GIF และมีม 10 แบบที่แชร์ได้สำหรับโซเชียลมีเดีย",
        "zh": "10个可分享的GIF动图和表情包，专为社交媒体打造。",
    },
    "index.p_text.ghibli_pixar_anime_style.22222228": {
        "th": "สไตล์ Ghibli, Pixar หรืออะนิเมะที่นำไปใช้กับฟุตเทจของคุณ",
        "zh": "吉卜力、皮克斯或动漫风格应用到您的视频中。",
    },
    "index.p_text.23_languages_dubbing.22222227": {
        "th": "23 ภาษา — การพากย์และคำบรรยายด้วย AI สำหรับครอบครัวนานาชาติ",
        "zh": "23种语言 — AI配音和字幕，让跨国亲友都能理解。",
    },
    "index.p_text.recover_30_year_old_tapes_8mm_to_4k.91827364": {
        "th": "กู้คืนเทป VHS อายุ 30 ปี อัปสเกล 8mm เป็น 4K แก้ไขสีและลดเสียงรบกวน งานแต่งงานของพ่อแม่คุณ ฟื้นฟูใหม่",
        "zh": "修复30年前的VHS录像带，将8mm升级至4K，色彩校正和音频降噪。让父母的婚礼重获新生。",
    },
    "index.p_text.turn_photos_into_cinematic_film.22222224": {
        "th": "เปลี่ยนภาพถ่ายงานแต่งงานของคุณให้เป็นภาพยนตร์ที่สร้างโดย AI แบบภาพยนตร์",
        "zh": "将您的婚礼照片变成电影级AI生成影片。",
    },
    "index.p_text.remote_family_video_message.22222222": {
        "th": "ครอบครัวที่อยู่ห่างไกลบันทึกข้อความและเราแทรกลงในภาพยนตร์ของคุณอย่างแนบเนียน",
        "zh": "远程亲友录制祝福，我们将其无缝嵌入您的婚礼影片。",
    },
    "index.p_text.tribute_for_a_deceased_loved_one.22222221": {
        "th": "ให้เกียรติผู้เป็นที่รักที่ล่วงลับด้วยวิดีโออนุสรณ์ที่สวยงาม",
        "zh": "为已故亲人制作精美的纪念视频蒙太奇。",
    },
    "index.p_text.ai_archetype_wedding_message.22222223": {
        "th": "ข้อความสไตล์คนดังที่สร้างโดย AI น่าประหลาดใจ ถูกกฎหมาย มีจริยธรรม",
        "zh": "AI生成的名人风格祝福。惊喜、合法、合乎道德。",
    },
}

# Vintage restoration page content (zh & th)
VINTAGE_RESTORATION = {
    "services.vintage_restoration.h1_text.restore_your_30_year_old_wedding.91827364": {
        "th": "ฟื้นฟูความทรงจำงานแต่งงานอายุ 30 ปีของคุณ",
        "zh": "修复您30年前的婚礼记忆",
    },
    "services.vintage_restoration.h2_text.how_it_works.91827364": {
        "th": "วิธีการทำงาน",
        "zh": "工作原理",
    },
    "services.vintage_restoration.h2_text.what_we_accept.91827364": {
        "th": "สิ่งที่เรารับ",
        "zh": "我们接受的格式",
    },
    "services.vintage_restoration.h2_text.why_this_matters.91827364": {
        "th": "ทำไมสิ่งนี้ถึงสำคัญ",
        "zh": "为什么这很重要",
    },
    "services.vintage_restoration.h3_text.accept_digital.91827364": {
        "th": "ไฟล์ดิจิทัล",
        "zh": "数字文件",
    },
    "services.vintage_restoration.h3_text.accept_film.91827364": {
        "th": "ฟิล์มรีล",
        "zh": "胶片卷",
    },
    "services.vintage_restoration.h3_text.accept_tape.91827364": {
        "th": "วิดีโอเทป",
        "zh": "录像带",
    },
    "services.vintage_restoration.h3_text.step_1_send.91827364": {
        "th": "ส่งฟุตเทจของคุณมาให้เรา",
        "zh": "发送您的录像素材",
    },
    "services.vintage_restoration.h3_text.step_2_diagnose.91827364": {
        "th": "การวินิจฉัยและใบเสนอราคาฟรี",
        "zh": "免费诊断和报价",
    },
    "services.vintage_restoration.h3_text.step_3_restore.91827364": {
        "th": "การฟื้นฟูและจัดส่งด้วย AI",
        "zh": "AI修复和交付",
    },
    "services.vintage_restoration.p_text.ai_powered_restoration.91827364": {
        "th": "การฟื้นฟูด้วย AI: แปลง VHS/8mm เป็นดิจิทัล อัปสเกลเป็น 4K แก้ไขสี ลดเสียงรบกวน งานแต่งงานของพ่อแม่คุณ ฟื้นฟูใหม่สำหรับคนรุ่นต่อไป",
        "zh": "AI驱动修复：将VHS/8mm数字化，升级至4K，修复色彩，降噪音频。让父母的婚礼为下一代重焕新生。",
    },
    "services.vintage_restoration.p_text.how_it_works_intro.91827364": {
        "th": "สามขั้นตอน ไม่จำเป็นต้องมีความรู้ทางเทคนิค",
        "zh": "三步完成。无需任何技术知识。",
    },
    "services.vintage_restoration.p_text.what_we_accept_intro.91827364": {
        "th": "เทป ฟิล์ม และดิจิทัล — เราจัดการทั้งหมด",
        "zh": "录像带、胶片和数字文件 — 我们全都能处理。",
    },
    "services.vintage_restoration.p_text.why_this_matters_intro.91827364": {
        "th": "วิดีโองานแต่งงานของพ่อแม่คุณ ฟิล์ม 8mm ของปู่ย่าตายาย เทป VHS ที่คุณตั้งใจจะแปลงเป็นดิจิทัลมาหลายปี — สิ่งเหล่านี้ไม่ใช่แค่การบันทึก แต่มันคือมรดกทางภาพของครอบครัวคุณ",
        "zh": "父母的婚礼录像、祖父母的8mm胶片、那盒你一直想数字化多年的VHS录像带 — 这些不仅仅是录像。它们是你家族的视觉传承。",
    },
    "services.vintage_restoration.p_text.why_this_matters_outro.91827364": {
        "th": "ทุกปี เทป VHS อีก 10% ไม่สามารถเล่นได้เนื่องจากการเสื่อมสภาพของเทปแม่เหล็ก อย่าปล่อยให้ความทรงจำของครอบครัวคุณหายไป",
        "zh": "每年，又有10%的VHS录像带因磁性衰减而无法播放。别让你的家庭记忆消失。",
    },
    "services.vintage_restoration.p_text.step_1_send_desc.91827364": {
        "th": "อัปโหลดไฟล์ดิจิทัลผ่านพอร์ทัลที่ปลอดภัยของเรา หรือส่งเทปหรือฟิล์มรีลมายังห้องปฏิบัติการของเรา เราครอบคลุมค่าจัดส่งสำหรับคำสั่งซื้อมากกว่า $200",
        "zh": "通过我们安全的门户上传数字文件，或将实体录像带或胶片寄到我们实验室。订单超过$200我们承担运费。",
    },
    "services.vintage_restoration.p_text.step_2_diagnose_desc.91827364": {
        "th": "ทีมงานของเราตรวจสอบฟุตเทจของคุณ ระบุความเสียหาย และส่งใบเสนอราคาที่ไม่มีข้อผูกมัดทางอีเมลภายใน 48 ชั่วโมง ไม่ต้องชำระเงินล่วงหน้า",
        "zh": "我们的团队检查您的素材、识别损坏部位，并在48小时内通过邮件发送无义务报价。无需预付。",
    },
    "services.vintage_restoration.p_text.step_3_restore_desc.91827364": {
        "th": "เราฟื้นฟูฟุตเทจของคุณตามแพ็คเกจที่คุณเลือก คุณจะได้รับลิงก์ตรวจสอบพร้อมลายน้ำส่วนตัว หลังจากอนุมัติ เราจัดส่งไฟล์สุดท้าย มีบริการจัดส่งด่วน",
        "zh": "我们按您选择的套餐修复素材。您会收到带水印的私密审查链接。批准后，我们交付最终文件。支持加急交付。",
    },
    "services.vintage_restoration.summary_text.damaged_tape_recovery.91827364": {
        "th": "เทปของฉันเสียหายมากจนเล่นไม่ได้ คุณยังสามารถกู้คืนได้ไหม?",
        "zh": "我的录像带损坏严重无法播放，你们还能修复吗？",
    },
    "services.vintage_restoration.p_text.damaged_tape_recovery_answer.91827364": {
        "th": "ในกรณีส่วนใหญ่ ได้ ทีมงานของเราใช้ VCR มืออาชีพพร้อม TBC ในตัว (การแก้ไขฐานเวลา) และสามารถต่อเทปที่ขาดได้ แม้แต่เทปที่มีเชื้อราก็มักจะสามารถทำความสะอาดและแปลงเป็นดิจิทัลได้ อัตราความสำเร็จ: ~95% สำหรับเทป VHS",
        "zh": "大多数情况下可以。我们使用带内置TBC（时基校正）的专业VCR，可以拼接断裂的录像带。即使发霉的录像带通常也能清理并数字化。成功率：VHS录像带约95%。",
    },
    "services.vintage_restoration.summary_text.upscaling_4k_quality.91827364": {
        "th": "การอัปสเกลเป็น 4K จะทำให้ฟุตเทจเก่าดูปลอมไหม?",
        "zh": "升级到4K会让我的老视频看起来假吗？",
    },
    "services.vintage_restoration.p_text.upscaling_4k_quality_answer.91827364": {
        "th": "ไม่ อัปสเกลเลอร์ AI ของเราถูกฝึกมาโดยเฉพาะกับฟุตเทจงานแต่งงานที่เก็บถาวร มันเพิ่มรายละเอียดที่สมจริงโดยไม่มีลักษณะ 'พลาสติก' ของอัปสเกลเลอร์ทั่วไป การแก้ไขสีรักษาความรู้สึกอบอุ่นและคิดถึงของฟุตเทจดั้งเดิมของคุณ",
        "zh": "不会。我们的AI升频器专门针对存档婚礼素材训练。它能添加真实细节，而不会像通用升频器那样产生'塑料感'。色彩校正保留原素材温暖怀旧的感觉。",
    },
    "services.vintage_restoration.summary_text.what_tape_formats_accepted.91827364": {
        "th": "คุณรับเทปและฟิล์มรูปแบบใดบ้าง?",
        "zh": "你们接受哪些录像带和胶片格式？",
    },
    "services.vintage_restoration.p_text.what_tape_formats_accepted_answer.91827364": {
        "th": "เรารับ VHS, S-VHS, VHS-C, Hi8, Digital8, MiniDV, Betamax, MiniDVD, ฟิล์ม 8mm, Super 8, และฟิล์ม 16mm หากคุณมีรูปแบบที่ไม่ได้ระบุไว้ที่นี่ ติดต่อเรา — เราน่าจะจัดการได้",
        "zh": "我们接受VHS、S-VHS、VHS-C、Hi8、Digital8、MiniDV、Betamax、MiniDVD、8mm胶片、Super 8和16mm胶片。如有未列出的格式，请联系我们 — 大概率也能处理。",
    },
    "services.vintage_restoration.p_text.accept_digital_desc.91827364": {
        "th": "MP4, MOV, AVI, MKV, MPG, WebM — ความละเอียดใดก็ได้ตั้งแต่ 144p ถึง 4K เรายังรับดีวีดีและบลูเรย์ที่ริปแล้ว",
        "zh": "MP4、MOV、AVI、MKV、MPG、WebM — 从144p到4K的任何分辨率。我们还接受DVD和蓝光翻录文件。",
    },
    "services.vintage_restoration.p_text.accept_film_desc.91827364": {
        "th": "ฟิล์ม 8mm, Super 8, และ 16mm เราทำงานร่วมกับห้องปฏิบัติการพันธมิตรสำหรับการสแกนฟิล์มจริง (รวมอยู่ในราคา)",
        "zh": "8mm、Super 8和16mm胶片。我们与合作伙伴实验室合作进行实体胶片扫描（包含在价格中）。",
    },
    "services.vintage_restoration.p_text.accept_tape_desc.91827364": {
        "th": "VHS, S-VHS, VHS-C, Hi8, Digital8, MiniDV, Betamax, MiniDVD แม้แต่เทปที่เล่นไม่ได้อีกต่อไป — เครื่องมือกู้คืนทางนิติวิทยาศาสตร์ของเรามักจะสามารถดึงสัญญาณวิดีโอออกมาได้",
        "zh": "VHS、S-VHS、VHS-C、Hi8、Digital8、MiniDV、Betamax、MiniDVD。即使无法播放的录像带 — 我们的取证恢复工具通常也能提取视频信号。",
    },
}


def main():
    print("=" * 70)
    print("WeddingAI.video — i18n Translation (key-based)")
    print("=" * 70)

    with open(I18N_DIR / "en.json", encoding="utf-8") as f:
        en_data = json.load(f)

    # Merge all translation dicts
    all_translations = {}
    for source_dict in [KEY_TRANSLATIONS, INDEX_FAQ, VINTAGE_RESTORATION]:
        for key, langs in source_dict.items():
            if key not in all_translations:
                all_translations[key] = {}
            all_translations[key].update(langs)

    total_translated = 0

    all_langs = {l for d in all_translations.values() for l in d}
    for lang in sorted(all_langs):
        json_path = I18N_DIR / f"{lang}.json"
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        count = 0
        for key, en_val in en_data.items():
            if key not in data:
                continue
            translations_for_key = all_translations.get(key, {})
            if lang in translations_for_key:
                if data[key] == en_val:  # only replace if still English fallback
                    data[key] = translations_for_key[lang]
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

    print(f"\n  Total translated this run: {total_translated}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
