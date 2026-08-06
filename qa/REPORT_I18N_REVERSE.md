# i18n Reverse-Translation Audit — 2026-07-28

**Source keys (en.json):** 6436
**Method:** Google translate gtx (zh/es/fr/de/pt/ja/ru/ar/th) reverse-translated to English, then SequenceMatcher similarity vs. original EN. 4 workers concurrent.

**Translator (declared in `_meta`):** Google Translate (machine) for all 9 langs. The audit is checking how well those machine translations actually preserve meaning when round-tripped.

## Per-language summary

| lang | name | total_keys | scored | SUSPICIOUS (sim<0.65) | review (0.65-0.9) | ok (>=0.9) | no_score (short text) | susp_rate |
|------|------|------------|--------|------------------------|---------------------|------------|----------------------|-----------|
| zh | Chinese | 6436 | 3397 | 1114 | 1040 | 1243 | 3137 | 32.8% |
| ja | Japanese | 6436 | 4734 | 1390 | 1453 | 1891 | 1800 | 29.4% |
| th | Thai | 6436 | 5963 | 1714 | 2016 | 2233 | 571 | 28.7% |
| es | Spanish | 6436 | 6084 | 1386 | 1442 | 3256 | 450 | 22.8% |
| de | German | 6436 | 6054 | 1401 | 1435 | 3218 | 480 | 23.1% |
| fr | French | 6436 | 6027 | 1392 | 1399 | 3236 | 409 | 23.1% |
| pt | Portuguese | 6436 | 6019 | 1306 | 1322 | 3391 | 417 | 21.7% |
| ru | Russian | 6436 | 5978 | 1644 | 1873 | 2461 | 458 | 27.5% |
| ar | Arabic | 6436 | 5798 | 1498 | 1751 | 2549 | 638 | 25.8% |

## Grand total

- Total rows: 58414
- SUSPICIOUS (sim<0.65): **12845**
- review (sim 0.65-0.9): 13731
- ok (sim≥0.9): 23478
- no_score (text too short to score): 8360

## What this means

- **SUSPICIOUS = sim<0.65**: The translation, when round-tripped to English, doesn't match the source. Either the translation is **truncated** (e.g. the famous '对于大多数情侣来说，是的。' which drops the rest of the paragraph), **semantically off**, or **written about something else entirely** (the 'mamá passed away' vs '1985 photo came alive' case).

- **review = 0.65-0.9**: Borderline. Worth a native speaker's eye before publishing.

- **no_score = text too short**: Names, URLs, brand strings. These are not meaningful to score and don't need fixing.


## Top 10 most-suspicious per language (preview)


### zh (Chinese)
- sim=0.068 `index.p_text.mam_passed_away_two_months_before_our_w.79329689`
  - EN: When Mamá's 1985 photo came alive in our wedding film, our whole table burst into tears. The most beautiful tribute. Rea
  - ZH: “妈妈在我们结婚前两个月去世了。WeddingAI 激活了她 1985 年的结婚照——电影中她转过头，微笑着，向我们伸出手。当招待会上播放那个场景时，我们整桌人都泪流满面。这是最美的致敬。谢谢你让我再次与她在一起的那一刻。”
- sim=0.084 `terms.p_text.to_the_maximum_extent_permitted_by_law_w.36792107`
  - EN: To the maximum extent permitted by law, WeddingAI.video's total liability for any claim arising from or related to our s
  - ZH: 在法律允许的最大范围内，WeddingAI.video 对因我们的服务引起的或与我们的服务相关的任何索赔的全部责任不应超过您为相关特定项目支付的总金额。
- sim=0.135 `blog.wedding-video-vs-photos.p_text.for_most_couples_yes_a_wedding_videograp.44609454`
  - EN: For most couples, yes. A wedding videographer captures moments that photography alone can't — voices, movement, music, a
  - ZH: 对于大多数情侣来说，是的。
- sim=0.136 `blog.wedding-video-social-media.p_text.your_wedding_day_was_incredible_now_you.74114320`
  - EN: Your wedding day was incredible. Now you want the world to see it. But here's the problem: what works in a 5-minute high
  - ZH: 你的婚礼真是令人难以置信。
- sim=0.136 `blog.skip-wedding-videographer.p_text.yes_when_done_correctly_assign_dedicated.80318213`
  - EN: Yes, when done correctly. Assign dedicated filming guests, use modern smartphones, capture in 4K, and let WeddingAI.vide
  - ZH: 是的，如果做得正确的话。

### ja (Japanese)
- sim=0.011 `terms.p_text.upon_full_payment_you_receive_a_perpetua.45993907`
  - EN: Upon full payment, you receive a perpetual, non-exclusive license to use the final deliverables for personal, non-commer
  - JA: 全額お支払いいただくと、最終成果物を個人的、非営利目的 (家族との共有、個人のウェディング アルバムなどを含むソーシャル メディアへの投稿など) で使用するための永久的、非独占的ライセンスを受け取ります。
