const fs = require('fs');
const path = require('path');
const css = fs.readFileSync(path.join(__dirname, '..', 'styles.css'), 'utf8');
// Match h2 { or h3 { as a top-level selector (preceded by newline or start)
const re = /(^|\n)(h[2-3])\s*\{([\s\S]*?)\n\}/g;
let m;
while ((m = re.exec(css)) !== null) {
  console.log(`Found ${m[2]}:`);
  console.log(m[2] + ' {');
  console.log(m[3]);
  console.log('}');
  console.log('---');
}
