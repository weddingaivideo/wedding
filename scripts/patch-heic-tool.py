#!/usr/bin/env python3
"""
Make the HEIC tool work in every browser, and stop claiming it only works
in Safari.

WHY THIS EXISTS (found 2026-11-09)
--------------------------------
1. THE TOOL WAS DEAD OUTSIDE SAFARI. The page decoded HEIC with the
   browser's own <img> decoder. Safari 17+ ships one; Chrome, Edge and
   Firefox do not. On those browsers every file failed with "your browser
   can't decode HEIC", i.e. the tool only ever worked for Apple users.

2. THE PAGE SAID SO, IN ELEVEN LANGUAGES. The intro, the "Browser support"
   box, the privacy note, two "how it works" paragraphs, the first how-to
   step and two FAQ answers all said the tool needs Safari. One paragraph
   even explained that we deliberately did NOT add the heic2any library
   because "every CDN we'd add would require editing the site's Content
   Security Policy - a change we don't want to make for a single tool".
   We have now made exactly that change, so that paragraph was not just
   wrong, it was describing a decision we reversed.

THE FIX
-------
* The decoder: heic2any (MIT, 1.3 MB, asm.js - no WebAssembly, so it needs
  no 'wasm-unsafe-eval') is vendored under /js/vendor/heic2any/ and loaded
  lazily by js/tools/common.js (decodeHeic). The native path is tried FIRST,
  so Safari never downloads the decoder; Chrome/Edge/Firefox fall back to it.
* The resize: pica (MIT) does the downscale instead of the browser's
  bilinear drawImage, so a 12 MP HEIC downscaled to 1600 px stays sharp.
* The prose: all eight Safari-specific blocks are rewritten in the English
  source AND in all ten localized copies, in each language. They are not
  data-i18n bound (they never were), so they are edited in place - the same
  structure the file already had.
* The JSON-LD: the SoftwareApplication's browserRequirements and the HowTo
  step 1 still advertised Safari 17+. Both are rewritten per language by
  parsing the JSON-LD and patching the objects, so no string matching on
  translated text is needed.

The inline JavaScript is changed in the ENGLISH SOURCE only; the localized
copies receive it through scripts/propagate-tool-js.py, which makes the
English page the single source of truth for behaviour.

Usage:  python scripts/patch-heic-tool.py [--dry-run]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th", "hi"]
SLUG = "heic-to-jpg-wedding-photos"

# ---------------------------------------------------------------------------
# 1. The eight prose blocks, in the order they appear in the document.
#    Every one of them contains the word "Safari" in every language, which
#    is how the script finds them - no fragile per-language anchors.
# ---------------------------------------------------------------------------

PROSE = {
    "en": [
        "<p>Convert iPhone HEIC wedding photos to JPG in your browser. Batch-friendly, quality preserved "
        "— and it now works in Chrome, Edge, Firefox and Safari alike.</p>",
        "<p><strong>Browser support:</strong> every current browser works. Safari uses its built-in HEIC "
        "decoder; Chrome, Edge and Firefox load a small self-hosted decoder (about 1.3 MB) the first time "
        "you convert. Nothing is uploaded either way.</p>",
        "<p><strong>Privacy:</strong> every photo is decoded and re-encoded locally in your browser tab. "
        "We do not upload, store, or log your wedding photos — the page never makes a network request "
        "with image data.</p>",
        "<p>So the conversion runs entirely in your browser. Safari decodes HEIC with its built-in image "
        "decoder; Chrome, Edge and Firefox load a self-hosted decoder that runs locally — no CDN, no "
        "upload, no account.</p>",
        "<p>If you would rather not wait for that one-time download, pre-convert on your iPhone "
        "(<em>Settings → Photos → Most Compatible</em>) and transfer JPGs instead. The in-browser path is "
        "free, private and needs no extra app.</p>",
        "<li><strong>Drop your HEIC files in.</strong> Chrome, Edge, Firefox and Safari all convert them. "
        "On Chrome, Edge or Firefox the decoder downloads once (about 1.3 MB) and is cached for next time.</li>",
        "<p>Yes. This tool runs entirely client-side on every current browser, iOS included. Tap the dropzone "
        "to open your photo library, pick the HEIC files, and convert. The output JPGs are saved with the "
        "standard iOS download flow.</p>",
        "<p>Chrome, Edge and Firefox don't ship a HEIC decoder, so we load a small self-hosted one the first "
        "time you convert (about 1.3 MB, cached afterwards). Your HEIC files haven't gone anywhere — we "
        "never upload them. If you prefer to skip the download, set <em>Settings → Photos → Most "
        "Compatible</em> on your iPhone and transfer JPGs instead.</p>",
    ],
    "zh": [
        "<p>在浏览器内将 iPhone HEIC 婚纱照转换为 JPG。支持批量处理、画质保留——而且现在 Chrome、Edge、Firefox 和 Safari 都能用。</p>",
        "<p><strong>浏览器支持：</strong>当前所有浏览器都能用。Safari 使用系统内置的 HEIC 解码器；Chrome、Edge 和 Firefox 则会在你首次转换时加载一个自托管的小型解码器（约 1.3 MB）。两种方式都不会上传任何文件。</p>",
        "<p><strong>隐私：</strong>每张照片都在浏览器标签页内本地解码与重新编码。我们不会上传、存储或记录你的婚礼照片——这个页面绝不会带着图片数据发起网络请求。</p>",
        "<p>因此整个转换过程都在你的浏览器里完成。Safari 用内置图像解码器处理 HEIC；Chrome、Edge 和 Firefox 则加载一个本地运行的自托管解码器——没有 CDN，不上传，也不需要账号。</p>",
        "<p>如果你不想等这一次性的下载，可以先在 iPhone 上预转（<em>设置 → 照片 → 兼容性最佳</em>）再传输 JPG。浏览器内转换这条路免费、私密，也不需要装任何额外应用。</p>",
        "<li><strong>把 HEIC 文件拖进来即可。</strong>Chrome、Edge、Firefox 和 Safari 都能转换。在 Chrome、Edge 或 Firefox 上，解码器只下载一次（约 1.3 MB），之后会被缓存。</li>",
        "<p>可以。这个工具在当前所有浏览器（包括 iOS）上完全在客户端运行。点击框打开相册，选好 HEIC 文件，然后转换。输出的 JPG 会走 iOS 常规的下载流程保存。</p>",
        "<p>Chrome、Edge 和 Firefox 本身不带 HEIC 解码器，所以我们在你首次转换时加载一个自托管的小解码器（约 1.3 MB，之后会缓存）。你的 HEIC 文件哪儿也没去——我们从不主动上传。如果你想跳过这次下载，在 iPhone 上设置<em>设置 → 照片 → 兼容性最佳</em>并传输 JPG 即可。</p>",
    ],
    "es": [
        "<p>Convierte fotos de boda HEIC de iPhone a JPG en tu navegador. Compatible con lotes, calidad "
        "conservada y ahora funciona igual en Chrome, Edge, Firefox y Safari.</p>",
        "<p><strong>Compatibilidad del navegador:</strong> todos los navegadores actuales funcionan. Safari usa "
        "su decodificador HEIC integrado; Chrome, Edge y Firefox cargan un decodificador propio alojado por "
        "nosotros (unos 1,3 MB) la primera vez que conviertes. En ningún caso se sube nada.</p>",
        "<p><strong>Privacidad:</strong> cada foto se decodifica y vuelve a codificar localmente en la pestaña "
        "de tu navegador. No subimos, almacenamos ni registramos tus fotos de boda — la página nunca hace "
        "una petición de red con datos de imagen.</p>",
        "<p>Así que la conversión se ejecuta enteramente en tu navegador. Safari decodifica HEIC con su "
        "decodificador de imágenes integrado; Chrome, Edge y Firefox cargan un decodificador alojado por "
        "nosotros que funciona en local — sin CDN, sin subidas y sin cuenta.</p>",
        "<p>Si prefieres no esperar a esa descarga única, pre-convierte en tu iPhone "
        "(<em>Ajustes → Fotos → Más compatible</em>) y transfiere los JPG. La ruta en el navegador es gratis, "
        "privada y no necesita ninguna app extra.</p>",
        "<li><strong>Suelta tus archivos HEIC.</strong> Chrome, Edge, Firefox y Safari los convierten todos. "
        "En Chrome, Edge o Firefox el decodificador se descarga una vez (unos 1,3 MB) y queda en caché para "
        "la próxima.</li>",
        "<p>Sí. Esta herramienta se ejecuta por completo en el cliente en todos los navegadores actuales, "
        "iOS incluido. Toca la zona para abrir tu fototeca, elige los HEIC y convierte. Los JPG de salida se "
        "guardan con el flujo de descarga habitual de iOS.</p>",
        "<p>Chrome, Edge y Firefox no incluyen un decodificador HEIC, así que cargamos uno propio alojado por "
        "nosotros la primera vez que conviertes (unos 1,3 MB, y luego queda en caché). Tus archivos HEIC no "
        "han salido de tu dispositivo — nunca los subimos. Si prefieres saltarte la descarga, ajusta "
        "<em>Ajustes → Fotos → Más compatible</em> en tu iPhone y transfiere los JPG.</p>",
    ],
    "fr": [
        "<p>Convertissez les photos de mariage HEIC de l'iPhone en JPG dans votre navigateur. Compatible par "
        "lots, qualité préservée — et ça marche désormais sur Chrome, Edge, Firefox et Safari.</p>",
        "<p><strong>Compatibilité des navigateurs :</strong> tous les navigateurs actuels fonctionnent. Safari "
        "utilise son décodeur HEIC intégré ; Chrome, Edge et Firefox chargent un petit décodeur auto-hébergé "
        "(environ 1,3 Mo) à la première conversion. Dans tous les cas, rien n'est envoyé.</p>",
        "<p><strong>Confidentialité :</strong> chaque photo est décodée et ré-encodée localement dans votre "
        "onglet. Nous ne transmettons, ne stockons et n'enregistrons pas vos photos de mariage — la page "
        "n'effectue jamais de requête réseau avec des données d'image.</p>",
        "<p>La conversion se fait donc entièrement dans votre navigateur. Safari décode le HEIC avec son "
        "décodeur d'images intégré ; Chrome, Edge et Firefox chargent un décodeur auto-hébergé qui tourne en "
        "local — pas de CDN, pas d'envoi, pas de compte.</p>",
        "<p>Si vous préférez ne pas attendre ce téléchargement unique, convertissez au préalable sur votre "
        "iPhone (<em>Réglages → Photos → Compatible</em>) et transférez les JPG. La voie navigateur est "
        "gratuite, privée et ne demande aucune application supplémentaire.</p>",
        "<li><strong>Déposez vos fichiers HEIC.</strong> Chrome, Edge, Firefox et Safari les convertissent tous. "
        "Sur Chrome, Edge ou Firefox, le décodeur se télécharge une fois (environ 1,3 Mo) puis reste en cache "
        "pour la prochaine fois.</li>",
        "<p>Oui. Cet outil fonctionne entièrement côté client sur tous les navigateurs actuels, iOS compris. "
        "Touchez la zone pour ouvrir votre photothèque, choisissez les HEIC et convertissez. Les JPG "
        "résultants sont enregistrés via le flux de téléchargement iOS habituel.</p>",
        "<p>Chrome, Edge et Firefox ne fournissent pas de décodeur HEIC : nous en chargeons un auto-hébergé "
        "à la première conversion (environ 1,3 Mo, mis en cache ensuite). Vos fichiers HEIC n'ont pas bougé "
        "— nous ne les envoyons jamais. Pour éviter ce téléchargement, réglez <em>Réglages → Photos → "
        "Compatible</em> sur votre iPhone et transférez les JPG.</p>",
    ],
    "de": [
        "<p>Konvertieren Sie iPhone HEIC Hochzeitsfotos direkt im Browser zu JPG. Stapelverarbeitung, "
        "Qualität bleibt erhalten — und es funktioniert jetzt in Chrome, Edge, Firefox und Safari gleichermaßen.</p>",
        "<p><strong>Browser-Unterstützung:</strong> Alle aktuellen Browser funktionieren. Safari nutzt seinen "
        "eingebauten HEIC-Decoder; Chrome, Edge und Firefox laden beim ersten Konvertieren einen kleinen, bei "
        "uns selbst gehosteten Decoder (etwa 1,3 MB). In keinem Fall wird etwas hochgeladen.</p>",
        "<p><strong>Datenschutz:</strong> Jedes Foto wird lokal in Ihrem Browser-Tab dekodiert und neu "
        "kodiert. Wir laden Ihre Hochzeitsfotos nicht hoch, speichern oder protokollieren sie nicht — die "
        "Seite stellt niemals eine Netzwerkanfrage mit Bilddaten.</p>",
        "<p>Die Konvertierung läuft also vollständig in Ihrem Browser. Safari dekodiert HEIC mit seinem "
        "eingebauten Bild-Decoder; Chrome, Edge und Firefox laden einen selbst gehosteten Decoder, der lokal "
        "läuft — kein CDN, kein Upload, kein Konto.</p>",
        "<p>Wenn Sie den einmaligen Download nicht abwarten möchten, konvertieren Sie vorher auf Ihrem iPhone "
        "(<em>Einstellungen → Fotos → Kompatibel</em>) und übertragen Sie die JPGs. Der Browser-Weg ist "
        "kostenlos, privat und braucht keine zusätzliche App.</p>",
        "<li><strong>Ziehen Sie Ihre HEIC-Dateien hierher.</strong> Chrome, Edge, Firefox und Safari "
        "konvertieren alle. Unter Chrome, Edge oder Firefox wird der Decoder einmal geladen (etwa 1,3 MB) und "
        "danach zwischengespeichert.</li>",
        "<p>Ja. Dieses Tool läuft in allen aktuellen Browsern vollständig clientseitig, auch auf iOS. Tippen "
        "Sie auf die Ablagefläche, um Ihre Fotomediathek zu öffnen, wählen Sie die HEIC-Dateien und konvertieren "
        "Sie. Die fertigen JPGs werden über den normalen iOS-Download-Ablauf gespeichert.</p>",
        "<p>Chrome, Edge und Firefox bringen keinen HEIC-Decoder mit, daher laden wir beim ersten "
        "Konvertieren einen kleinen selbst gehosteten (etwa 1,3 MB, danach zwischengespeichert). Ihre HEIC-"
        "Dateien sind nirgendwohingegangen — wir laden sie nie hoch. Wer den Download vermeiden möchte, "
        "stellt <em>Einstellungen → Fotos → Kompatibel</em> auf dem iPhone ein und überträgt JPGs.</p>",
    ],
    "pt": [
        "<p>Converta fotos de casamento HEIC do iPhone em JPG no seu navegador. Aceita lotes, mantém a "
        "qualidade — e agora funciona igual em Chrome, Edge, Firefox e Safari.</p>",
        "<p><strong>Compatibilidade do navegador:</strong> todos os navegadores atuais funcionam. O Safari usa "
        "o seu decodificador HEIC nativo; Chrome, Edge e Firefox carregam um pequeno decodificador hospedado "
        "por nós (cerca de 1,3 MB) na primeira conversão. Nada é enviado em nenhum dos casos.</p>",
        "<p><strong>Privacidade:</strong> cada foto é decodificada e recodificada localmente na aba do seu "
        "navegador. Não enviamos, armazenamos nem registramos as suas fotos de casamento — a página nunca faz "
        "uma requisição de rede com dados de imagem.</p>",
        "<p>Então a conversão roda inteiramente no seu navegador. O Safari decodifica HEIC com o decodificador "
        "de imagens nativo; Chrome, Edge e Firefox carregam um decodificador hospedado por nós que roda "
        "localmente — sem CDN, sem envio, sem conta.</p>",
        "<p>Se preferir não esperar por esse download único, converta antes no seu iPhone "
        "(<em>Ajustes → Fotos → Mais Compatível</em>) e transfira os JPGs. O caminho pelo navegador é "
        "gratuito, privado e não exige nenhum app extra.</p>",
        "<li><strong>Solte seus arquivos HEIC.</strong> Chrome, Edge, Firefox e Safari convertem todos. No "
        "Chrome, Edge ou Firefox o decodificador baixa uma vez (cerca de 1,3 MB) e fica em cache para a "
        "próxima.</li>",
        "<p>Sim. Esta ferramenta roda inteiramente no cliente em todos os navegadores atuais, iOS incluso. Toque "
        "na área para abrir sua galeria, escolha os arquivos HEIC e converta. Os JPGs de saída são salvos pelo "
        "fluxo de download padrão do iOS.</p>",
        "<p>Chrome, Edge e Firefox não trazem decodificador HEIC, então carregamos um próprio hospedado por "
        "nós na primeira conversão (cerca de 1,3 MB, depois fica em cache). Seus arquivos HEIC não foram a "
        "lugar nenhum — nunca os enviamos. Para pular o download, ajuste <em>Ajustes → Fotos → Mais "
        "Compatível</em> no iPhone e transfira os JPGs.</p>",
    ],
    "ja": [
        "<p>iPhone の HEIC の結婚式写真をブラウザ内で JPG に変換します。まとめて処理でき、画質も保たれます。"
        "そして 이제 Chrome・Edge・Firefox・Safari のすべてで動作します。</p>",
        "<p><strong>ブラウザ対応：</strong>現在の主要なブラウザすべてで動作します。Safari は内蔵の HEIC "
        "デコーダを使い、Chrome・Edge・Firefox では初回変換時に当社でホストしている小さなデコーダ"
        "（約 1.3 MB）を読み込みます。いずれの場合もアップロードは発生しません。</p>",
        "<p><strong>プライバシー：</strong>すべての写真はブラウザのタブ内でローカルにデコード・再エンコードされ"
        "ます。結婚式の写真をアップロード・保存・記録することは一切ありません。画像データを含むネットワーク"
        "リクエストもこのページから送信されません。</p>",
        "<p>だから Safari は内蔵の画像デコーダで HEIC を解読し、Chrome・Edge・Firefox は当社でホストした"
        "デコーダをローカルで実行します。CDN なし、アップロードなし、"
        "アカウントも不要です。</p>",
        "<p>その一度きりのダウンロードを待てない場合は、iPhone 側で先に変換してください（<em>設定 → 写真 → "
        "最も互換性が高い</em>）。ブラウザ内の経路は無料で、プライバシーも守られ、追加アプリも不要です。</p>",
        "<li><strong>HEIC ファイルをドロップしてください。</strong>Chrome・Edge・Firefox・Safari すべてで変換"
        "できます。Chrome・Edge・Firefox ではデコーダは一度だけダウンロードされ（約 1.3 MB）、以降はキャッシュ"
        "されます。</li>",
        "<p>はい。このツールは iOS を含む現在のすべてのブラウザで完全にクライアントサイドで動作します。ドロップ"
        "領域をタップして写真ライブラリを開き、HEIC を選んで変換してください。出力された JPG は iOS 標準の"
        "ダウンロード手順で保存されます。</p>",
        "<p>Chrome・Edge・Firefox には HEIC デコーダが同梱されていないため、初回変換時に当社でホストした"
        "小さなデコーダを読み込みます（約 1.3 MB、以降はキャッシュ）。あなたの HEIC ファイルはどこにも送信"
        "されていません — アップロードすることはありません。ダウンロードを避けたい場合は iPhone の<em>設定 → "
        "写真 → 最も互換性が高い</em>を設定して JPG を転送してください。</p>",
    ],
    "ru": [
        "<p>Конвертируйте свадебные фото HEIC с iPhone в JPG прямо в браузере. Пакетная обработка, качество "
        "сохраняется — и теперь это работает в Chrome, Edge, Firefox и Safari одинаково.</p>",
        "<p><strong>Поддержка браузеров:</strong> работают все современные браузеры. Safari использует "
        "встроенный HEIC-декодер, а Chrome, Edge и Firefox при первом преобразовании загружают небольшой "
        "декодер, размещённый на нашем сервере (около 1,3 МБ). Ни в одном случае ничего не загружается "
        "на сторону пользователя.</p>",
        "<p><strong>Приватность:</strong> каждое фото декодируется и перекодируется локально во вкладке "
        "браузера. Мы не загружаем, не храним и не логируем ваши свадебные фотографии — страница никогда не "
        "делает сетевой запрос с данными изображений.</p>",
        "<p>Таким образом, преобразование полностью выполняется в вашем браузере. Safari декодирует HEIC "
        "встроенным декодером изображений, а Chrome, Edge и Firefox загружают размещённый у нас декодер, "
        "который работает локально — без CDN, без загрузки файлов и без аккаунта.</p>",
        "<p>Если вы не хотите ждать эту разовую загрузку, сконвертируйте файлы заранее на iPhone "
        "(<em>Настройки → Фото → Совместимый</em>) и передайте готовые JPG. Вариант в браузере бесплатный, "
        "приватный и не требует дополнительных приложений.</p>",
        "<li><strong>Перетащите файлы HEIC.</strong> Chrome, Edge, Firefox и Safari конвертируют их все. "
        "В Chrome, Edge или Firefox декодер скачивается один раз (около 1,3 МБ) и затем кэшируется.</li>",
        "<p>Да. Этот инструмент полностью работает на стороне клиента во всех современных браузерах, включая "
        "iOS. Нажмите на зону, чтобы открыть медиатеку, выберите файлы HEIC и нажмите «Конвертировать». "
        "Готовые JPG сохраняются обычным способом загрузки в iOS.</p>",
        "<p>В Chrome, Edge и Firefox нет HEIC-декодера, поэтому при первом преобразовании мы загружаем "
        "небольшой размещённый у нас декодер (около 1,3 МБ, дальше он в кэше). Ваши файлы HEIC никуда не "
        "отправлялись — мы никогда их не загружаем. Если вы хотите избежать загрузки, установите <em>Настройки "
        "→ Фото → Совместимый</em> на iPhone и передайте JPG.</p>",
    ],
    "ar": [
        "<p>حوّل صور زفاف HEIC من iPhone إلى JPG داخل متصفحك. يدعم الدفعات ويحافظ على الجودة — والأهم أنه "
        "يعمل الآن على Chrome وEdge وFirefox وSafari على حد سواء.</p>",
        "<p><strong>دعم المتصفحات:</strong> تعمل جميع المتصفحات الحديثة. يستخدم Safari مفكّك ترميز HEIC "
        "المدمج، بينما يحمّل Chrome وEdge وFirefox مفكّك ترميز صغيرًا مستضافًا لدينا (نحو 1.3 ميغابايت) عند "
        "أول عملية تحويل. ولا يتم رفع أي ملف في الحالتين.</p>",
        "<p><strong>الخصوصية:</strong> يتم فك ترميز كل صورة وإعادة ترميزها محليًا داخل تبويب المتصفح. نحن لا "
        "نرفع ولا نخزّن ولا نسجّل صور زفافكم — لا تُجري الصفحة أي طلب شبكة يحمل بيانات الصور.</p>",
        "<p>لذلك يتم التحويل بالكامل داخل متصفحك. يفكّ Safari ترميز HEIC عبر مفكّك الصور المدمج، بينما يحمّل "
        "Chrome وEdge وFirefox مفكّك ترميز مستضافًا لدينا يعمل محليًا — بلا CDN، وبلا رفع، وبلا حساب.</p>",
        "<p>إن كنت تفضّل عدم انتظار هذا التنزيل لمرة واحدة، فحوّل مسبقًا على iPhone "
        "(<em>الإعدادات ← الصور ← الأكثر توافقًا</em>) وانقل ملفات JPG. أما المسار داخل المتصفح فهو مجاني "
        "وخاص ولا يحتاج أي تطبيق إضافي.</p>",
        "<li><strong>أفلت ملفات HEIC هنا.</strong> يحوّلها Chrome وEdge وFirefox وSafari جميعًا. وعلى Chrome "
        "أو Edge أو Firefox يُنزَّل مفكّك الترميز مرة واحدة (نحو 1.3 ميغابايت) ثم يُخزَّن مؤقتًا.</li>",
        "<p>نعم. تعمل هذه الأداة بالكامل على الجهاز في كل المتصفحات الحديثة، بما فيها iOS. اضغط منطقة الإفلات "
        "لفتح معرض الصور، اختر ملفات HEIC ثم حوّل. تُحفظ ملفات JPG الناتجة عبر تدفق التنزيل المعتاد في iOS.</p>",
        "<p>لا تحتوي Chrome وEdge وFirefox على مفكّك ترميز HEIC، لذا نحمّل مفكّكًا صغيرًا مستضافًا لدينا عند "
        "أول تحويل (نحو 1.3 ميغابايت، ثم يُخزَّن مؤقتًا). لم تغادر ملفات HEIC جهازك — نحن لا نرفعها أبدًا. "
        "وإن أردت تفادي التنزيل، فاضبط <em>الإعدادات ← الصور ← الأكثر توافقًا</em> على iPhone وانقل ملفات "
        "JPG.</p>",
    ],
    "th": [
        "<p>แปลงรูปภาพงานแต่งงาน HEIC จาก iPhone เป็น JPG ในเบราว์เซอร์ของคุณ รองรับการแปลงเป็นชุด "
        "รักษาคุณภาพไว้ — และตอนนี้ใช้ได้ทั้งใน Chrome, Edge, Firefox และ Safari</p>",
        "<p><strong>การรองรับเบราว์เซอร์:</strong> เบราว์เซอร์รุ่นปัจจุบันทั้งหมดใช้ได้ Safari ใช้ตัวถอดรหัส "
        "HEIC ที่มากับระบบ ส่วน Chrome, Edge และ Firefox จะโหลดตัวถอดรหัสขนาดเล็กที่เราจัดให้ฟรี (ประมาณ "
        "1.3 MB) ในการแปลงครั้งแรก และไม่มีการอัปโหลดไฟล์ในทุกกรณี</p>",
        "<p><strong>ความเป็นส่วนตัว:</strong> ทุกภาพถูกถอดรหัสและเข้ารหัสใหม่ภายในแท็บเบราว์เซอร์ของคุณ "
        "เราไม่อัปโหลด ไม่จัดเก็บ และไม่บันทึกรูปภาพงานแต่งงานของคุณ — และหน้านี้ไม่เคยส่งคำขอเครือข่ายที่มีข้อมูลภาพ "
        "ออกไป</p>",
        "<p>ดังนั้นการแปลงทั้งหมดจึงทำงานในเบราว์เซอร์ของคุณ Safari ถอดรหัส HEIC ด้วยตัวถอดรหัสภาพที่มากับระบบ "
        "ขณะที่ Chrome, Edge และ Firefox โหลดตัวถอดรหัสที่เราจัดให้ฟรีซึ่งทำงานในเครื่อง — ไม่มี CDN ไม่มีการอัปโหลด "
        "และไม่ต้องมีบัญชี</p>",
        "<p>ถ้าไม่อยากรอดาวน์โหลดครั้งเดียวนั้น ให้แปลงล่วงหน้าบน iPhone "
        "(<em>การตั้งค่า → รูปภาพ → เข้ากันได้ที่สุด</em>) แล้วส่งไฟล์ JPG มาแทน วิธีในเบราว์เซอร์ฟรี เป็นส่วนตัว "
        "และไม่ต้องติดตั้งแอปเพิ่ม</p>",
        "<li><strong>ลากไฟล์ HEIC มาวางที่นี่</strong> Chrome, Edge, Firefox และ Safari แปลงได้ทั้งหมด "
        "บน Chrome, Edge หรือ Firefox ตัวถอดรหัสจะถูกโหลดครั้งเดียว (ประมาณ 1.3 MB) แล้วแคชไว้ใช้ครั้งต่อไป</li>",
        "<p>ได้ครับ เครื่องมือนี้ทำงานทั้งหมดบนเครื่องของคุณในเบราว์เซอร์รุ่นปัจจุบันทุกตัว รวมถึง iOS "
        "แตะที่พื้นที่วางเพื่อเปิดคลังรูปภาพ เลือกไฟล์ HEIC แล้วกดแปลง ไฟล์ JPG ที่ได้จะถูกบันทึกด้วยวิธีดาวน์โหลด "
        "มาตรฐานของ iOS</p>",
        "<p>Chrome, Edge และ Firefox ไม่มีตัวถอดรหัส HEIC มาพร้อม เราจึงโหลดตัวถอดรหัสขนาดเล็กที่เราจัดให้ฟรีในการแปลงครั้งแรก "
        "(ประมาณ 1.3 MB แล้วแคชไว้) ไฟล์ HEIC ของคุณไม่ได้ออกจากเครื่อง — เราไม่เคยอัปโหลดไฟล์ หากไม่อยากโหลด "
        "ให้ตั้งค่า <em>การตั้งค่า → รูปภาพ → เข้ากันได้ที่สุด</em> บน iPhone แล้วส่งไฟล์ JPG มาแทน</p>",
    ],
    "hi": [
        "<p>अपने iPhone की HEIC शादी की तस्वीरों को ब्राउज़र में ही JPG में बदलें। बैच में काम करता है, क्वालिटी "
        "बनी रहती है — और अब Chrome, Edge, Firefox और Safari सभी में चलता है।</p>",
        "<p><strong>ब्राउज़र समर्थन:</strong> सभी मौजूदा ब्राउज़र काम करते हैं। Safari अपना अंतर्निहित HEIC "
        "डिकोडर इस्तेमाल करता है; Chrome, Edge और Firefox पहली बार बदलते समय एक छोटा डिकोडर लोड करते हैं जो हम "
        "खुद होस्ट करते हैं (लगभग 1.3 MB)। किसी भी स्थिति में कुछ अपलोड नहीं होता।</p>",
        "<p><strong>गोपनीयता:</strong> हर फ़ोटो आपके ब्राउज़र टैब में ही लोकल डिकोड और दोबारा एन्कोड होती है। हम "
        "आपकी शादी की तस्वीरें नहीं अपलोड करते, सहेजते या लॉग करते — और यह पेज कभी इमेज डेटा के साथ नेटवर्क "
        "रिक्वेस्ट नहीं भेजता।</p>",
        "<p>इसलिए पूरा कन्वर्ज़न आपके ब्राउज़र में ही चलता है। Safari HEIC को अपने अंतर्निहित इमेज डिकोडर से "
        "चीरता है; जबकि Chrome, Edge और Firefox हमारे होस्ट किए हुए डिकोडर को लोड करते हैं जो लोकली चलता है — न कोई "
        "CDN, न अपलोड, न अकाउंट।</p>",
        "<p>अगर आप उस एक बार के डाउनलोड का इंतज़ार नहीं करना चाहते, तो iPhone पर ही पहले बदल लें "
        "(<em>सेटिंग्स → फ़ोटो → सबसे ज़्यादा कॉम्पैटिबल</em>) और JPG फ़ाइलें भेजें। ब्राउज़र वाला रास्ता मुफ़्त है, "
        "निजी है और उसे कोई अतिरिक्त ऐप नहीं चाहिए।</p>",
        "<li><strong>अपनी HEIC फ़ाइलें यहाँ छोड़ें।</strong> Chrome, Edge, Firefox और Safari सभी उन्हें बदल देते "
        "हैं। Chrome, Edge या Firefox में डिकोडर एक बार डाउनलोड होता है (लगभग 1.3 MB) और फिर कैश रहता है।</li>",
        "<p>हाँ। यह टूल हर मौजूदा ब्राउज़र में पूरी तरह क्लाइंट-साइड चलता है, iOS भी। फ़ोटो लाइब्रेरी खोलने के लिए ड्रॉप ज़ोन "
        "पर टैप करें, HEIC फ़ाइलें चुनें और बदलें। बनी हुई JPG फ़ाइलें iOS के सामान्य डाउनलोड तरीके से सेव होती हैं।</p>",
        "<p>Chrome, Edge और Firefox में HEIC डिकोडर नहीं होता, इसलिए पहली बार बदलते समय हम अपना होस्ट किया हुआ छोटा "
        "डिकोडर लोड करते हैं (लगभग 1.3 MB, बाद में कैश रहता है)। आपकी HEIC फ़ाइलें कहीं नहीं गईं — हम उन्हें कभी "
        "अपलोड नहीं करते। डाउनलोड से बचना हो तो iPhone पर <em>सेटिंग्स → फ़ोटो → सबसे ज़्यादा कॉम्पैटिबल</em> सेट करके "
        "JPG भेजें।</p>",
    ],
}

# ---------------------------------------------------------------------------
# 2. JSON-LD: browserRequirements + HowTo step 1, per language.
# ---------------------------------------------------------------------------

JSONLD = {
    "en": ("Any modern browser (Chrome, Edge, Firefox or Safari)",
           "Add your HEIC photos",
           "Drop your HEIC/HEIF files into the tool. Chrome, Edge, Firefox and Safari all convert them in "
           "your browser, and nothing is uploaded."),
    "zh": ("任何现代浏览器（Chrome、Edge、Firefox 或 Safari）",
           "添加你的 HEIC 照片",
           "把 HEIC/HEIF 文件拖进工具。Chrome、Edge、Firefox 和 Safari 都会在浏览器里完成转换，全程不���传。"),
    "es": ("Cualquier navegador moderno (Chrome, Edge, Firefox o Safari)",
           "Añade tus fotos HEIC",
           "Suelta tus archivos HEIC/HEIF en la herramienta. Chrome, Edge, Firefox y Safari los convierten en tu "
           "navegador, y no se sube nada."),
    "fr": ("Tout navigateur moderne (Chrome, Edge, Firefox ou Safari)",
           "Ajoutez vos photos HEIC",
           "Déposez vos fichiers HEIC/HEIF dans l'outil. Chrome, Edge, Firefox et Safari les convertissent dans "
           "votre navigateur, et rien n'est envoyé."),
    "de": ("Jeder moderne Browser (Chrome, Edge, Firefox oder Safari)",
           "HEIC-Fotos hinzufügen",
           "Ziehen Sie Ihre HEIC/HEIF-Dateien in das Tool. Chrome, Edge, Firefox und Safari konvertieren sie im "
           "Browser, und es wird nichts hochgeladen."),
    "pt": ("Qualquer navegador moderno (Chrome, Edge, Firefox ou Safari)",
           "Adicione suas fotos HEIC",
           "Solte seus arquivos HEIC/HEIF na ferramenta. Chrome, Edge, Firefox e Safari convertem tudo no seu "
           "navegador, e nada é enviado."),
    "ja": ("主要なブラウザ（Chrome・Edge・Firefox・Safari のいずれか）",
           "HEIC 写真を追加",
           "HEIC/HEIF ファイルをツールにドロップしてください。Chrome・Edge・Firefox・Safari のいずれもブラウザ内で"
           "変換し、アップロードは一切行いません。"),
    "ru": ("Любой современный браузер (Chrome, Edge, Firefox или Safari)",
           "Добавьте HEIC-фотографии",
           "Перетащите файлы HEIC/HEIF в инструмент. Chrome, Edge, Firefox и Safari конвертируют их прямо в "
           "браузере, и ничего не отправляется."),
    "ar": ("أي متصفح حديث (Chrome أو Edge أو Firefox أو Safari)",
           "أضف صور HEIC الخاصة بك",
           "أفلت ملفات HEIC/HEIF في الأداة. يحولها Chrome وEdge وFirefox وSafari داخل متصفحك، ولا يتم رفع أي شيء."),
    "th": ("เบราว์เซอร์สมัยใหม่ทุกตัว (Chrome, Edge, Firefox หรือ Safari)",
           "เพิ่มรูปภาพ HEIC ของคุณ",
           "ลากไฟล์ HEIC/HEIF เข้ามาในเครื่องมือ Chrome, Edge, Firefox และ Safari จะแปลงให้ในเบราว์เซอร์ของคุณ "
           "และไม่มีการอัปโหลดแม้แต่ไฟล์เดียว"),
    "hi": ("कोई भी आधुनिक ब्राउज़र (Chrome, Edge, Firefox या Safari)",
           "अपनी HEIC तस्वीरें जोड़ें",
           "अपनी HEIC/HEIF फ़ाइलें टूल में छोड़ें। Chrome, Edge, Firefox और Safari सभी उन्हें आपके ब्राउज़र में ही "
           "बदल देते हैं, और कुछ भी अपलोड नहीं होता।"),
}

# ---------------------------------------------------------------------------
# 3. The inline JavaScript, changed in the ENGLISH SOURCE only.
#    The localized copies get it from scripts/propagate-tool-js.py.
# ---------------------------------------------------------------------------

JS_OLD_DECODE = """      async function processOne(entry, settings) {
        entry.status = 'working';
        entry.error = null;
        refreshUI();

        try {
          var loaded = await window.weddingAITool.fileToImage(entry.inputFile);
          var img = loaded.img;
          var w = img.naturalWidth, h = img.naturalHeight;"""

JS_NEW_DECODE = """      // HEIC decoding.
      //
      // Safari ships a HEIC decoder in the browser; Chrome, Edge and Firefox
      // do not. heic2any (MIT, asm.js - no WebAssembly, so it needs no CSP
      // change) is vendored under /js/vendor/heic2any/ and is loaded on
      // demand by the shared layer. The native path is tried FIRST so that
      // Safari never downloads the 1.3 MB decoder, and only the browsers
      // that need it pay for it.
      async function loadDecodableImage(file) {
        try {
          var loaded = await window.weddingAITool.fileToImage(file);
          return { img: loaded.img, release: function () { URL.revokeObjectURL(loaded.url); } };
        } catch (nativeErr) {
          var blob = await window.weddingAITool.decodeHeic(file, { toType: 'image/jpeg', quality: 1 });
          var url = URL.createObjectURL(blob);
          var img = new Image();
          await new Promise(function (resolve, reject) {
            img.onload = resolve;
            img.onerror = function () { reject(new Error('HEIC decode produced an unreadable image')); };
            img.src = url;
          });
          return { img: img, release: function () { URL.revokeObjectURL(url); } };
        }
      }

      async function processOne(entry, settings) {
        entry.status = 'working';
        entry.error = null;
        refreshUI();

        try {
          var loaded = await loadDecodableImage(entry.inputFile);
          var img = loaded.img;
          var w = img.naturalWidth, h = img.naturalHeight;"""

JS_OLD_RESIZE = """          var canvas = document.createElement('canvas');
          canvas.width = tw;
          canvas.height = th;
          var ctx = canvas.getContext('2d');
          ctx.imageSmoothingEnabled = true;
          ctx.imageSmoothingQuality = 'high';
          ctx.drawImage(img, 0, 0, tw, th);
          var blob = await window.weddingAITool.canvasToBlob(canvas, settings.format, settings.quality);"""

JS_NEW_RESIZE = """          // pica (MIT) does a proper multi-step resample; the browser's
          // drawImage() bilinear filter visibly softens a large downscale.
          var canvas = await window.weddingAITool.resizeCanvas(img, tw, th);
          var blob = await window.weddingAITool.canvasToBlob(canvas, settings.format, settings.quality);"""

JS_OLD_RELEASE = """          // free the loaded image
          URL.revokeObjectURL(loaded.url);"""
JS_NEW_RELEASE = """          // free the loaded image
          loaded.release();"""

JS_OLD_ERROR = """          if (/decode|HEIC|HEIF/i.test(rawMsg)) {
            entry.error = 'Your browser can\\u2019t decode HEIC. Open this URL in Safari, or pre-convert via Settings → Photos on your iPhone.';
          } else {"""
JS_NEW_ERROR = """          if (/decode|HEIC|HEIF/i.test(rawMsg)) {
            entry.error = window.weddingAITool.t('heicDecodeFailed', 'Could not decode this HEIC/HEIF file.');
          } else {"""

JS_OLD_TOAST = """        if (errCount > 0 && doneCount === 0) {
          window.weddingAITool.toast('No files converted — your browser may not decode HEIC. Try Safari.', 'error');
        } else {
          window.weddingAITool.toast('Conversion complete.');
        }"""
JS_NEW_TOAST = """        if (errCount > 0 && doneCount === 0) {
          window.weddingAITool.toast(window.weddingAITool.t('heicDecodeFailed', 'No files converted — this HEIC/HEIF file could not be decoded.'), 'error');
        } else {
          window.weddingAITool.toast(window.weddingAITool.t('heicComplete', 'Conversion complete.'), 'success');
        }"""

JS_OLD_NOFILES = """        if (accepted === 0) { window.weddingAITool.toast('No HEIC/HEIF files found. Drop .heic or .heif files.', 'error'); return; }"""
JS_NEW_NOFILES = """        if (accepted === 0) { window.weddingAITool.toast(window.weddingAITool.t('noHeicFiles', 'No HEIC/HEIF files found. Drop .heic or .heif files.'), 'error'); return; }"""

JS_OLD_SAVE = """        window.weddingAITool.downloadZip(outputs, 'heic_converted');
        window.weddingAITool.toast('Saving ' + outputs.length + ' file' + (outputs.length === 1 ? '' : 's') + '\\u2026');"""
JS_NEW_SAVE = """        window.weddingAITool.downloadZip(outputs, 'heic_converted');
        window.weddingAITool.toast(window.weddingAITool.t('heicSaving', 'Saving {n} file(s)…', { n: outputs.length }), 'success');"""

JS_OLD_SUMMARY = """        summaryEl.innerHTML =
          (done.length > 0
            ? '<div><strong>' + done.length + '</strong> converted to JPG</div>' +
              '<div><strong>Total now:</strong> ' + window.weddingAITool.formatBytes(outTotal) + ' (was ' + window.weddingAITool.formatBytes(origTotal) + ' HEIC)</div>'
            : '<div style="color:#b00020"><strong>0 converted</strong> — your browser likely can\\u2019t decode HEIC.</div>') +
          (errs.length ? '<div style="color:#b00020"><strong>' + errs.length + ' errored</strong> — likely browser limitation. See the note above.</div>' : '');"""
JS_NEW_SUMMARY = """        var T = window.weddingAITool.t;
        summaryEl.innerHTML =
          (done.length > 0
            ? '<div><strong>' + done.length + '</strong> ' + T('heicConvertedToJpg', 'converted to JPG') + '</div>' +
              '<div><strong>' + T('heicTotalNow', 'Total now:') + '</strong> ' + window.weddingAITool.formatBytes(outTotal) + ' (was ' + window.weddingAITool.formatBytes(origTotal) + ' HEIC)</div>'
            : '<div style="color:#b00020"><strong>0</strong> ' + T('heicZeroConverted', 'converted — this file could not be decoded.') + '</div>') +
          (errs.length ? '<div style="color:#b00020"><strong>' + errs.length + '</strong> ' + T('heicErrored', 'errored — this file could not be decoded.') + '</div>' : '');"""

JS_REPLACEMENTS = [
    (JS_OLD_DECODE, JS_NEW_DECODE),
    (JS_OLD_RESIZE, JS_NEW_RESIZE),
    (JS_OLD_RELEASE, JS_NEW_RELEASE),
    (JS_OLD_ERROR, JS_NEW_ERROR),
    (JS_OLD_TOAST, JS_NEW_TOAST),
    (JS_OLD_NOFILES, JS_NEW_NOFILES),
    (JS_OLD_SAVE, JS_NEW_SAVE),
    (JS_OLD_SUMMARY, JS_NEW_SUMMARY),
]


def write_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmpwrite")
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def replace_prose(text: str, blocks: list, lang: str):
    """Replace the eight Safari-bearing blocks, in document order."""
    # A <p> that lives INSIDE a <script> (the JSON-LD) is not prose. Find the
    # script spans and skip anything that overlaps them.
    spans = [(m.start(), m.end())
             for m in re.finditer(r"(?s)<script\b[^>]*>.*?</script>", text)]

    def inside_script(a: int, b: int) -> bool:
        return any(s < b and a < e for s, e in spans)

    # The eight blocks live in four different containers:
    #   <p>                                     intro / how-it-works / FAQ
    #   <li>                                    the how-to step
    #   <div class="wa-tool-heic-note">        the "Browser support" box
    #   <div class="wa-tool-banner">           the "Privacy" banner
    #
    # They are identified by ROLE, not by position: the ru copy of this page
    # is an older revision and only has four of the eight blocks, so a
    # positional match would silently mis-assign them.
    ROLES = ["intro", "support", "privacy", "how1", "how2", "step", "faqios", "faqchrome"]
    BLOCK_RE = re.compile(
        r"(?s)<p\b[^>]*>.*?</p>"
        r"|<li\b[^>]*>.*?</li>"
        r"|<div class=\"wa-tool-heic-note\">.*?</div>"
        r"|<div class=\"wa-tool-banner\">.*?</div>")

    details_spans = [(m.start(), m.end(), m.group(0))
                     for m in re.finditer(r"(?s)<details\b[^>]*>.*?</details>", text)]

    def enclosing_details(pos):
        for s, e, body in details_spans:
            if s <= pos < e:
                return body
        return ""

    h1_end = text.find("</h1>")
    h1_end = h1_end if h1_end >= 0 else -1

    cands = list(BLOCK_RE.finditer(text))
    if not cands:
        raise SystemExit(f"[FAIL] {lang}: no candidate blocks found")

    def is_p(m):
        return m.group(0).startswith("<p")

    def is_li(m):
        return m.group(0).startswith("<li")

    by_role = {}

    def take(role, m):
        by_role[role] = m

    for m in cands:
        b = m.group(0)
        if "wa-tool-heic-note" in b and "support" not in by_role:
            take("support", m)
        elif "wa-tool-banner" in b and "privacy" not in by_role:
            take("privacy", m)

    # the intro paragraph is the first <p> after the <h1>
    for m in cands:
        if is_p(m) and h1_end >= 0 and h1_end < m.start() < h1_end + 600:
            take("intro", m)
            break

    intro_end = by_role["intro"].end() if "intro" in by_role else 0

    # "how1" is the first <p> after the intro that mentions the <img> decoder
    for m in cands:
        if m.start() < intro_end or not is_p(m):
            continue
        if "wa-tool-banner" in m.group(0) or "wa-tool-heic-note" in m.group(0):
            continue
        if "&lt;img&gt;" in m.group(0):
            take("how1", m)
            break

    # "how2" is the <p> right after "how1"
    if "how1" in by_role:
        h1e = by_role["how1"].end()
        for m in cands:
            if m.start() >= h1e and is_p(m):
                take("how2", m)
                break

    # "step" is the first <li> of the ordered list that follows "how2"
    if "how2" in by_role:
        h2e = by_role["how2"].end()
        for m in cands:
            if m.start() >= h2e and is_li(m):
                take("step", m)
                break

    # the two FAQ answers: identified by their <summary>.
    #
    # The summaries are TRANSLATED, so a literal "iPhone" is not reliable -
    # the Arabic copy writes it as "آيفوني" and the Hindi copy keeps "iPhone",
    # while the Russian copy is an older revision with a different FAQ set.
    # So: the Chrome answer is found by the browser names (which survive
    # translation), and the iPhone answer falls back to "the first FAQ" only
    # when the page has the modern six-question structure.
    details_list = [m for m in re.finditer(r"(?s)<details\b[^>]*>.*?</details>", text)]

    def summary_of(dm):
        sm = re.search(r"(?s)<summary\b[^>]*>(.*?)</summary>", dm.group(0))
        return sm.group(1) if sm else ""

    for dm in details_list:
        summ = summary_of(dm)
        if ("Chrome" in summ or "Safari" in summ) and "faqchrome" not in by_role:
            for m in cands:
                if dm.start() <= m.start() < dm.end():
                    take("faqchrome", m)
                    break
            break

    for dm in details_list:
        summ = summary_of(dm)
        if ("iPhone" in summ or "iOS" in summ) and "faqios" not in by_role:
            for m in cands:
                if dm.start() <= m.start() < dm.end():
                    take("faqios", m)
                    break
            break

    if "faqios" not in by_role and len(details_list) >= 6:
        dm = details_list[0]
        for m in cands:
            if dm.start() <= m.start() < dm.end():
                # skip it if this block is already the Chrome answer
                if "faqchrome" not in by_role or m is not by_role["faqchrome"]:
                    take("faqios", m)
                break

    out = []
    last = 0
    replaced = 0
    for role, m in sorted(by_role.items(), key=lambda kv: kv[1].start()):
        idx = ROLES.index(role)
        if idx >= len(blocks):
            continue
        out.append(text[last:m.start()])
        out.append(blocks[idx])
        last = m.end()
        replaced += 1
        print(f"      {role}: {m.group(0)[:58]}...")
    out.append(text[last:])
    if replaced == 0:
        raise SystemExit(f"[FAIL] {lang}: no Safari block could be identified")
    return "".join(out), replaced


def patch_jsonld(text: str, lang: str):
    req, step_name, step_text = JSONLD[lang]
    changed = [0]

    def repl(m):
        raw = m.group(2)
        try:
            obj = json.loads(raw)
        except Exception:
            return m.group(0)
        touched = False
        if isinstance(obj, dict) and obj.get("@type") == "SoftwareApplication":
            if obj.get("browserRequirements") != req:
                obj["browserRequirements"] = req
                touched = True
        if isinstance(obj, dict) and obj.get("@type") == "HowTo":
            steps = obj.get("step")
            if isinstance(steps, list) and steps:
                s0 = steps[0]
                if isinstance(s0, dict):
                    if s0.get("name") != step_name:
                        s0["name"] = step_name
                        touched = True
                    if s0.get("text") != step_text:
                        s0["text"] = step_text
                        touched = True
        if not touched:
            return m.group(0)
        changed[0] += 1
        return m.group(1) + json.dumps(obj, ensure_ascii=False) + m.group(3)

    text = re.sub(r'(<script type="application/ld\+json">)(.*?)(</script>)', repl, text, flags=re.S)
    return text, changed[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    total = 0
    for lang in LANGS:
        p = ROOT / "tools" / SLUG / "index.html" if lang == "en" else ROOT / lang / "tools" / SLUG / "index.html"
        if not p.exists():
            print(f"  {lang}: MISSING")
            continue
        original = p.read_text(encoding="utf-8")
        new, nprose = replace_prose(original, PROSE[lang], lang)
        new, njson = patch_jsonld(new, lang)
        changes = [f"prose x{nprose}", f"jsonld x{njson}"]

        if lang == "en":
            for old, rep in JS_REPLACEMENTS:
                if old not in new:
                    raise SystemExit("[FAIL] the English inline script anchor did not match:\n" + old[:200])
                new = new.replace(old, rep, 1)
            changes.append("js x%d" % len(JS_REPLACEMENTS))

        if new == original:
            print(f"  {lang}: no change")
            continue

        # The inline script must still parse.
        scripts = re.findall(r"(?s)<script\b[^>]*>(.*?)</script>", new)
        biggest = max(scripts, key=len) if scripts else ""
        tmp = Path(os.environ.get("TEMP", ".")) / "heic_inline_check.js"
        tmp.write_text(biggest, encoding="utf-8")
        r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"[FAIL] {lang}: inline script does not parse:\n{r.stderr}")

        if not args.dry_run:
            write_atomic(p, new)
        print(f"  {lang}: {', '.join(changes)}")
        total += 1

    print(f"\npatched copies: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
