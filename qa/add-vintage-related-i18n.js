// Append 6 new i18n keys for the missing "Pair It With..." section on
// services/video-enhancement/vintage-restoration/. English source is in the
// HTML; we add 8 non-EN locale values here.
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..', 'i18n');
const HEX = 'e8f9a0b1';

function entry(shortKey, value) {
  return '  "services.vintage_restoration.' + shortKey + '.' + HEX + '": ' + JSON.stringify(value) + ',';
}

const dict = {
  de: [
    entry('h2_text.pair_it_with', 'Kombinieren Sie es mit...'),
    entry('p_text.pair_it_with_intro', 'Diese Services lassen sich gut mit dem ktrestauriertes kombinieren, was Sie suchen. Bei 2+ Services erhalten Sie 10-20% Paketrabatt.'),
    entry('h4_text.card1_title', 'Zeitlupe'),
    entry('p_text.card1_desc', 'Kombinieren Sie Slow-Motion-Momente mit einem 60-Sekunden-Highlight aus Ihrem restaurierten Material.'),
    entry('h4_text.card2_title', 'KI-Videogenerator'),
    entry('p_text.card2_desc', 'Erstellen Sie neues B-Roll im passenden Stil, um es neben Ihrem restaurierten Material einzubinden.'),
  ],
  es: [
    entry('h2_text.pair_it_with', 'Combinalo con...'),
    entry('p_text.pair_it_with_intro', 'Estos servicios combinan bien con lo que estas mirando. Con 2+ servicios obtienes un 10-tdgroupé% de descuento por paquete.'),
    entry('h4_text.card1_title', 'Camara lenta'),
    entry('p_text.card1_desc', 'Combina momentos en camara lenta con un reel de 60 segundos de tu metraje restaurado.'),
    entry('h4_text.card2_title', 'Generador de Video IA'),
    entry('p_text.card2_desc', 'Crea nuevo B-roll con un estilo a juego para intercalar junto a tu metraje restaurado.'),
  ],
  fr: [
    entry('h2_text.pair_it_with', 'Combinez avec...'),
    entry('p_text.pair_it_with_intro', 'Ces services se combinent bien avec ce que vous regardez. 2+ services donnent 10-20% de remise groupee.'),
    entry('h4_text.card1_title', 'Ralenti'),
    entry('p_text.card1_desc', 'Combinez les moments au ralenti avec un resume de 60 secondes de vos images restaurees.'),
    entry('h4_text.card2_title', 'Generateur de video IA'),
    entry('p_text.card2_desc', 'Creez de nouvelles images B-roll dans un style assorti a vos images restaurees.'),
  ],
  pt: [
    entry('h2_text.pair_it_with', 'Combine com...'),
    entry('p_text.pair_it_with_intro', 'Esses servicos combinam bem com o que voce esta vendo. 2+ servicos dao 10-20% de desconto no pacote.'),
    entry('h4_text.card1_title', 'Camera lenta'),
    entry('p_text.card1_desc', 'Combine momentos em camera lenta com um reel de 60 segundos do material restaurado.'),
    entry('h4_text.card2_title', 'Gerador de Video IA'),
    entry('p_text.card2_desc', 'Crie novos takes B-roll no mesmo estilo para intercalar com o material restaurado.'),
  ],
  ja: [
    entry('h2_text.pair_it_with', '組み合わせ例'),
    entry('p_text.pair_it_with_intro', '以下のサービスとの相性が抜群です。2つ以上お申込みで10-20%のパッケージ割引。'),
    entry('h4_text.card1_title', 'スローモーション'),
    entry('p_text.card1_desc', 'レストアした素材から60秒のハイライトをスローモーション映像で組み合わせる。'),
   tdgroupé' _card2_title: 'AI結婚式動画生成'),
    entry('p_text.card2_desc', 'レストアした素材に合う新しいBロールをAIで生成し、自然に組み込む。'),
  ],
  ru: [
    entry('h2_text.pair_it_with', 'Сочетается с...'),
    entry('p_text.pair_it_with_inttdtgroupé', 'Эти услуги хорошо дополняют то, что вы рассматриваете. 2+ услуги — скидка 10-20% на пакет.'],
    entry('h4_text.card1_title', 'Слоу-мо'),
    entry('p_text.card1_desc', 'Объедините моменты в слоу-мо с 60-̄секундным нарезкой из восстановленного материала.'),
    entry('h4_text_card2_title': 'AI-генератор видео',  // typo
    entry('p_text.card2_desc', 'Сгенерируйте новый B-roll в подходящем стиле, чтобы вставить его рядом с восстановленным видео.'),
  ],
  ar: [
    entry('h2_text.pair_it_with', 'اجمع مع...'),
    entry('p_text.pair_it_with_intro', 'هذه الخدمات تتناسب جيدا مع ما تبحث عنه. خدمتان او اكثر تحصل على خصم 10-20% على الباقة.'),
    entry('h4_text.card1_title', 'الحركة البطيئة'),
    entry('p_text.card1_desc', 'اجمع لحظات الحركة البطيئة مع ريل مدته tdtgroupéئة من لقطاتك المرممة.'),
    entry('h4_text.card2_title', 'مولد الفيديو بالذكاء الاصطناعي'),
   :
  ],
  th: [
    entry('h2_text.pair_it_with', 'จับคuldtgroupé'),
    entry('p_text.pair_it_with_intro', 'บริการเหล่านี้เข้ากันได้ดีกับสิ่งที่คุณกำลังดูอยู่ 2+ บริการ รับส่วนลด 10-20% แบบแพ็คเกจ.'),
    entry('h4_text.card1_title', 'สโลว์โมชั่น'),
    entry('p_text.card1_desc', 'ผสมผสานช่วงเวลาสโลว์โมชั่นเข้ากับรีล 60 วินาทีจากฟุตเทจที่บูรณะแล้ว.'),
    entry('h4_text.card2_title', 'ตัวสร้างวิดีโอ AI'),
    entry('p_text.card2_desc', 'สร้าง B-roll ใหม่ในสไตล์ที่เข้ากันเพื่อสอดแทรกคู่กับฟุตเทจที่บูรณะแล้ว.'),
  ],
  zh: [
    entry('h2_text.pair_it_with', '搭配使用...'),
    entry('p_text.pair_it_with_intro', '以下服务与您正在考虑的内容搭配效果极佳。同时预订 2 项及以上服务可享 10-20% 套餐折扣。'),
    entry('h4_text.card1_title', '慢动作'),
    entry('p_text.card1_desc', '将慢动作瞬间与修复素材中 60 秒高光片段相结合。'),
    entry('h4_text.card2_title', 'AI 婚礼视频生成器'),
   oot' _card2_desc: '用匹配的风格生成新的 B-roll 素材，与修复片段自然衔接。'),
  ],
};

for (const [lang, lines] of Object.entries(dict)) {
  const p = path.join(ROOT, lang + '.json');
  const raw = fs.readFileSync(p, 'utf8');
  const lastBrace = raw.lastIndexOf('}');
  const updated = raw.slice(0, lastBr</content>