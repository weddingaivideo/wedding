# i18n Translation Audit — 2026-07-28

**Auditor:** Mavis (static analysis, no native-speaker review)  
**Scope:** 9 non-EN languages × 6534 source keys  
**Translator (declared in `_meta`):** Google Translate (machine) for all 9 langs


## TL;DR — 关键问题

1. **Google 机器翻译对长文本有内部截断** — 所有 9 个语言都受影响。
   标尺: EN ≥ 100 字符 且译文比率 < 0.20。

2. **EN 缺 2 个键** — `_meta` 和 `index.p_text.the_real_time_editing_at_our_reception.87089643`
   后者在所有 9 个非EN语言里有完整翻译，但 EN 是 source 反而空。

3. **覆盖率 100%**（没有 missing 键，没有占位符错位，没有空值）— 但**翻译完整性很差**。

4. **专有名词处理**：15 个键保持原文（产品名/邮箱），是正确行为。


## 各语言严重截断数（高优先级）

| lang | name | severe_truncation | total_findings | trunc% |
|------|------|-------------------|----------------|--------|
| zh | Chinese | **1121** | 3415 | 33% |
| ja | Japanese | **766** | 1494 | 51% |
| th | Thai | **309** | 622 | 50% |
| es | Spanish | **225** | 450 | 50% |
| de | German | **218** | 434 | 50% |
| fr | French | **210** | 413 | 51% |
| pt | Portuguese | **231** | 468 | 49% |
| ru | Russian | **247** | 494 | 50% |
| ar | Arabic | **342** | 627 | 55% |

## 各语言全部 findings 分类

| lang | missing | untranslated | too_short | en_leak | empty | extra |
|------|---------|--------------|-----------|---------|-------|-------|
| zh | 0 | 2 | 3403 | 9 | 0 | 1 |
| ja | 0 | 9 | 1478 | 6 | 0 | 1 |
| th | 0 | 3 | 597 | 21 | 0 | 1 |
| es | 0 | 2 | 447 | 0 | 0 | 1 |
| de | 0 | 16 | 417 | 0 | 0 | 1 |
| fr | 0 | 6 | 406 | 0 | 0 | 1 |
| pt | 0 | 2 | 465 | 0 | 0 | 1 |
| ru | 0 | 5 | 479 | 9 | 0 | 1 |
| ar | 0 | 2 | 619 | 5 | 0 | 1 |

## 严重截断的典型例子（每个语言挑 3 个）


### zh (Chinese) — 1121 个严重截断

- **`about.p_text.always_every_inquiry_is_answered_by_sofi.60797813`** (ratio 0.01)
  - EN: Always. Every inquiry is answered by Sofia, our Client Experience Manager, within 24 hours. For larger projects we can also schedule a 30-minute video call to w
  - ZH: 总是。
- **`about.p_text.two_rounds_of_revisions_are_included_wit.63698545`** (ratio 0.07)
  - EN: Two rounds of revisions are included with every service at no extra cost. If after revisions you're still not satisfied, we offer a full refund — no questions a
  - ZH: 每项服务均包含两轮修订，无需额外费用。
- **`about.p_text.two_rounds_of_revisions_are_included_wit.93522521`** (ratio 0.07)
  - EN: Two rounds of revisions are included with every service at no extra cost. If after revisions you're still not satisfied, we offer a full refund — no questions a
  - ZH: 每项服务均包含两轮修订，无需额外费用。

### ja (Japanese) — 766 个严重截断

- **`about.p_text.always_every_inquiry_is_answered_by_sofi.60797813`** (ratio 0.02)
  - EN: Always. Every inquiry is answered by Sofia, our Client Experience Manager, within 24 hours. For larger projects we can also schedule a 30-minute video call to w
  - JA: いつも。
- **`about.p_text.two_rounds_of_revisions_are_included_wit.63698545`** (ratio 0.11)
  - EN: Two rounds of revisions are included with every service at no extra cost. If after revisions you're still not satisfied, we offer a full refund — no questions a
  - JA: 各サービスには 2 回の修正が追加料金なしで含まれています。
