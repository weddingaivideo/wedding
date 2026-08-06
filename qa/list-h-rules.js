const fs = require('fs');
const path = require('path');
const css = fs.readFileSync(path.join(__dirname, '..', 'styles.css'), 'utf8');
const re = /\b(h[1-6])\b[^{}]*?\{[^{}]*?\}/g;
let m;
while ((m = re.exec(css)) !== null) {
  console.log(m[0].replace(/\n/g, ' | '));
}
