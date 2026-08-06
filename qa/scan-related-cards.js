// Strict scan: find <hN>...</hM> with N != M, and check the i18n-key says what.
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..', 'services');
function walk(d) {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    const p = path.join(d, e.name);
    if (e.isDirectory()) walk(p);
    else if (e.name === 'index.html') {
      const t = fs.readFileSync(p, 'utf8');
      // Match: opening <hN ... data-i18n=...>text</hM>, where the OPENING tag has
      // a data-i18n that should be applied. We capture open-level and close-level.
      // Use a non-greedy match of inner content.
      const re = /<h([1-6])\b[^>]*\bdata-i18n="[^"]+"[^>]*>([\s\S]*?)<\/h([1-6])>/g;
      let m;
      while ((m = re.exec(t)) !== null) {
        if (m[1] !== m[3]) {
          const line = (t.substring(0, m.index).split('\n').length);
          console.log(`${p.replace(/\\/g, '/').split('weddingai/')[1]} : L${line} open=h${m[1]} close=h${m[3]} inner="${m[2].slice(0, 60)}"`);
        }
      }
    }
  }
}
walk(root);
console.log('---');