- **`about.p_text.two_rounds_of_revisions_are_included_wit.93522521`** (ratio 0.11)
  - EN: Two rounds of revisions are included with every service at no extra cost. If after revisions you're still not satisfied, we offer a full refund — no questions a
  - JA: 各サービスには 2 回の修正が追加料金なしで含まれています。

### th (Thai) — 309 个严重截断

- **`about.p_text.always_every_inquiry_is_answered_by_sofi.60797813`** (ratio 0.03)
  - EN: Always. Every inquiry is answered by Sofia, our Client Experience Manager, within 24 hours. For larger projects we can also schedule a 30-minute video call to w
  - TH: เสมอ. 
- **`about.p_text.we_re_not_a_traditional_wedding_videogra.85987715`** (ratio 0.16)
  - EN: We're not a traditional wedding videography studio. We don't shoot weddings — we work with what you (or your guests) already filmed, and we use AI to make it un
  - TH: เราไม่ใช่สตูดิโอถ่ายวิดีโองานแต่งงานแบบดั้งเดิม 
- **`blog.restore-vhs-wedding-footage.p_text.absolutely_dvds_are_also_aging_disc_rot.59754416`** (ratio 0.05)
  - EN: Absolutely. DVDs are also aging (disc rot is real), and the quality of a VHS-to-DVD transfer done years ago was likely poor. Starting fresh from the original ta
  - TH: อย่างแน่นอน. 

### es (Spanish) — 225 个严重截断

- **`about.p_text.always_every_inquiry_is_answered_by_sofi.60797813`** (ratio 0.04)
  - EN: Always. Every inquiry is answered by Sofia, our Client Experience Manager, within 24 hours. For larger projects we can also schedule a 30-minute video call to w
  - ES: Siempre. 
- **`about.p_text.we_re_not_a_traditional_wedding_videogra.85987715`** (ratio 0.19)
  - EN: We're not a traditional wedding videography studio. We don't shoot weddings — we work with what you (or your guests) already filmed, and we use AI to make it un
  - ES: No somos un estudio de videografía de bodas tradicional. 
- **`blog.restore-vhs-wedding-footage.p_text.absolutely_dvds_are_also_aging_disc_rot.59754416`** (ratio 0.06)
  - EN: Absolutely. DVDs are also aging (disc rot is real), and the quality of a VHS-to-DVD transfer done years ago was likely poor. Starting fresh from the original ta
  - ES: Absolutamente. 

### de (German) — 218 个严重截断

- **`about.p_text.always_every_inquiry_is_answered_by_sofi.60797813`** (ratio 0.03)
  - EN: Always. Every inquiry is answered by Sofia, our Client Experience Manager, within 24 hours. For larger projects we can also schedule a 30-minute video call to w
  - DE: Stets. 
- **`about.p_text.we_re_not_a_traditional_wedding_videogra.85987715`** (ratio 0.17)
  - EN: We're not a traditional wedding videography studio. We don't shoot weddings — we work with what you (or your guests) already filmed, and we use AI to make it un
  - DE: Wir sind kein traditionelles Hochzeitsvideostudio. 
- **`blog.restore-vhs-wedding-footage.p_text.absolutely_dvds_are_also_aging_disc_rot.59754416`** (ratio 0.04)
  - EN: Absolutely. DVDs are also aging (disc rot is real), and the quality of a VHS-to-DVD transfer done years ago was likely poor. Starting fresh from the original ta
  - DE: Absolut. 

### fr (French) — 210 个严重截断

- **`about.p_text.always_every_inquiry_is_answered_by_sofi.60797813`** (ratio 0.05)
  - EN: Always. Every inquiry is answered by Sofia, our Client Experience Manager, within 24 hours. For larger projects we can also schedule a 30-minute video call to w
  - FR: Toujours. 
- **`blog.restore-vhs-wedding-footage.p_text.absolutely_dvds_are_also_aging_disc_rot.59754416`** (ratio 0.05)
  - EN: Absolutely. DVDs are also aging (disc rot is real), and the quality of a VHS-to-DVD transfer done years ago was likely poor. Starting fresh from the original ta
  - FR: Absolument. 
- **`blog.restore-vhs-wedding-footage.p_text.in_many_cases_yes_moldy_tapes_require_pr.17217270`** (ratio 0.09)
  - EN: In many cases, yes. Moldy tapes require professional cleaning before playback, which involves carefully removing mold and treating the tape surface. However, if
  - FR: Dans de nombreux cas, oui. 

