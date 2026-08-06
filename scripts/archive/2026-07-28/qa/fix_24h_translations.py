import json
from pathlib import Path

ROOT = Path(r'C:\Users\qiaoshan\.openclaw\workspace\weddingai')
key = 'order.p_text.we_ll_respond_within_24_hours_check_your.67979247'

# Translations: "We'll respond within 24 hours. Check your spam folder if you don't hear from us."
translations = {
    'zh': '我们将在 24 小时内回复。如果您没有收到消息，请检查垃圾邮件文件夹。',
    'ja': '24時間以内に返信いたします。もし連絡がない場合は、迷惑メールフォルダをご確認ください。',
    'es': 'Responderemos dentro de las 24 horas. Revisa tu carpeta de spam si no recibes noticias nuestras.',
    'fr': 'Nous vous répondrons dans les 24 heures. Vérifiez votre dossier de courrier indésirable si vous n\'avez pas de nouvelles.',
    'de': 'Wir antworten innerhalb von 24 Stunden. Überprüfe deinen Spam-Ordner, falls du nichts von uns hörst.',
    'pt': 'Responderemos dentro de 24 horas. Verifique sua pasta de spam se não receber retorno.',
    'ru': 'Мы ответим в течение 24 часов. Проверьте папку со спамом, если не получите от нас сообщение.',
    'ar': 'سنرد خلال 24 ساعة. تحقق من مجلد البريد العشوائي إذا لم تسمع منا.',
    'th': 'เราจะตอบกลับภายใน 24 ชั่วโมง หากไม่ได้รับการติดต่อ กรุณาตรวจสอบโฟลเดอร์สแปม',
}

for lang, value in translations.items():
    path = ROOT / 'i18n' / f'{lang}.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    data[key] = value
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{lang}: updated')
