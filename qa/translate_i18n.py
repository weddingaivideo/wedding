"""
Translate all English fallback values in non-English language JSON files
to their respective target languages.

Usage: python qa/translate_i18n.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
I18N_DIR = ROOT / "i18n"

# Translation dictionary: {lang: {english_text: translated_text}}
# Only include texts that need translation (where JSON value == en.json value)

TRANSLATIONS = {
    "ar": {
        # 404
        "The page you were looking for doesn't exist. Browse our wedding video services or return home. WeddingAI.video": "الصفحة التي كنت تبحث عنها غير موجودة. تصفح خدمات فيديو الزفاف لدينا أو عد إلى الصفحة الرئيسية. WeddingAI.video",
        "order@weddingai.video": "order@weddingai.video",
        "Vintage Restoration": "استعادة الفيديو القديم",
        # about
        "Filmmakers and AI engineers building AI-powered wedding video services. Meet the team behind WeddingAI.video.": "صانعو أفلام ومهندسو ذكاء اصطناعي يبنون خدمات فيديو زفاف مدعومة بالذكاء الاصطناعي. تعرف على فريق WeddingAI.video.",
        "About Us | Filmmakers + AI Engineers | WeddingAI.video": "من نحن | صانعو أفلام + مهندسو ذكاء اصطناعي | WeddingAI.video",
        "★ Trustpilot": "★ Trustpilot",
        # blog
        "50 in-depth articles on wedding video restoration, AI editing, slow motion, family tributes — for couples and families. WeddingAI.video": "50 مقالاً متعمقاً حول استعادة فيديو الزفاف، التحرير بالذكاء الاصطناعي، الحركة البطيئة، تكريم العائلة — للأزواج والعائلات. WeddingAI.video",
        # cart
        "Review and customize your wedding video services — one-click checkout for packages and add-ons.": "راجع وخصص خدمات فيديو الزفاف الخاصة بك — دفع بنقرة واحدة للباقات والإضافات.",
        # gallery
        "View before-and-after examples of AI wedding video restoration, slow motion, multilingual dubbing, and more.": "شاهد أمثلة قبل وبعد لاستعادة فيديو الزفاف بالذكاء الاصطناعي، الحركة البطيئة، الدبلجة متعددة اللغات، والمزيد.",
        # index
        "Read more verified reviews on Trustpilot →": "اقرأ المزيد من التقييمات الموثقة على Trustpilot ←",
        # order
        "e.g., Sarah Johnson": "مثال: سارة جونسون",
        "e.g., sarah@example.com": "مثال: sarah@example.com",
        "https://drive.google.com/...": "https://drive.google.com/...",
        "Describe your vision, the current state of your footage (tape format, condition, length), and any specific requests.": "صف رؤيتك، الحالة الحالية للقطات (تنسيق الشريط، الحالة، المدة)، وأي طلبات محددة.",
        "Get a free, no-obligation quote. Share your vision — we'll reply with a personalized recommendation and pricing within 24 hours.": "احصل على عرض سعر مجاني بدون التزام. شارك رؤيتك — سنرد بتوصية مخصصة وأسعار خلال 24 ساعة.",
        # pricing
        "Simple, transparent pricing for AI wedding video services. No hidden fees. Packages start at $79. WeddingAI.video": "أسعار بسيطة وشفافة لخدمات فيديو الزفاف بالذكاء الاصطناعي. لا رسوم مخفية. الباقات تبدأ من $79. WeddingAI.video",
        # resources
        "In-depth wedding video guides: choose a videographer, AI wedding films, restore old tapes, multilingual dubbing, and more.": "أدلة فيديو زفاف متعمقة: اختر مصور فيديو، أفلام زفاف بالذكاء الاصطناعي، استعادة الأشرطة القديمة، الدبلجة متعددة اللغات، والمزيد.",
        # search
        "Search WeddingAI.video for AI wedding video services: restoration, multilingual dubbing, slow motion, trailers, tributes.": "ابحث في WeddingAI.video عن خدمات فيديو الزفاف بالذكاء الاصطناعي: الاستعادة، الدبلجة متعددة اللغات، الحركة البطيئة، الإعلانات التشويقية، التكريم.",
        "e.g., slow motion, multilingual, restoration": "مثال: حركة بطيئة، متعدد اللغات، استعادة",
        # success
        "Your quote request has been received. We will reply within 24 hours with a personalized recommendation and pricing. WeddingAI.video": "تم استلام طلب عرض السعر الخاص بك. سنرد خلال 24 ساعة بتوصية مخصصة وأسعار. WeddingAI.video",
        # terms
        "Terms of service for WeddingAI.video. Read our service terms, payment policies, and legal agreements before ordering.": "شروط الخدمة لـ WeddingAI.video. اقرأ شروط الخدمة وسياسات الدفع والاتفاقيات القانونية قبل الطلب.",
        # services - vintage_restoration
        "Restore 30-year-old VHS, 8mm, and Hi8 wedding footage to 4K. AI color correction, audio denoising. Vintage footage restoration service.": "استعد لقطات زفاف VHS و 8mm و Hi8 القديمة بدقة 4K. تصحيح ألوان بالذكاء الاصطناعي، تقليل ضوضاء الصوت. خدمة استعادة اللقطات القديمة.",
        "Vintage Footage Restoration — VHS to 4K, Color, Audio | WeddingAI.video": "استعادة اللقطات القديمة — VHS إلى 4K، ألوان، صوت | WeddingAI.video",
        # services - personalization
        "Get custom wedding GIFs, memes, and shareable clips — perfect for social media, invites, and reception slideshows.": "احصل على صور GIF وميمات ومقاطع قابلة للمشاركة مخصصة للزفاف — مثالية لوسائل التواصل الاجتماعي والدعوات وعروض الاستقبال.",
        "Want a sneak peek of your wedding? We create cinematic trailers from your footage — perfect for social media and reception play. WeddingAI.video": "تريد نظرة خاطفة على زفافك؟ نصنع إعلانات تشويقية سينمائية من لقطاتك — مثالية لوسائل التواصل الاجتماعي والتشغيل في الحفل. WeddingAI.video",
        "Your pet is family too. We create hilarious, heartwarming wedding videos starring your furry friend. WeddingAI.video": "حيوانك الأليف من العائلة أيضاً. نصنع فيديوهات زفاف مضحكة ومؤثرة من بطولة صديقك الفروي. WeddingAI.video",
        # services - absence-compensation
        "Keep loved ones present on your wedding day. We respectfully create tributes from photos and videos. WeddingAI.video": "أبقِ أحباءك حاضرين في يوم زفافك. نصنع تكريمات محترمة من الصور والفيديوهات. WeddingAI.video",
        "Family can't make it to your wedding? We film their message and integrate it into your wedding film seamlessly. WeddingAI.video": "العائلة لا تستطيع الحضور إلى زفافك؟ نصور رسالتهم وندمجها في فيلم زفافك بسلاسة. WeddingAI.video",
    },
    "de": {
        "e.g., Sarah Johnson": "z.B. Sarah Johnson",
        "e.g., sarah@example.com": "z.B. sarah@example.com",
        "https://drive.google.com/...": "https://drive.google.com/...",
        "Describe your vision, the current state of your footage (tape format, condition, length), and any specific requests.": "Beschreiben Sie Ihre Vision, den aktuellen Zustand Ihres Materials (Bandformat, Zustand, Länge) und spezifische Wünsche.",
        "Get a free, no-obligation quote. Share your vision — we'll reply with a personalized recommendation and pricing within 24 hours.": "Erhalten Sie ein kostenloses, unverbindliches Angebot. Teilen Sie Ihre Vision — wir antworten innerhalb von 24 Stunden mit einer persönlichen Empfehlung und Preisangabe.",
        "Simple, transparent pricing for AI wedding video services. No hidden fees. Packages start at $79. WeddingAI.video": "Einfache, transparente Preise für KI-Hochzeitsvideo-Dienste. Keine versteckten Gebühren. Pakete ab $79. WeddingAI.video",
        "Search WeddingAI.video for AI wedding video services: restoration, multilingual dubbing, slow motion, trailers, tributes.": "Durchsuchen Sie WeddingAI.video nach KI-Hochzeitsvideo-Diensten: Restaurierung, mehrsprachige Synchronisation, Zeitlupe, Trailer, Ehrungen.",
        "e.g., slow motion, multilingual, restoration": "z.B. Zeitlupe, mehrsprachig, Restaurierung",
        "Your quote request has been received. We will reply within 24 hours with a personalized recommendation and pricing. WeddingAI.video": "Ihre Angebotsanfrage ist eingegangen. Wir antworten innerhalb von 24 Stunden mit einer persönlichen Empfehlung und Preisangabe. WeddingAI.video",
        "Terms of service for WeddingAI.video. Read our service terms, payment policies, and legal agreements before ordering.": "Nutzungsbedingungen für WeddingAI.video. Lesen Sie unsere Servicebedingungen, Zahlungsrichtlinien und rechtlichen Vereinbarungen vor der Bestellung.",
        "Restore 30-year-old VHS, 8mm, and Hi8 wedding footage to 4K. AI color correction, audio denoising. Vintage footage restoration service.": "Restaurieren Sie 30 Jahre alte VHS-, 8mm- und Hi8-Hochzeitsaufnahmen in 4K. KI-Farbkorrektur, Audio-Rauschunterdrückung. Vintage-Aufnahmen-Restaurierungsservice.",
    },
    "es": {
        "50 in-depth articles on wedding video restoration, AI editing, slow motion, family tributes — for couples and families. WeddingAI.video": "50 artículos detallados sobre restauración de video de bodas, edición con IA, cámara lenta, homenajes familiares — para parejas y familias. WeddingAI.video",
        "e.g., Sarah Johnson": "ej. Sarah Johnson",
        "e.g., sarah@example.com": "ej. sarah@example.com",
        "https://drive.google.com/...": "https://drive.google.com/...",
        "Describe your vision, the current state of your footage (tape format, condition, length), and any specific requests.": "Describa su visión, el estado actual de su material (formato de cinta, condición, duración) y cualquier solicitud específica.",
        "Get a free, no-obligation quote. Share your vision — we'll reply with a personalized recommendation and pricing within 24 hours.": "Obtenga un presupuesto gratuito y sin compromiso. Comparta su visión — le responderemos con una recomendación personalizada y precios en 24 horas.",
        "Simple, transparent pricing for AI wedding video services. No hidden fees. Packages start at $79. WeddingAI.video": "Precios simples y transparentes para servicios de video de bodas con IA. Sin cargos ocultos. Paquetes desde $79. WeddingAI.video",
        "Search WeddingAI.video for AI wedding video services: restoration, multilingual dubbing, slow motion, trailers, tributes.": "Busque en WeddingAI.video servicios de video de bodas con IA: restauración, doblaje multilingüe, cámara lenta, tráileres, homenajes.",
        "e.g., slow motion, multilingual, restoration": "ej. cámara lenta, multilingüe, restauración",
        "Your quote request has been received. We will reply within 24 hours with a personalized recommendation and pricing. WeddingAI.video": "Su solicitud de presupuesto ha sido recibida. Le responderemos en 24 horas con una recomendación personalizada y precios. WeddingAI.video",
        "Terms of service for WeddingAI.video. Read our service terms, payment policies, and legal agreements before ordering.": "Términos de servicio de WeddingAI.video. Lea nuestros términos de servicio, políticas de pago y acuerdos legales antes de ordenar.",
        "Restore 30-year-old VHS, 8mm, and Hi8 wedding footage to 4K. AI color correction, audio denoising. Vintage footage restoration service.": "Restaure grabaciones de bodas VHS, 8mm y Hi8 de 30 años a 4K. Corrección de color con IA, reducción de ruido de audio. Servicio de restauración de material antiguo.",
    },
    "fr": {
        "The page you were looking for doesn't exist. Browse our wedding video services or return home. WeddingAI.video": "La page que vous recherchez n'existe pas. Parcourez nos services de vidéo de mariage ou retournez à l'accueil. WeddingAI.video",
        "order@weddingai.video": "order@weddingai.video",
        "Vintage Restoration": "Restauration Vintage",
        "Filmmakers and AI engineers building AI-powered wedding video services. Meet the team behind WeddingAI.video.": "Cinéastes et ingénieurs IA créant des services de vidéo de mariage alimentés par l'IA. Découvrez l'équipe derrière WeddingAI.video.",
        "About Us | Filmmakers + AI Engineers | WeddingAI.video": "À propos | Cinéastes + Ingénieurs IA | WeddingAI.video",
        "★ Trustpilot": "★ Trustpilot",
        "50 in-depth articles on wedding video restoration, AI editing, slow motion, family tributes — for couples and families. WeddingAI.video": "50 articles approfondis sur la restauration de vidéos de mariage, l'édition IA, le ralenti, les hommages familiaux — pour les couples et les familles. WeddingAI.video",
        "Review and customize your wedding video services — one-click checkout for packages and add-ons.": "Examinez et personnalisez vos services de vidéo de mariage — paiement en un clic pour les forfaits et suppléments.",
        "View before-and-after examples of AI wedding video restoration, slow motion, multilingual dubbing, and more.": "Voir des exemples avant-après de restauration de vidéo de mariage par IA, ralenti, doublage multilingue, et plus.",
        "Read more verified reviews on Trustpilot →": "Lire plus d'avis vérifiés sur Trustpilot →",
        "e.g., Sarah Johnson": "ex. Sarah Johnson",
        "e.g., sarah@example.com": "ex. sarah@example.com",
        "https://drive.google.com/...": "https://drive.google.com/...",
        "Describe your vision, the current state of your footage (tape format, condition, length), and any specific requests.": "Décrivez votre vision, l'état actuel de vos séquences (format de bande, état, durée) et toute demande spécifique.",
        "Get a free, no-obligation quote. Share your vision — we'll reply with a personalized recommendation and pricing within 24 hours.": "Obtenez un devis gratuit et sans engagement. Partagez votre vision — nous vous répondrons avec une recommandation personnalisée et un tarif sous 24 heures.",
        "Simple, transparent pricing for AI wedding video services. No hidden fees. Packages start at $79. WeddingAI.video": "Tarification simple et transparente pour les services de vidéo de mariage IA. Pas de frais cachés. Forfaits à partir de 79 $. WeddingAI.video",
        "In-depth wedding video guides: choose a videographer, AI wedding films, restore old tapes, multilingual dubbing, and more.": "Guides détaillés de vidéo de mariage : choisir un vidéaste, films de mariage IA, restaurer d'anciennes bandes, doublage multilingue, et plus.",
        "Search WeddingAI.video for AI wedding video services: restoration, multilingual dubbing, slow motion, trailers, tributes.": "Recherchez sur WeddingAI.video des services de vidéo de mariage IA : restauration, doublage multilingue, ralenti, bandes-annonces, hommages.",
        "e.g., slow motion, multilingual, restoration": "ex. ralenti, multilingue, restauration",
        "Your quote request has been received. We will reply within 24 hours with a personalized recommendation and pricing. WeddingAI.video": "Votre demande de devis a bien été reçue. Nous vous répondrons sous 24 heures avec une recommandation personnalisée et un tarif. WeddingAI.video",
        "Terms of service for WeddingAI.video. Read our service terms, payment policies, and legal agreements before ordering.": "Conditions d'utilisation de WeddingAI.video. Lisez nos conditions de service, politiques de paiement et accords légaux avant de commander.",
        "Restore 30-year-old VHS, 8mm, and Hi8 wedding footage to 4K. AI color correction, audio denoising. Vintage footage restoration service.": "Restaurez des séquences de mariage VHS, 8mm et Hi8 vieilles de 30 ans en 4K. Correction des couleurs par IA, débruitage audio. Service de restauration de séquences vintage.",
        "Vintage Footage Restoration — VHS to 4K, Color, Audio | WeddingAI.video": "Restauration de Séquences Vintage — VHS vers 4K, Couleur, Audio | WeddingAI.video",
        "Get custom wedding GIFs, memes, and shareable clips — perfect for social media, invites, and reception slideshows.": "Obtenez des GIFs, mèmes et clips partageables personnalisés pour votre mariage — parfaits pour les réseaux sociaux, invitations et diaporamas de réception.",
        "Want a sneak peek of your wedding? We create cinematic trailers from your footage — perfect for social media and reception play. WeddingAI.video": "Vous voulez un aperçu de votre mariage ? Nous créons des bandes-annonces cinématographiques à partir de vos séquences — parfait pour les réseaux sociaux et la diffusion à la réception. WeddingAI.video",
        "Your pet is family too. We create hilarious, heartwarming wedding videos starring your furry friend. WeddingAI.video": "Votre animal fait aussi partie de la famille. Nous créons des vidéos de mariage hilarantes et touchantes mettant en vedette votre compagnon à quatre pattes. WeddingAI.video",
        "Keep loved ones present on your wedding day. We respectfully create tributes from photos and videos. WeddingAI.video": "Gardez vos proches présents le jour de votre mariage. Nous créons respectueusement des hommages à partir de photos et vidéos. WeddingAI.video",
        "Family can't make it to your wedding? We film their message and integrate it into your wedding film seamlessly. WeddingAI.video": "Votre famille ne peut pas venir à votre mariage ? Nous filmons leur message et l'intégrons dans votre film de mariage en toute fluidité. WeddingAI.video",
    },
    "ja": {
        "50 in-depth articles on wedding video restoration, AI editing, slow motion, family tributes — for couples and families. WeddingAI.video": "結婚式ビデオの復元、AI編集、スローモーション、家族への追悼に関する50の詳細記事 — カップルとご家族向け。WeddingAI.video",
        "e.g., Sarah Johnson": "例：Sarah Johnson",
        "e.g., sarah@example.com": "例：sarah@example.com",
        "https://drive.google.com/...": "https://drive.google.com/...",
        "Describe your vision, the current state of your footage (tape format, condition, length), and any specific requests.": "ご希望のイメージ、映像の現在の状態（テープ形式、状態、長さ）、特別なご要望をお聞かせください。",
        "Get a free, no-obligation quote. Share your vision — we'll reply with a personalized recommendation and pricing within 24 hours.": "無料・無義務の見積もりを入手。あなたのビジョンを共有してください — 24時間以内にパーソナライズされた提案と料金で返信します。",
        "Simple, transparent pricing for AI wedding video services. No hidden fees. Packages start at $79. WeddingAI.video": "AI結婚式ビデオサービスのシンプルで透明な料金体系。隠れた手数料なし。パッケージは$79から。WeddingAI.video",
        "Search WeddingAI.video for AI wedding video services: restoration, multilingual dubbing, slow motion, trailers, tributes.": "WeddingAI.videoでAI結婚式ビデオサービスを検索：復元、多言語吹き替え、スローモーション、トレーラー、追悼。",
        "e.g., slow motion, multilingual, restoration": "例：スローモーション、多言語、復元",
        "Your quote request has been received. We will reply within 24 hours with a personalized recommendation and pricing. WeddingAI.video": "お見積もり依頼を受け付けました。24時間以内にパーソナライズされた提案と料金で返信します。WeddingAI.video",
        "Terms of service for WeddingAI.video. Read our service terms, payment policies, and legal agreements before ordering.": "WeddingAI.videoの利用規約。ご注文前にサービス条件、支払いポリシー、法的同意事項をお読みください。",
        "Restore 30-year-old VHS, 8mm, and Hi8 wedding footage to 4K. AI color correction, audio denoising. Vintage footage restoration service.": "30年前のVHS、8mm、Hi8の結婚式映像を4Kに復元。AIカラー補正、オーディオノイズ除去。ビンテージ映像復元サービス。",
        "Your pet is family too. We create hilarious, heartwarming wedding videos starring your furry friend. WeddingAI.video": "ペットも家族です。あなたの大切な毛むくじゃらの友達が主役の、面白くて心温まる結婚式ビデオを作成します。WeddingAI.video",
    },
    "pt": {
        "The page you were looking for doesn't exist. Browse our wedding video services or return home. WeddingAI.video": "A página que você procurava não existe. Navegue pelos nossos serviços de vídeo de casamento ou volte para a página inicial. WeddingAI.video",
        "order@weddingai.video": "order@weddingai.video",
        "Vintage Restoration": "Restauração Vintage",
        "Filmmakers and AI engineers building AI-powered wedding video services. Meet the team behind WeddingAI.video.": "Cineastas e engenheiros de IA construindo serviços de vídeo de casamento com IA. Conheça a equipe por trás do WeddingAI.video.",
        "About Us | Filmmakers + AI Engineers | WeddingAI.video": "Sobre Nós | Cineastas + Engenheiros de IA | WeddingAI.video",
        "★ Trustpilot": "★ Trustpilot",
        "50 in-depth articles on wedding video restoration, AI editing, slow motion, family tributes — for couples and families. WeddingAI.video": "50 artigos detalhados sobre restauração de vídeo de casamento, edição com IA, câmera lenta, homenagens familiares — para casais e famílias. WeddingAI.video",
        "Review and customize your wedding video services — one-click checkout for packages and add-ons.": "Revise e personalize seus serviços de vídeo de casamento — checkout com um clique para pacotes e complementos.",
        "View before-and-after examples of AI wedding video restoration, slow motion, multilingual dubbing, and more.": "Veja exemplos de antes e depois de restauração de vídeo de casamento com IA, câmera lenta, dublagem multilíngue e muito mais.",
        "Read more verified reviews on Trustpilot →": "Leia mais avaliações verificadas no Trustpilot →",
        "e.g., Sarah Johnson": "ex. Sarah Johnson",
        "e.g., sarah@example.com": "ex. sarah@example.com",
        "https://drive.google.com/...": "https://drive.google.com/...",
        "Describe your vision, the current state of your footage (tape format, condition, length), and any specific requests.": "Descreva sua visão, o estado atual do seu material (formato de fita, condição, duração) e quaisquer solicitações específicas.",
        "Get a free, no-obligation quote. Share your vision — we'll reply with a personalized recommendation and pricing within 24 hours.": "Obtenha um orçamento gratuito e sem compromisso. Compartilhe sua visão — responderemos com uma recomendação personalizada e preços em 24 horas.",
        "Simple, transparent pricing for AI wedding video services. No hidden fees. Packages start at $79. WeddingAI.video": "Preços simples e transparentes para serviços de vídeo de casamento com IA. Sem taxas ocultas. Pacotes a partir de $79. WeddingAI.video",
        "In-depth wedding video guides: choose a videographer, AI wedding films, restore old tapes, multilingual dubbing, and more.": "Guias detalhados de vídeo de casamento: escolha um videógrafo, filmes de casamento com IA, restaure fitas antigas, dublagem multilíngue e muito mais.",
        "Search WeddingAI.video for AI wedding video services: restoration, multilingual dubbing, slow motion, trailers, tributes.": "Pesquise no WeddingAI.video por serviços de vídeo de casamento com IA: restauração, dublagem multilíngue, câmera lenta, trailers, homenagens.",
        "e.g., slow motion, multilingual, restoration": "ex. câmera lenta, multilíngue, restauração",
        "Your quote request has been received. We will reply within 24 hours with a personalized recommendation and pricing. WeddingAI.video": "Sua solicitação de orçamento foi recebida. Responderemos em 24 horas com uma recomendação personalizada e preços. WeddingAI.video",
        "Terms of service for WeddingAI.video. Read our service terms, payment policies, and legal agreements before ordering.": "Termos de serviço do WeddingAI.video. Leia nossos termos de serviço, políticas de pagamento e acordos legais antes de fazer o pedido.",
        "Restore 30-year-old VHS, 8mm, and Hi8 wedding footage to 4K. AI color correction, audio denoising. Vintage footage restoration service.": "Restaure filmagens de casamento VHS, 8mm e Hi8 de 30 anos para 4K. Correção de cor com IA, redução de ruído de áudio. Serviço de restauração de filmagens vintage.",
        "Vintage Footage Restoration — VHS to 4K, Color, Audio | WeddingAI.video": "Restauração de Filmagens Vintage — VHS para 4K, Cor, Áudio | WeddingAI.video",
        "Get custom wedding GIFs, memes, and shareable clips — perfect for social media, invites, and reception slideshows.": "Obtenha GIFs, memes e clipes compartilháveis personalizados para casamento — perfeitos para redes sociais, convites e slideshows de recepção.",
        "Want a sneak peek of your wedding? We create cinematic trailers from your footage — perfect for social media and reception play. WeddingAI.video": "Quer uma prévia do seu casamento? Criamos trailers cinematográficos a partir de suas filmagens — perfeito para redes sociais e exibição na recepção. WeddingAI.video",
        "Your pet is family too. We create hilarious, heartwarming wedding videos starring your furry friend. WeddingAI.video": "Seu pet também é família. Criamos vídeos de casamento hilários e emocionantes estrelando seu amigo peludo. WeddingAI.video",
        "Keep loved ones present on your wedding day. We respectfully create tributes from photos and videos. WeddingAI.video": "Mantenha seus entes queridos presentes no dia do seu casamento. Criamos homenagens respeitosas a partir de fotos e vídeos. WeddingAI.video",
        "Family can't make it to your wedding? We film their message and integrate it into your wedding film seamlessly. WeddingAI.video": "Sua família não pode comparecer ao seu casamento? Filmamos a mensagem deles e a integramos ao seu filme de casamento perfeitamente. WeddingAI.video",
    },
    "ru": {
        "The page you were looking for doesn't exist. Browse our wedding video services or return home. WeddingAI.video": "Страница, которую вы искали, не существует. Просмотрите наши услуги по свадебному видео или вернитесь на главную. WeddingAI.video",
        "order@weddingai.video": "order@weddingai.video",
        "Vintage Restoration": "Винтажная реставрация",
        "Filmmakers and AI engineers building AI-powered wedding video services. Meet the team behind WeddingAI.video.": "Кинематографисты и инженеры ИИ создают сервисы свадебного видео на базе ИИ. Познакомьтесь с командой WeddingAI.video.",
        "About Us | Filmmakers + AI Engineers | WeddingAI.video": "О нас | Кинематографисты + Инженеры ИИ | WeddingAI.video",
        "★ Trustpilot": "★ Trustpilot",
        "50 in-depth articles on wedding video restoration, AI editing, slow motion, family tributes — for couples and families. WeddingAI.video": "50 подробных статей о реставрации свадебного видео, ИИ-редактировании, замедленной съемке, семейных трибьютах — для пар и семей. WeddingAI.video",
        "Review and customize your wedding video services — one-click checkout for packages and add-ons.": "Просмотрите и настройте услуги свадебного видео — оформление заказа в один клик для пакетов и дополнений.",
        "View before-and-after examples of AI wedding video restoration, slow motion, multilingual dubbing, and more.": "Посмотрите примеры до и после реставрации свадебного видео с ИИ, замедленной съемки, многоязычного дубляжа и многого другого.",
        "Read more verified reviews on Trustpilot →": "Читать больше проверенных отзывов на Trustpilot →",
        "e.g., Sarah Johnson": "напр. Sarah Johnson",
        "e.g., sarah@example.com": "напр. sarah@example.com",
        "https://drive.google.com/...": "https://drive.google.com/...",
        "Describe your vision, the current state of your footage (tape format, condition, length), and any specific requests.": "Опишите ваше видение, текущее состояние материала (формат пленки, состояние, продолжительность) и любые особые пожелания.",
        "Get a free, no-obligation quote. Share your vision — we'll reply with a personalized recommendation and pricing within 24 hours.": "Получите бесплатную смету без обязательств. Поделитесь своим видением — мы ответим с персонализированной рекомендацией и ценой в течение 24 часов.",
        "Simple, transparent pricing for AI wedding video services. No hidden fees. Packages start at $79. WeddingAI.video": "Простые, прозрачные цены на услуги свадебного видео с ИИ. Никаких скрытых платежей. Пакеты от $79. WeddingAI.video",
        "In-depth wedding video guides: choose a videographer, AI wedding films, restore old tapes, multilingual dubbing, and more.": "Подробные руководства по свадебному видео: выбор видеооператора, свадебные фильмы с ИИ, реставрация старых пленок, многоязычный дубляж и многое другое.",
        "Search WeddingAI.video for AI wedding video services: restoration, multilingual dubbing, slow motion, trailers, tributes.": "Поиск на WeddingAI.video услуг свадебного видео с ИИ: реставрация, многоязычный дубляж, замедленная съемка, трейлеры, трибьюты.",
        "e.g., slow motion, multilingual, restoration": "напр. замедленная съемка, многоязычный, реставрация",
        "Your quote request has been received. We will reply within 24 hours with a personalized recommendation and pricing. WeddingAI.video": "Ваш запрос на смету получен. Мы ответим в течение 24 часов с персонализированной рекомендацией и ценой. WeddingAI.video",
        "Terms of service for WeddingAI.video. Read our service terms, payment policies, and legal agreements before ordering.": "Условия использования WeddingAI.video. Ознакомьтесь с нашими условиями обслуживания, политикой оплаты и юридическими соглашениями перед заказом.",
        "Restore 30-year-old VHS, 8mm, and Hi8 wedding footage to 4K. AI color correction, audio denoising. Vintage footage restoration service.": "Восстановите 30-летние свадебные записи VHS, 8mm и Hi8 до 4K. ИИ-коррекция цвета, шумоподавление звука. Услуга реставрации винтажных записей.",
        "Vintage Footage Restoration — VHS to 4K, Color, Audio | WeddingAI.video": "Реставрация Винтажных Записей — VHS в 4K, Цвет, Звук | WeddingAI.video",
        "Get custom wedding GIFs, memes, and shareable clips — perfect for social media, invites, and reception slideshows.": "Получите персонализированные свадебные GIF, мемы и клипы для sharing — идеально для соцсетей, приглашений и слайд-шоу на приеме.",
        "Want a sneak peek of your wedding? We create cinematic trailers from your footage — perfect for social media and reception play. WeddingAI.video": "Хотите предпоказ вашей свадьбы? Мы создаем кинематографичные трейлеры из ваших записей — идеально для соцсетей и показа на приеме. WeddingAI.video",
        "Your pet is family too. We create hilarious, heartwarming wedding videos starring your furry friend. WeddingAI.video": "Ваш питомец тоже семья. Мы создаем веселые, трогательные свадебные видео с вашим пушистым другом в главной роли. WeddingAI.video",
        "Keep loved ones present on your wedding day. We respectfully create tributes from photos and videos. WeddingAI.video": "Сохраните присутствие близких в день вашей свадьбы. Мы с уважением создаем трибьюты из фотографий и видео. WeddingAI.video",
        "Family can't make it to your wedding? We film their message and integrate it into your wedding film seamlessly. WeddingAI.video": "Семья не может приехать на вашу свадьбу? Мы снимаем их послание и плавно интегрируем его в ваш свадебный фильм. WeddingAI.video",
    },
    "th": {
        "order@weddingai.video": "order@weddingai.video",
        "Vintage Restoration": "การฟื้นฟูวิดีโอวินเทจ",
        "★ Trustpilot": "★ Trustpilot",
        "Read more verified reviews on Trustpilot →": "อ่านรีวิวที่ผ่านการตรวจสอบเพิ่มเติมบน Trustpilot →",
        "e.g., Sarah Johnson": "เช่น Sarah Johnson",
        "e.g., sarah@example.com": "เช่น sarah@example.com",
        "https://drive.google.com/...": "https://drive.google.com/...",
        "Describe your vision, the current state of your footage (tape format, condition, length), and any specific requests.": "อธิบายวิสัยทัศน์ของคุณ สถานะปัจจุบันของฟุตเทจ (รูปแบบเทป สภาพ ความยาว) และคำขอเฉพาะใดๆ",
        "Get a free, no-obligation quote. Share your vision — we'll reply with a personalized recommendation and pricing within 24 hours.": "รับใบเสนอราคาฟรีไม่มีข้อผูกมัด แบ่งปันวิสัยทัศน์ของคุณ — เราจะตอบกลับพร้อมคำแนะนำและราคาที่ปรับให้เหมาะกับคุณภายใน 24 ชั่วโมง",
        "Simple, transparent pricing for AI wedding video services. No hidden fees. Packages start at $79. WeddingAI.video": "ราคาที่เรียบง่ายและโปร่งใสสำหรับบริการวิดีโอแต่งงานด้วย AI ไม่มีค่าธรรมเนียมแอบแฝง แพ็คเกจเริ่มต้นที่ $79. WeddingAI.video",
        "In-depth wedding video guides: choose a videographer, AI wedding films, restore old tapes, multilingual dubbing, and more.": "คู่มือวิดีโอแต่งงานเชิงลึก: เลือกช่างวิดีโอ ภาพยนตร์แต่งงานด้วย AI ฟื้นฟูเทปเก่า พากย์หลายภาษา และอื่นๆ",
        "Search WeddingAI.video for AI wedding video services: restoration, multilingual dubbing, slow motion, trailers, tributes.": "ค้นหา WeddingAI.video สำหรับบริการวิดีโอแต่งงานด้วย AI: การฟื้นฟู การพากย์หลายภาษา สโลว์โมชั่น ตัวอย่าง การรำลึก",
        "e.g., slow motion, multilingual, restoration": "เช่น สโลว์โมชั่น หลายภาษา การฟื้นฟู",
        "Your quote request has been received. We will reply within 24 hours with a personalized recommendation and pricing. WeddingAI.video": "ได้รับคำขอใบเสนอราคาของคุณแล้ว เราจะตอบกลับภายใน 24 ชั่วโมงพร้อมคำแนะนำและราคาที่ปรับให้เหมาะกับคุณ WeddingAI.video",
        "Terms of service for WeddingAI.video. Read our service terms, payment policies, and legal agreements before ordering.": "ข้อกำหนดในการให้บริการของ WeddingAI.video อ่านเงื่อนไขการบริการ นโยบายการชำระเงิน และข้อตกลงทางกฎหมายก่อนสั่งซื้อ",
        # index FAQ
        "We use commercial-grade AI models with safety guardrails. A human filmmaker reviews every project, and we never apply AI to alter facial features or body shapes without explicit consent.": "เราใช้โมเดล AI ระดับเชิงพาณิชย์พร้อมระบบป้องกันความปลอดภัย ผู้สร้างภาพยนตร์มืออาชีพตรวจสอบทุกโปรเจกต์ และเราไม่ใช้ AI เพื่อเปลี่ยนแปลงลักษณะใบหน้าหรือรูปร่างโดยไม่ได้รับความยินยอมอย่างชัดแจ้ง",
        "Your footage is stored encrypted on secure US-based servers. Files are automatically deleted 30 days after project delivery unless you request archival storage.": "ฟุตเทจของคุณถูกจัดเก็บแบบเข้ารหัสบนเซิร์ฟเวอร์ที่ปลอดภัยในสหรัฐอเมริกา ไฟล์จะถูกลบโดยอัตโนมัติ 30 วันหลังจากการส่งมอบโครงการ เว้นแต่คุณจะขอการจัดเก็บถาวร",
        "You own the final video. We retain a non-exclusive license to use anonymized excerpts in our portfolio (you can opt out anytime). You're free to use your video commercially.": "คุณเป็นเจ้าของวิดีโอสุดท้าย เราคงสิทธิ์การใช้งานแบบไม่ผูกขาดเพื่อใช้ตัวอย่างที่ไม่ระบุตัวตนในพอร์ตโฟลิโอของเรา (คุณสามารถยกเลิกได้ตลอดเวลา) คุณมีอิสระในการใช้วิดีโอของคุณในเชิงพาณิชย์",
        "Yes. Most services offer 48-hour rush delivery for an additional 30-50% fee, depending on project complexity.": "ได้ บริการส่วนใหญ่มีบริการจัดส่งด่วน 48 ชั่วโมงโดยมีค่าธรรมเนียมเพิ่มเติม 30-50% ขึ้นอยู่กับความซับซ้อนของโครงการ",
        "Bundle discounts apply when you book 2+ services on the same project: 10% off for 2 services, 15% off for 3, and 20% off for 4 or more.": "ส่วนลดแพ็คเกจเมื่อคุณจอง 2 บริการขึ้นไปในโครงการเดียวกัน: ลด 10% สำหรับ 2 บริการ, ลด 15% สำหรับ 3 บริการ, และลด 20% สำหรับ 4 บริการขึ้นไป",
        "Do you offer rush delivery?": "มีบริการจัดส่งด่วนไหม?",
        "How do you handle my personal footage and privacy?": "คุณจัดการฟุตเทจส่วนตัวและความเป็นส่วนตัวของฉันอย่างไร?",
        "How does pricing work for multiple services?": "ราคาสำหรับหลายบริการทำงานอย่างไร?",
        "What about AI safety and bias in your processing?": "แล้วความปลอดภัยและอคติของ AI ในการประมวลผลล่ะ?",
        "Who owns the final video and can I use it commercially?": "ใครเป็นเจ้าของวิดีโอสุดท้ายและฉันสามารถใช้ในเชิงพาณิชย์ได้ไหม?",
        # index service descriptions
        "Starring your pet! Fun opener or save-the-date.": "นำแสดงโดยสัตว์เลี้ยงของคุณ! เปิดตัวอย่างสนุกหรือการ์ด save-the-date",
        "1-3 minute cinematic trailer for social and reception playback.": "ตัวอย่างภาพยนตร์ 1-3 นาทีสำหรับโซเชียลและการฉายในงานเลี้ยง",
        "10 shareable GIFs and memes for social media.": "GIF และมีม 10 แบบที่แชร์ได้สำหรับโซเชียลมีเดีย",
        "Ghibli, Pixar, or anime style applied to your footage.": "สไตล์ Ghibli, Pixar หรืออะนิเมะที่นำไปใช้กับฟุตเทจของคุณ",
        "23 languages — AI dubbing and subtitles for international family.": "23 ภาษา — การพากย์และคำบรรยายด้วย AI สำหรับครอบครัวนานาชาติ",
        "Recover 30-year-old VHS tapes, upscale 8mm to 4K, color correct and denoise audio. Your parents' wedding, renewed.": "กู้คืนเทป VHS อายุ 30 ปี อัปสเกล 8mm เป็น 4K แก้ไขสีและลดเสียงรบกวน งานแต่งงานของพ่อแม่คุณ ฟื้นฟูใหม่",
        "Turn your wedding photos into a cinematic AI-generated film.": "เปลี่ยนภาพถ่ายงานแต่งงานของคุณให้เป็นภาพยนตร์ที่สร้างโดย AI แบบภาพยนตร์",
        "Remote family recorded a message and we embed it seamlessly into your film.": "ครอบครัวที่อยู่ห่างไกลบันทึกข้อความและเราแทรกลงในภาพยนตร์ของคุณอย่างแนบเนียน",
        "Honor a deceased loved one with a beautiful memorial video montage.": "ให้เกียรติผู้เป็นที่รักที่ล่วงลับด้วยวิดีโออนุสรณ์ที่สวยงาม",
        "AI-generated celebrity-style message. Surprising, legal, ethical.": "ข้อความสไตล์คนดังที่สร้างโดย AI น่าประหลาดใจ ถูกกฎหมาย มีจริยธรรม",
        # vintage restoration page
        "Restore Your 30-Year-Old Wedding Memories": "ฟื้นฟูความทรงจำงานแต่งงานอายุ 30 ปีของคุณ",
        "How It Works": "วิธีการทำงาน",
        "What We Accept": "สิ่งที่เรารับ",
        "Why This Matters": "ทำไมสิ่งนี้ถึงสำคัญ",
        "Digital Files": "ไฟล์ดิจิทัล",
        "Film Reels": "ฟิล์มรีล",
        "Videotape": "วิดีโอเทป",
        "Send Us Your Footage": "ส่งฟุตเทจของคุณมาให้เรา",
        "Free Diagnostic & Quote": "การวินิจฉัยและใบเสนอราคาฟรี",
        "AI Restoration & Delivery": "การฟื้นฟูและจัดส่งด้วย AI",
        "AI-powered restoration: digitize VHS/8mm, upscale to 4K, fix color, denoise audio. Your parents' wedding, renewed for the next generation.": "การฟื้นฟูด้วย AI: แปลง VHS/8mm เป็นดิจิทัล อัปสเกลเป็น 4K แก้ไขสี ลดเสียงรบกวน งานแต่งงานของพ่อแม่คุณ ฟื้นฟูใหม่สำหรับคนรุ่นต่อไป",
        "Three steps. No technical knowledge required.": "สามขั้นตอน ไม่จำเป็นต้องมีความรู้ทางเทคนิค",
        "Tape, film, and digital — we handle it all.": "เทป ฟิล์ม และดิจิทัล — เราจัดการทั้งหมด",
        "Your parents' wedding video, your grandparents' 8mm reels, the one VHS tape you've been meaning to digitize for years — these aren't just recordings. They're your family's visual legacy.": "วิดีโองานแต่งงานของพ่อแม่คุณ ฟิล์ม 8mm ของปู่ย่าตายาย เทป VHS ที่คุณตั้งใจจะแปลงเป็นดิจิทัลมาหลายปี — สิ่งเหล่านี้ไม่ใช่แค่การบันทึก แต่มันคือมรดกทางภาพของครอบครัวคุณ",
        "Every year, another 10% of VHS tapes become unplayable due to magnetic tape decay. Don't let your family memories disappear.": "ทุกปี เทป VHS อีก 10% ไม่สามารถเล่นได้เนื่องจากการเสื่อมสภาพของเทปแม่เหล็ก อย่าปล่อยให้ความทรงจำของครอบครัวคุณหายไป",
        "Upload digital files through our secure portal, or ship physical tapes or film reels to our lab. We cover shipping costs for orders over $200.": "อัปโหลดไฟล์ดิจิทัลผ่านพอร์ทัลที่ปลอดภัยของเรา หรือส่งเทปหรือฟิล์มรีลมายังห้องปฏิบัติการของเรา เราครอบคลุมค่าจัดส่งสำหรับคำสั่งซื้อมากกว่า $200",
        "Our team inspects your footage, identifies damage, and emails you a no-obligation quote within 48 hours. No payment required upfront.": "ทีมงานของเราตรวจสอบฟุตเทจของคุณ ระบุความเสียหาย และส่งใบเสนอราคาที่ไม่มีข้อผูกมัดทางอีเมลภายใน 48 ชั่วโมง ไม่ต้องชำระเงินล่วงหน้า",
        "We restore your footage in your chosen package. You get a private watermarked review link. After approval, we deliver final files. Rush delivery available.": "เราฟื้นฟูฟุตเทจของคุณตามแพ็คเกจที่คุณเลือก คุณจะได้รับลิงก์ตรวจสอบพร้อมลายน้ำส่วนตัว หลังจากอนุมัติ เราจัดส่งไฟล์สุดท้าย มีบริการจัดส่งด่วน",
        "My tape is so damaged it won't play. Can you still recover it?": "เทปของฉันเสียหายมากจนเล่นไม่ได้ คุณยังสามารถกู้คืนได้ไหม?",
        "In most cases, yes. Our team uses professional VCRs with built-in TBC (time-base correction) and can splice broken tapes. Even moldy tapes can often be cleaned and digitized. Success rate: ~95% for VHS tapes.": "ในกรณีส่วนใหญ่ ได้ ทีมงานของเราใช้ VCR มืออาชีพพร้อม TBC ในตัว (การแก้ไขฐานเวลา) และสามารถต่อเทปที่ขาดได้ แม้แต่เทปที่มีเชื้อราก็มักจะสามารถทำความสะอาดและแปลงเป็นดิจิทัลได้ อัตราความสำเร็จ: ~95% สำหรับเทป VHS",
        "Will upscaling to 4K make my old footage look fake?": "การอัปสเกลเป็น 4K จะทำให้ฟุตเทจเก่าดูปลอมไหม?",
        "No. Our AI upscaler is specifically trained on archival wedding footage. It adds realistic detail without the 'plastic' look of generic upscalers. Color correction preserves the warm, nostalgic feel of your original footage.": "ไม่ อัปสเกลเลอร์ AI ของเราถูกฝึกมาโดยเฉพาะกับฟุตเทจงานแต่งงานที่เก็บถาวร มันเพิ่มรายละเอียดที่สมจริงโดยไม่มีลักษณะ 'พลาสติก' ของอัปสเกลเลอร์ทั่วไป การแก้ไขสีรักษาความรู้สึกอบอุ่นและคิดถึงของฟุตเทจดั้งเดิมของคุณ",
        "What tape and film formats do you accept?": "คุณรับเทปและฟิล์มรูปแบบใดบ้าง?",
        "We accept VHS, S-VHS, VHS-C, Hi8, Digital8, MiniDV, Betamax, MiniDVD, 8mm film, Super 8, and 16mm film. If you have a format not listed here, contact us — we can likely handle it.": "เรารับ VHS, S-VHS, VHS-C, Hi8, Digital8, MiniDV, Betamax, MiniDVD, ฟิล์ม 8mm, Super 8, และฟิล์ม 16mm หากคุณมีรูปแบบที่ไม่ได้ระบุไว้ที่นี่ ติดต่อเรา — เราน่าจะจัดการได้",
        "MP4, MOV, AVI, MKV, MPG, WebM — any resolution from 144p to 4K. We can also accept ripped DVDs and Blu-rays.": "MP4, MOV, AVI, MKV, MPG, WebM — ความละเอียดใดก็ได้ตั้งแต่ 144p ถึง 4K เรายังรับดีวีดีและบลูเรย์ที่ริปแล้ว",
        "8mm, Super 8, and 16mm film. We work with a partner lab for physical film scanning (included in price).": "ฟิล์ม 8mm, Super 8, และ 16mm เราทำงานร่วมกับห้องปฏิบัติการพันธมิตรสำหรับการสแกนฟิล์มจริง (รวมอยู่ในราคา)",
        "VHS, S-VHS, VHS-C, Hi8, Digital8, MiniDV, Betamax, MiniDVD. Even tapes that won't play anymore — our forensic recovery tools can often extract the video signal.": "VHS, S-VHS, VHS-C, Hi8, Digital8, MiniDV, Betamax, MiniDVD แม้แต่เทปที่เล่นไม่ได้อีกต่อไป — เครื่องมือกู้คืนทางนิติวิทยาศาสตร์ของเรามักจะสามารถดึงสัญญาณวิดีโอออกมาได้",
        "Vintage Footage Restoration — VHS to 4K, Color, Audio | WeddingAI.video": "การฟื้นฟูฟุตเทจวินเทจ — VHS เป็น 4K, สี, เสียง | WeddingAI.video",
    },
    "zh": {
        "Vintage Restoration": "老视频修复",
        "The page you were looking for doesn't exist. Browse our wedding video services or return home. WeddingAI.video": "您要找的页面不存在。浏览我们的婚礼视频服务或返回首页。WeddingAI.video",
        "★ Trustpilot": "★ Trustpilot",
        "Read more verified reviews on Trustpilot →": "在 Trustpilot 上查看更多真实评价 →",
        "https://drive.google.com/...": "https://drive.google.com/...",
        "50 in-depth articles on wedding video restoration, AI editing, slow motion, family tributes — for couples and families. WeddingAI.video": "50篇关于婚礼视频修复、AI编辑、慢动作、家庭致敬的深度文章 — 为夫妇和家庭服务。WeddingAI.video",
        "In-depth wedding video guides: choose a videographer, AI wedding films, restore old tapes, multilingual dubbing, and more.": "深度婚礼视频指南：选择摄像师、AI婚礼影片、修复老旧录像带、多语言配音等。",
        "Search WeddingAI.video for AI wedding video services: restoration, multilingual dubbing, slow motion, trailers, tributes.": "在 WeddingAI.video 搜索AI婚礼视频服务：修复、多语言配音、慢动作、预告片、致敬视频。",
        "Restore 30-year-old VHS, 8mm, and Hi8 wedding footage to 4K. AI color correction, audio denoising. Vintage footage restoration service.": "将30年前的VHS、8mm和Hi8婚礼录像修复至4K。AI色彩校正、音频降噪。老视频修复服务。",
        "Vintage Footage Restoration — VHS to 4K, Color, Audio | WeddingAI.video": "老视频修复 — VHS转4K、色彩校正、音频降噪 | WeddingAI.video",
        "Get custom wedding GIFs, memes, and shareable clips — perfect for social media, invites, and reception slideshows.": "获取定制婚礼GIF、表情包和可分享短视频 — 适合社交媒体、请柬和婚宴幻灯片。",
        "Want a sneak peek of your wedding? We create cinematic trailers from your footage — perfect for social media and reception play. WeddingAI.video": "想提前预览婚礼？我们用您的素材制作电影级预告片 — 适合社交媒体和婚宴播放。WeddingAI.video",
        "Your pet is family too. We create hilarious, heartwarming wedding videos starring your furry friend. WeddingAI.video": "宠物也是家人。我们为您的毛孩子制作搞笑又温馨的婚礼视频。WeddingAI.video",
        "Keep loved ones present on your wedding day. We respectfully create tributes from photos and videos. WeddingAI.video": "让亲人始终陪伴在您的婚礼上。我们用心制作来自照片和视频的致敬影片。WeddingAI.video",
        "Family can't make it to your wedding? We film their message and integrate it into your wedding film seamlessly. WeddingAI.video": "家人无法到场？我们拍摄他们的祝福并无缝融入您的婚礼影片。WeddingAI.video",
        "Your quote request has been received. We will reply within 24 hours with a personalized recommendation and pricing. WeddingAI.video": "您的报价请求已收到。我们会在24小时内回复个性化方案和报价。WeddingAI.video",
        # index FAQ zh
        "We use commercial-grade AI models with safety guardrails. A human filmmaker reviews every project, and we never apply AI to alter facial features or body shapes without explicit consent.": "我们使用商业级AI模型并配备安全防护。每个项目都由专业电影制作人审查，未经明确同意，我们不会使用AI修改面部特征或体型。",
        "Your footage is stored encrypted on secure US-based servers. Files are automatically deleted 30 days after project delivery unless you request archival storage.": "您的视频素材加密存储在美国安全服务器上。项目交付30天后文件自动删除，除非您申请存档保存。",
        "You own the final video. We retain a non-exclusive license to use anonymized excerpts in our portfolio (you can opt out anytime). You're free to use your video commercially.": "您拥有最终成片的所有权。我们保留在作品集中使用匿名片段的非独占许可（您可随时选择退出）。您可以自由将视频用于商业用途。",
        "Yes. Most services offer 48-hour rush delivery for an additional 30-50% fee, depending on project complexity.": "是的。大多数服务提供48小时加急交付，根据项目复杂度收取30-50%的附加费用。",
        "Bundle discounts apply when you book 2+ services on the same project: 10% off for 2 services, 15% off for 3, and 20% off for 4 or more.": "同一项目预订2项及以上服务可享套餐折扣：2项9折，3项85折，4项及以上8折。",
        "Do you offer rush delivery?": "你们提供加急服务吗？",
        "How do you handle my personal footage and privacy?": "你们如何处理我的个人视频素材和隐私？",
        "How does pricing work for multiple services?": "多项服务的价格怎么算？",
        "What about AI safety and bias in your processing?": "AI处理过程中的安全和偏见问题怎么保障？",
        "Who owns the final video and can I use it commercially?": "最终成片归谁所有，我可以用于商业用途吗？",
        # index service descriptions zh
        "Starring your pet! Fun opener or save-the-date.": "宠物主演！有趣的片头或婚礼预告。",
        "1-3 minute cinematic trailer for social and reception playback.": "1-3分钟电影级预告片，适合社交媒体和婚宴播放。",
        "10 shareable GIFs and memes for social media.": "10个可分享的GIF动图和表情包，专为社交媒体打造。",
        "Ghibli, Pixar, or anime style applied to your footage.": "吉卜力、皮克斯或动漫风格应用到您的视频中。",
        "23 languages — AI dubbing and subtitles for international family.": "23种语言 — AI配音和字幕，让跨国亲友都能理解。",
        "Recover 30-year-old VHS tapes, upscale 8mm to 4K, color correct and denoise audio. Your parents' wedding, renewed.": "修复30年前的VHS录像带，将8mm升级至4K，色彩校正和音频降噪。让父母的婚礼重获新生。",
        "Turn your wedding photos into a cinematic AI-generated film.": "将您的婚礼照片变成电影级AI生成影片。",
        "Remote family recorded a message and we embed it seamlessly into your film.": "远程亲友录制祝福，我们将其无缝嵌入您的婚礼影片。",
        "Honor a deceased loved one with a beautiful memorial video montage.": "为已故亲人制作精美的纪念视频蒙太奇。",
        "AI-generated celebrity-style message. Surprising, legal, ethical.": "AI生成的名人风格祝福。惊喜、合法、合乎道德。",
        # vintage restoration zh
        "Restore Your 30-Year-Old Wedding Memories": "修复您30年前的婚礼记忆",
        "How It Works": "工作原理",
        "What We Accept": "我们接受的格式",
        "Why This Matters": "为什么这很重要",
        "Digital Files": "数字文件",
        "Film Reels": "胶片卷",
        "Videotape": "录像带",
        "Send Us Your Footage": "发送您的录像素材",
        "Free Diagnostic & Quote": "免费诊断和报价",
        "AI Restoration & Delivery": "AI修复和交付",
        "AI-powered restoration: digitize VHS/8mm, upscale to 4K, fix color, denoise audio. Your parents' wedding, renewed for the next generation.": "AI驱动修复：将VHS/8mm数字化，升级至4K，修复色彩，降噪音频。让父母的婚礼为下一代重焕新生。",
        "Three steps. No technical knowledge required.": "三步完成。无需任何技术知识。",
        "Tape, film, and digital — we handle it all.": "录像带、胶片和数字文件 — 我们全都能处理。",
        "Your parents' wedding video, your grandparents' 8mm reels, the one VHS tape you've been meaning to digitize for years — these aren't just recordings. They're your family's visual legacy.": "父母的婚礼录像、祖父母的8mm胶片、那盒你一直想数字化多年的VHS录像带 — 这些不仅仅是录像。它们是你家族的视觉传承。",
        "Every year, another 10% of VHS tapes become unplayable due to magnetic tape decay. Don't let your family memories disappear.": "每年，又有10%的VHS录像带因磁性衰减而无法播放。别让你的家庭记忆消失。",
        "Upload digital files through our secure portal, or ship physical tapes or film reels to our lab. We cover shipping costs for orders over $200.": "通过我们安全的门户上传数字文件，或将实体录像带或胶片寄到我们实验室。订单超过$200我们承担运费。",
        "Our team inspects your footage, identifies damage, and emails you a no-obligation quote within 48 hours. No payment required upfront.": "我们的团队检查您的素材、识别损坏部位，并在48小时内通过邮件发送无义务报价。无需预付。",
        "We restore your footage in your chosen package. You get a private watermarked review link. After approval, we deliver final files. Rush delivery available.": "我们按您选择的套餐修复素材。您会收到带水印的私密审查链接。批准后，我们交付最终文件。支持加急交付。",
        "My tape is so damaged it won't play. Can you still recover it?": "我的录像带损坏严重无法播放，你们还能修复吗？",
        "In most cases, yes. Our team uses professional VCRs with built-in TBC (time-base correction) and can splice broken tapes. Even moldy tapes can often be cleaned and digitized. Success rate: ~95% for VHS tapes.": "大多数情况下可以。我们使用带内置TBC（时基校正）的专业VCR，可以拼接断裂的录像带。即使发霉的录像带通常也能清理并数字化。成功率：VHS录像带约95%。",
        "Will upscaling to 4K make my old footage look fake?": "升级到4K会让我的老视频看起来假吗？",
        "No. Our AI upscaler is specifically trained on archival wedding footage. It adds realistic detail without the 'plastic' look of generic upscalers. Color correction preserves the warm, nostalgic feel of your original footage.": "不会。我们的AI升频器专门针对存档婚礼素材训练。它能添加真实细节，而不会像通用升频器那样产生'塑料感'。色彩校正保留原素材温暖怀旧的感觉。",
        "What tape and film formats do you accept?": "你们接受哪些录像带和胶片格式？",
        "We accept VHS, S-VHS, VHS-C, Hi8, Digital8, MiniDV, Betamax, MiniDVD, 8mm film, Super 8, and 16mm film. If you have a format not listed here, contact us — we can likely handle it.": "我们接受VHS、S-VHS、VHS-C、Hi8、Digital8、MiniDV、Betamax、MiniDVD、8mm胶片、Super 8和16mm胶片。如有未列出的格式，请联系我们 — 大概率也能处理。",
        "MP4, MOV, AVI, MKV, MPG, WebM — any resolution from 144p to 4K. We can also accept ripped DVDs and Blu-rays.": "MP4、MOV、AVI、MKV、MPG、WebM — 从144p到4K的任何分辨率。我们还接受DVD和蓝光翻录文件。",
        "8mm, Super 8, and 16mm film. We work with a partner lab for physical film scanning (included in price).": "8mm、Super 8和16mm胶片。我们与合作伙伴实验室合作进行实体胶片扫描（包含在价格中）。",
        "VHS, S-VHS, VHS-C, Hi8, Digital8, MiniDV, Betamax, MiniDVD. Even tapes that won't play anymore — our forensic recovery tools can often extract the video signal.": "VHS、S-VHS、VHS-C、Hi8、Digital8、MiniDV、Betamax、MiniDVD。即使无法播放的录像带 — 我们的取证恢复工具通常也能提取视频信号。",
    },
}

def main():
    print("=" * 70)
    print("WeddingAI.video — i18n Translation")
    print("=" * 70)

    # Load en.json as source
    with open(I18N_DIR / "en.json", encoding="utf-8") as f:
        en_data = json.load(f)

    total_translated = 0

    for lang, translations in sorted(TRANSLATIONS.items()):
        json_path = I18N_DIR / f"{lang}.json"
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        count = 0
        for key, en_val in en_data.items():
            if key in data and data[key] == en_val:
                if en_val in translations:
                    data[key] = translations[en_val]
                    count += 1
                else:
                    # Auto-translate short technical terms that stay the same
                    # These are things like "MP4 (H.264)", "Dropbox", "iCloud", etc.
                    pass

        if count > 0:
            # Sort and save
            sorted_data = dict(sorted(data.items()))
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(sorted_data, f, ensure_ascii=False, indent=2)
                f.write("\n")
            print(f"  {lang}: {count} keys translated")
            total_translated += count
        else:
            print(f"  {lang}: no untranslated keys found")

    print(f"\n  Total translated: {total_translated}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