### pt (Portuguese) — 231 个严重截断

- **`about.p_text.always_every_inquiry_is_answered_by_sofi.60797813`** (ratio 0.04)
  - EN: Always. Every inquiry is answered by Sofia, our Client Experience Manager, within 24 hours. For larger projects we can also schedule a 30-minute video call to w
  - PT: Sempre. 
- **`blog.restore-vhs-wedding-footage.p_text.absolutely_dvds_are_also_aging_disc_rot.59754416`** (ratio 0.06)
  - EN: Absolutely. DVDs are also aging (disc rot is real), and the quality of a VHS-to-DVD transfer done years ago was likely poor. Starting fresh from the original ta
  - PT: Absolutamente. 
- **`blog.restore-vhs-wedding-footage.p_text.in_many_cases_yes_moldy_tapes_require_pr.17217270`** (ratio 0.08)
  - EN: In many cases, yes. Moldy tapes require professional cleaning before playback, which involves carefully removing mold and treating the tape surface. However, if
  - PT: Em muitos casos, sim. 

### ru (Russian) — 247 个严重截断

- **`about.p_text.always_every_inquiry_is_answered_by_sofi.60797813`** (ratio 0.04)
  - EN: Always. Every inquiry is answered by Sofia, our Client Experience Manager, within 24 hours. For larger projects we can also schedule a 30-minute video call to w
  - RU: Всегда. 
- **`about.p_text.we_re_not_a_traditional_wedding_videogra.85987715`** (ratio 0.16)
  - EN: We're not a traditional wedding videography studio. We don't shoot weddings — we work with what you (or your guests) already filmed, and we use AI to make it un
  - RU: Мы не традиционная студия свадебной видеосъемки. 
- **`blog.restore-vhs-wedding-footage.p_text.absolutely_dvds_are_also_aging_disc_rot.59754416`** (ratio 0.04)
  - EN: Absolutely. DVDs are also aging (disc rot is real), and the quality of a VHS-to-DVD transfer done years ago was likely poor. Starting fresh from the original ta
  - RU: Абсолютно. 

### ar (Arabic) — 342 个严重截断

- **`about.p_text.always_every_inquiry_is_answered_by_sofi.60797813`** (ratio 0.04)
  - EN: Always. Every inquiry is answered by Sofia, our Client Experience Manager, within 24 hours. For larger projects we can also schedule a 30-minute video call to w
  - AR: دائماً. 
- **`about.p_text.we_don_t_replace_human_creativity_we_amp.98136523`** (ratio 0.19)
  - EN: We don't replace human creativity. We amplify it. Every project is reviewed by a professional editor before delivery, and we're not happy until you're happy.
  - AR: نحن لا نستبدل الإبداع البشري. 
- **`about.p_text.we_re_not_a_traditional_wedding_videogra.85987715`** (ratio 0.14)
  - EN: We're not a traditional wedding videography studio. We don't shoot weddings — we work with what you (or your guests) already filmed, and we use AI to make it un
  - AR: نحن لسنا استوديو تصوير فيديو زفاف تقليدي. 

## 未翻译 (untranslated) — 完整列表


### zh (2 个)
- `blog.wedding-video-audio-fix.h3_text.final_cut_pro_logic_pro.78403515` — `Final Cut Pro / Logic Pro`
- `order.input_placeholder.https_drive_google_com.53310346` — `https://drive.google.com/...`

### ja (9 个)
- `404.a_text.order_weddingai_video.05724559` — `order@weddingai.video`
- `blog.wedding-video-formats.h3_text.mov_apple_quicktime.60582527` — `MOV (Apple QuickTime)`
- `order.input_placeholder.https_drive_google_com.53310346` — `https://drive.google.com/...`
- `resources.strong_text.minidv_hi8_1995_2010.63001487` — `MiniDV / Hi8 (1995-2010):`
- `resources.strong_text.slow_motion_from_standard_footage.62797554` — `Slow motion from standard footage.`
- `resources.strong_text.vhs_to_digital_just_digitization_no_rest.63389045` — `VHS to digital (just digitization, no restoration):`
- `resources.strong_text.vhs_vhs_c_1976_2005.74475766` — `VHS / VHS-C (1976-2005):`
- `resources.strong_text.what_happens_if_your_camera_fails_mid_c.89666785` — `"What happens if your camera fails mid-ceremony?"`
- `resources.strong_text.what_s_included_in_the_package_exactly.28221293` — `"What's included in the package, exactly?"`

