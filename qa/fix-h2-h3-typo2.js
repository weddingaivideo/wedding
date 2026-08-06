// Broader fallback: catch any <h2 ... data-i18n=...>...</h3> inside a service page,
// regardless of i18n-key segment. This catches wedding-trailer and slow-motion
// which use custom keys (kim_family_testimonial, mike_rachel_testimonial).
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const files = [
  'services\\personalization\\wedding-trailer\\index.html',
  'services\\video-enhancement\\slow-motion\\index.html',
];
// Match: <h2 ... data-i18n="anything" ...>...no-<... </h3>
const re = new RegExp('(<h2[^>]*\\bdata-i18n="[^"]+"[^>]*>[^<]*)</h3>', 'g');
let total = 0;
for (const rel of files) {
  const p = path.join(root, rel);
  const src = fs.readFileSync(p, 'utf8');
  const matches = src.match(re) || [];
  if (matches.length) {
    const out = src.replace(re, '$1</h2>');
    fs.writeFileSync(p, out, 'utf8');
    console.log(`fixed ${matches.length} in ${rel}`);
    total += matches.length;
  } else {
    console.log(`no match in ${rel}`);
  }
}
console.log(`Total: ${total}`);