- sim=0.045 `blog.weddingai-video-review.p_text.if_you_can_afford_it_hire_a_skilled_vide.55856367`
  - EN: If you can afford it, hire a skilled videographer for the day-of coverage, then use WeddingAI.video for specialty servic
  - JA: 予算に余裕がある場合は、取材当日は熟練したビデオ撮影者を雇い、スローモーションの強化、家族への追悼、多言語字幕などの専門サービスには WeddingAI.video を使用してください。
- sim=0.051 `gallery.p_text.couple_picked_3_celebrity_personality_te.83130970`
  - EN: Couple picked 3 celebrity personality templates (charming leading man, witty comedian, glamorous leading lady) for diffe
  - JA: カップルは、結婚式のさまざまな部分 (オープナー、ケーキ入刀、不況の場面) に合わせて 3 つの有名人の性格テンプレート (魅力的な主役の男性、機知に富んだコメディアン、魅力的な主役の女性) を選びました。
- sim=0.062 `index.p_text.mam_passed_away_two_months_before_our_w.79329689`
  - EN: When Mamá's 1985 photo came alive in our wedding film, our whole table burst into tears. The most beautiful tribute. Rea
  - JA: 「ママは私たちの結婚式の2か月前に亡くなりました。WeddingAIは彼女の1985年の結婚式の写真をアクティベートしました。映画の中で彼女は顔を向け、微笑み、私たちに手を差し伸べました。披露宴でそのシーンが流れたとき、私たちのテーブル全体
- sim=0.069 `blog.raw-wedding-footage-ideas.p_text.even_if_your_wedding_didn_t_include_form.37275982`
  - EN: Even if your wedding didn't include formal memorials, raw footage often captures spontaneous moments of remembrance — a 
  - JA: たとえ結婚式に正式な追悼式が含まれていなかったとしても、生の映像には、おばあさんの椅子、行方不明者への乾杯、静かに物思いにふける瞬間など、自然発生的な思い出の瞬間が捉えられていることがよくあります。

### th (Thai)
- sim=0.025 `blog.cinematic-wedding-trailer-guide.p_text.absolutely_they_serve_different_purposes.61646505`
  - EN: Absolutely. They serve different purposes. Your full wedding video is a comprehensive record of the day — it's what you'
  - TH: อย่างแน่นอน. 
- sim=0.026 `blog.christmas-wedding-video.p_text.from_the_challenges_of_low_winter_light.63067737`
  - EN: From the challenges of low winter light to the opportunities of holiday décor and atmosphere, this guide covers everythi
  - TH: ตั้งแต่ความท้าทายเรื่องแสงน้อยในฤดูหนาวไปจนถึงโอกาสในการตกแต่งและบรรยากาศในช่วงวันหยุด คู่มือนี้ครอบคลุมทุกสิ่งที่คุณจำเ
- sim=0.028 `blog.elopement-video-ideas.p_text.absolutely_modern_smartphones_and_action.57465614`
  - EN: Absolutely. Modern smartphones and action cameras produce excellent video quality. Combined with a gimbal for stability,
  - TH: อย่างแน่นอน. 
- sim=0.031 `blog.honor-deceased-parent-wedding.p_text.absolutely_there_s_no_expiration_date_on.28296783`
  - EN: Absolutely. There's no expiration date on love or grief. Whether your parent passed away last year or 20 years ago, hono
  - TH: อย่างแน่นอน. 
- sim=0.032 `blog.cartoon-wedding-video.p_text.absolutely_hybrid_videos_that_blend_real.04988820`
  - EN: Absolutely. Hybrid videos that blend real footage with animated elements are some of the most visually striking wedding 
  - TH: อย่างแน่นอน. 

### es (Spanish)
- sim=0.015 `blog.include-remote-family-wedding-video.p_text.give_them_a_specific_role_reading_toast.14020412`
  - EN: Give them a specific role (reading, toast, or message), acknowledge them publicly during the ceremony or reception, assi
  - ES: Asígnales un rol específico (lectura, brindis o mensaje), reconócelos públicamente durante la ceremonia o recepción, asi
- sim=0.037 `index.p_text.mam_passed_away_two_months_before_our_w.79329689`
  - EN: When Mamá's 1985 photo came alive in our wedding film, our whole table burst into tears. The most beautiful tribute. Rea
  - ES: "Mamá falleció dos meses antes de nuestra boda. WeddingAI activó su foto de boda de 1985: giró la cabeza, sonrió y se ac