### th (3 个)
- `404.a_text.order_weddingai_video.05724559` — `order@weddingai.video`
- `blog.cinematic-wedding-trailer-guide.strong_text.instagram_reels_tiktok.09208013` — `Instagram Reels/TikTok:`
- `order.input_placeholder.https_drive_google_com.53310346` — `https://drive.google.com/...`

### es (2 个)
- `blog.wedding-video-formats.h3_text.mov_apple_quicktime.60582527` — `MOV (Apple QuickTime)`
- `order.input_placeholder.https_drive_google_com.53310346` — `https://drive.google.com/...`

### de (16 个)
- `404.a_text.order_weddingai_video.05724559` — `order@weddingai.video`
- `about.p_text.client_experience_manager.88913259` — `Client Experience Manager`
- `blog.ai-wedding-video-generator-guide.a_text.mit_technology_review.11057944` — `MIT Technology Review`
- `blog.wedding-slow-motion-effect.h3_text.option_3_mobile_apps.01296943` — `Option 3: Mobile Apps`
- `blog.wedding-video-formats.h3_text.mov_apple_quicktime.60582527` — `MOV (Apple QuickTime)`
- `blog.wedding-video-audio-fix.h3_text.davinci_resolve_fairlight_audio.24766982` — `DaVinci Resolve (Fairlight Audio)`
- `blog.wedding-video-audio-fix.h3_text.final_cut_pro_logic_pro.78403515` — `Final Cut Pro / Logic Pro`
- `blog.weddingai-success-stories.a_text.harvard_business_review.80220392` — `Harvard Business Review`
- `gallery.p_text.chicago_il_september_2024.87132352` — `Chicago, IL · September 2024`
- `gallery.p_text.columbus_oh_september_2024.54308434` — `Columbus, OH · September 2024`
- `gallery.p_text.kyoto_japan_april_2024.25065229` — `Kyoto, Japan · April 2024`
- `gallery.p_text.seattle_wa_april_2024.14579978` — `Seattle, WA · April 2024`
- `order.input_placeholder.https_drive_google_com.53310346` — `https://drive.google.com/...`
- `resources.strong_text.8mm_super_8_1965_1990.37749110` — `8mm / Super 8 (1965-1990):`
- `resources.strong_text.minidv_hi8_1995_2010.63001487` — `MiniDV / Hi8 (1995-2010):`
- `resources.strong_text.vhs_vhs_c_1976_2005.74475766` — `VHS / VHS-C (1976-2005):`

### fr (6 个)
- `blog.restore-vhs-wedding-footage.h3_text.film_super_8_regular_8.54596419` — `Film (Super 8, Regular 8)`
- `blog.wedding-video-formats.h3_text.mov_apple_quicktime.60582527` — `MOV (Apple QuickTime)`
- `blog.wedding-photo-slideshow.strong_text.apple_photos_imovie.97055344` — `Apple Photos (iMovie)`
- `blog.wedding-video-audio-fix.h3_text.davinci_resolve_fairlight_audio.24766982` — `DaVinci Resolve (Fairlight Audio)`
- `blog.wedding-video-audio-fix.h3_text.final_cut_pro_logic_pro.78403515` — `Final Cut Pro / Logic Pro`
- `order.input_placeholder.https_drive_google_com.53310346` — `https://drive.google.com/...`

### pt (2 个)
- `blog.wedding-video-formats.h3_text.mov_apple_quicktime.60582527` — `MOV (Apple QuickTime)`
- `order.input_placeholder.https_drive_google_com.53310346` — `https://drive.google.com/...`

