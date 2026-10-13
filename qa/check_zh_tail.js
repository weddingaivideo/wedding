const fs = require('fs');
const j = JSON.parse(fs.readFileSync('i18n/zh.json', 'utf8'));
const v = j['tools.a.heic_to_jpg_converter_iphone_photos_in.b096ba35'];
console.log('length:', v.length);
console.log('last 30 chars:', JSON.stringify(Array.from(v).slice(-30)));
console.log('hex tail:');
const tail = Buffer.from(v).slice(-30);
for (let i = 0; i < tail.length; i++) {
  process.stdout.write(tail[i].toString(16).padStart(2,'0') + ' ');
  if ((i+1) % 8 === 0) process.stdout.write('\n');
}
console.log();
console.log('has literal backslash?', v.includes('\\\\'));
console.log('has 打开工具\\\\ ?', v.includes('打开工具\\\\'));
console.log('match:', v.match(/打开工具[\\ ]?\\?[ ]?[→↑]?/g));