- sim=0.044 `resources.p_text.five_in_depth_guides_to_help_you_make_be.99867266`
  - EN: Five in-depth guides to help you make better decisions about your wedding video — from choosing a videographer to restor
  - ES: Cinco guías detalladas que lo ayudarán a tomar mejores decisiones sobre el video de su boda, desde elegir un camarógrafo
- sim=0.055 `blog.cinematic-wedding-trailer-guide.p_text.absolutely_they_serve_different_purposes.61646505`
  - EN: Absolutely. They serve different purposes. Your full wedding video is a comprehensive record of the day — it's what you'
  - ES: Absolutamente. 
- sim=0.062 `blog.restore-vhs-wedding-footage.strong_text.tracking_correction.11650968`
  - EN: Tracking correction
  - ES: Corrección de seguimiento

### de (German)
- sim=0.015 `blog.include-remote-family-wedding-video.p_text.give_them_a_specific_role_reading_toast.14020412`
  - EN: Give them a specific role (reading, toast, or message), acknowledge them publicly during the ceremony or reception, assi
  - DE: Weisen Sie ihnen eine bestimmte Rolle zu (Lesung, Trinkspruch oder Botschaft), würdigen Sie sie öffentlich während der Z
- sim=0.043 `blog.ai-wedding-video-industry.p_text.no_ai_is_transforming_the_tools_videogra.29714692`
  - EN: No. AI is transforming the tools videographers use, but the human elements of wedding videography — creative storytellin
  - DE: Nein. KI verändert die Werkzeuge, die Videofilmer verwenden, aber die menschlichen Elemente der Hochzeitsvideografie – k
- sim=0.065 `index.p_text.mam_passed_away_two_months_before_our_w.79329689`
  - EN: When Mamá's 1985 photo came alive in our wedding film, our whole table burst into tears. The most beautiful tribute. Rea
  - DE: „Mamá verstarb zwei Monate vor unserer Hochzeit. WeddingAI aktivierte ihr Hochzeitsfoto von 1985 – sie drehte im Film de