### ru (5 个)
- `404.a_text.order_weddingai_video.05724559` — `order@weddingai.video`
- `blog.wedding-video-formats.h3_text.mov_apple_quicktime.60582527` — `MOV (Apple QuickTime)`
- `blog.wedding-photo-slideshow.strong_text.apple_photos_imovie.97055344` — `Apple Photos (iMovie)`
- `blog.wedding-video-audio-fix.h3_text.davinci_resolve_fairlight_audio.24766982` — `DaVinci Resolve (Fairlight Audio)`
- `order.input_placeholder.https_drive_google_com.53310346` — `https://drive.google.com/...`

### ar (2 个)
- `404.a_text.order_weddingai_video.05724559` — `order@weddingai.video`
- `order.input_placeholder.https_drive_google_com.53310346` — `https://drive.google.com/...`

## 目标语言多出但 EN 没有的键


### zh (1 个)
- `index.p_text.the_real_time_editing_at_our_reception.87089643` — `“我们接待处的实时编辑改变了游戏规则。我们的客人不停地谈论实时评论屏幕。每一分钱都值得。”`

### ja (1 个)
- `index.p_text.the_real_time_editing_at_our_reception.87089643` — `「レセプションでのリアルタイム編集は状況を大きく変えるものでした。ゲストはライブ コメント画面について話が止まりませんでした。その価値はありました。」`

### th (1 个)
- `index.p_text.the_real_time_editing_at_our_reception.87089643` — `"การแก้ไขแบบเรียลไทม์ที่แผนกต้อนรับส่วนหน้าของเราเป็นตัวเปลี่ยนเกม แขกของเราไม่สามารถหยุดพูดถึงหน้าจอแสดงความคิดเห็นได้ `

### es (1 个)
- `index.p_text.the_real_time_editing_at_our_reception.87089643` — `"La edición en tiempo real en nuestra recepción cambió las reglas del juego. Nuestros invitados no podían dejar de habla`

### de (1 个)
- `index.p_text.the_real_time_editing_at_our_reception.87089643` — `„Die Echtzeitbearbeitung an unserem Empfang hat das Spiel verändert. Unsere Gäste konnten nicht aufhören, über den Live-`

### fr (1 个)
- `index.p_text.the_real_time_editing_at_our_reception.87089643` — `"Le montage en temps réel lors de notre réception a changé la donne. Nos invités ne pouvaient s'empêcher de parler de l'`

### pt (1 个)
- `index.p_text.the_real_time_editing_at_our_reception.87089643` — `"A edição em tempo real em nossa recepção foi uma virada de jogo. Nossos convidados não paravam de falar sobre a tela de`

### ru (1 个)
- `index.p_text.the_real_time_editing_at_our_reception.87089643` — `«Монтаж в реальном времени на нашем приеме изменил правила игры. Наши гости не могли перестать говорить об экране живых `

### ar (1 个)
- `index.p_text.the_real_time_editing_at_our_reception.87089643` — `"لقد أحدث التحرير في الوقت الفعلي في مكتب الاستقبال لدينا تغييرًا جذريًا. لم يستطع ضيوفنا التوقف عن الحديث عن شاشة التعل`

## EN (source) 缺键

- `_meta` (其他 9 个语言都有)
- `index.p_text.the_real_time_editing_at_our_reception.87089643` — 这是 EN 自己的 bug；其他 9 个语言都有完整翻译

## 建议下一步（待用户决定）

**选项 A — 报告到此为止**：你已经看到完整问题清单，自己决定是否投入修复。

**选项 B — 重译严重截断的键**：用百度翻译 API 重新翻译所有 `severe_truncation` 项。
  - 估算：~3669 个键 × 9 语言重译
  - 需要：百度翻译 appid（用户给了密钥 `yoUb_...`，但缺 appid）

**选项 C — 全量重译**：所有 9 语言用百度 API 重新翻译全部 6536 键。
  - 估算：~59000 次 API 调用，免费版 QPS=1 约 16 小时
  - 风险：覆盖原本就翻译好的 100% 覆盖内容，可能引入新 bug

**选项 D — 先跑全量反向翻译审查**：用百度 API 把每条翻译翻回英文，对比 EN 原文相似度，
  找出真正『语义偏移』或『漏译』的键。这比单纯长度比对更精确。
  - 同样需要 appid

**选项 E — 修 EN 自身的 2 个 bug**：硬编码缺失的 2 个键到 HTML 或 EN 字典。