- sim=0.086 `blog.wedding-video-from-photos.p_text.yes_absolutely_modern_smartphone_photos.78432068`
  - EN: Yes, absolutely. Modern smartphone photos (from iPhones 12 and newer, Samsung Galaxy S21 and newer, Google Pixel 6 and n
  - DE: Ja, absolut. 
- sim=0.088 `blog.what-to-do-with-wedding-video.p_text.that_someday_is_now_your_wedding_video_i.59271512`
  - EN: That someday is now. Your wedding video is one of the most valuable keepsakes from your wedding day — and the longer you
  - DE: Das ist eines Tages jetzt. 

### fr (French)
- sim=0.005 `blog.wedding-video-subtitles.p_text.at_multicultural_weddings_it_s_common_fo.41684770`
  - EN: At multicultural weddings, it's common for speakers to switch languages mid-sentence or for different speakers to use di
  - FR: Lors des mariages multiculturels, il est courant que les locuteurs changent de langue au milieu d'une phrase ou que diff
- sim=0.047 `blog.how-long-should-wedding-video-be.p_text.not_at_all_a_10_minute_wedding_video_fal.91946677`
  - EN: Not at all. A 10-minute wedding video falls into the "short film" category and is ideal for couples who want more storyt
  - FR: Pas du tout. 
- sim=0.055 `blog.cinematic-wedding-trailer-guide.p_text.absolutely_they_serve_different_purposes.61646505`
  - EN: Absolutely. They serve different purposes. Your full wedding video is a comprehensive record of the day — it's what you'
  - FR: Absolument. 
- sim=0.059 `services.personalization.pet-wedding.p_text.not_at_all_we_use_your_existing_photos_o.14107911`
  - EN: Not at all. We use your existing photos. Our AI generates realistic pet movements and wedding scenarios — no pet acting 
  - FR: Pas du tout. 
- sim=0.062 `blog.elopement-video-ideas.p_text.absolutely_modern_smartphones_and_action.57465614`
  - EN: Absolutely. Modern smartphones and action cameras produce excellent video quality. Combined with a gimbal for stability,
  - FR: Absolument. 

### pt (Portuguese)
- sim=0.005 `blog.wedding-video-subtitles.p_text.at_multicultural_weddings_it_s_common_fo.41684770`
  - EN: At multicultural weddings, it's common for speakers to switch languages mid-sentence or for different speakers to use di
  - PT: Em casamentos multiculturais, é comum que os falantes troquem de idioma no meio da frase ou que diferentes falantes usem
- sim=0.047 `blog.how-long-should-wedding-video-be.p_text.not_at_all_a_10_minute_wedding_video_fal.91946677`
  - EN: Not at all. A 10-minute wedding video falls into the "short film" category and is ideal for couples who want more storyt
  - PT: De jeito nenhum. 
- sim=0.055 `blog.cinematic-wedding-trailer-guide.p_text.absolutely_they_serve_different_purposes.61646505`
  - EN: Absolutely. They serve different purposes. Your full wedding video is a comprehensive record of the day — it's what you'
  - PT: Absolutamente. 
- sim=0.059 `services.personalization.pet-wedding.p_text.not_at_all_we_use_your_existing_photos_o.14107911`
  - EN: Not at all. We use your existing photos. Our AI generates realistic pet movements and wedding scenarios — no pet acting 
  - PT: De jeito nenhum. 
- sim=0.060 `index.p_text.mam_passed_away_two_months_before_our_w.79329689`
  - EN: When Mamá's 1985 photo came alive in our wedding film, our whole table burst into tears. The most beautiful tribute. Rea
  - PT: "Mamá faleceu dois meses antes do nosso casamento. WeddingAI ativou sua foto de casamento de 1985 - ela virou a cabeça, 

### ru (Russian)
- sim=0.014 `blog.christmas-wedding-video.p_text.from_the_challenges_of_low_winter_light.63067737`
  - EN: From the challenges of low winter light to the opportunities of holiday décor and atmosphere, this guide covers everythi
  - RU: Это руководство охватывает все, что вам нужно знать о создании потрясающего рождественского свадебного видео, которое бу
- sim=0.043 `blog.ai-wedding-video-industry.p_text.no_ai_is_transforming_the_tools_videogra.29714692`
  - EN: No. AI is transforming the tools videographers use, but the human elements of wedding videography — creative storytellin
  - RU: Нет. ИИ меняет инструменты, которые используют видеооператоры, но человеческие элементы свадебной видеосъемки — творческ
- sim=0.049 `blog.what-to-do-with-wedding-video.p_text.that_someday_is_now_your_wedding_video_i.59271512`
  - EN: That someday is now. Your wedding video is one of the most valuable keepsakes from your wedding day — and the longer you
  - RU: Это когда-нибудь произойдет сейчас. 
- sim=0.062 `index.p_text.mam_passed_away_two_months_before_our_w.79329689`
  - EN: When Mamá's 1985 photo came alive in our wedding film, our whole table burst into tears. The most beautiful tribute. Rea
  - RU: «Мама скончалась за два месяца до нашей свадьбы. WeddingAI активировала свою свадебную фотографию 1985 года — она поверн
- sim=0.072 `blog.restore-vhs-wedding-footage.p_text.the_good_news_restoring_old_wedding_vide.89150426`
  - EN: The good news? Restoring old wedding videos has never been more accessible or affordable. Whether your footage lives on 
  - RU: Хорошие новости? 

### ar (Arabic)
- sim=0.040 `index.p_text.mam_passed_away_two_months_before_our_w.79329689`
  - EN: When Mamá's 1985 photo came alive in our wedding film, our whole table burst into tears. The most beautiful tribute. Rea
  - AR: "توفيت ماما قبل شهرين من حفل زفافنا. قامت شركة WeddingAI بتنشيط صورة زفافها عام 1985 - أدارت رأسها وابتسمت ومدت يدها نحو
- sim=0.050 `blog.wedding-video-gift-ideas.p_text.unlike_a_highlight_reel_that_jumps_betwe.80293208`
  - EN: Unlike a highlight reel that jumps between the best moments, a documentary includes the full narrative: the morning prep
  - AR: على عكس اللقطات المميزة التي تتنقل بين أفضل اللحظات، يتضمن الفيلم الوثائقي السرد الكامل: الاستعدادات الصباحية، والطاقة ا
- sim=0.072 `gallery.p_text.couple_picked_3_celebrity_personality_te.83130970`
  - EN: Couple picked 3 celebrity personality templates (charming leading man, witty comedian, glamorous leading lady) for diffe
  - AR: اختار الزوجان 3 نماذج لشخصيات المشاهير (الرجل الرائد الساحر، الممثل الكوميدي الذكي، السيدة الرائدة الفاتنة) لأجزاء مختلف
- sim=0.075 `blog.wedding-video-from-photos.p_text.yes_absolutely_modern_smartphone_photos.78432068`
  - EN: Yes, absolutely. Modern smartphone photos (from iPhones 12 and newer, Samsung Galaxy S21 and newer, Google Pixel 6 and n
  - AR: نعم بالتأكيد. 
- sim=0.086 `blog.digitize-parents-wedding-video.p_text.enhancement_is_good_over_enhancement_is.93388488`
  - EN: Enhancement is good. Over-enhancement is bad. Excessive noise reduction creates a waxy, artificial look. Too much sharpe
  - AR: التعزيز جيد. 

## What was done about it

See `qa/REPORT_I18N_ZH_FIX.md` for the zh fix report (V1 single-sample, V2 N=3 stable, with rollback).
Other 8 languages can be fixed with the same pipeline: `qa/fix_lang.py --lang <code>`.

