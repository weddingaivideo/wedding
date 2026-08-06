// Fix the 9 <h2 ... data-i18n="...">...</h3> typos in 9 service pages.
// The bug: opening <h2> has a stray </h3> in source HTML. The i18n regex
// requires open==close so mismatches are skipped, leaving EN text in non-EN
// pages AND (worse) the next regex match gobbles up to the next </h3> which
// swallows card2 + section-close. Fix the close: </h3> -> </h2>.

const fs = require('fs');
const path = require('path');

const root = 'C:\\Users\\qiaoshan\\.openclaw\\workspace\\weddingai';
const files = [
  'services\\absence-compensation\\celebrity-message\\index.html',
  'services\\absence-compensation\\family-message\\index.html',
  'services\\personalization\\ai-video-generator\\index.html',
  'services\\personalization\\cartoon-style\\index.html',
  'services\\personalization\\meme-generator\\index.html',
  'services\\personalization\\multilingual\\index.html',
  'services\\personalization\\pet-wedding\\index.html',
  'services\\personalization\\wedding-trailer\\index.html',
  'services\\video-enhancement\\slow-motion\\index.html',
];

const re = new RegExp('(<h2[^>]*data-i18n="[^"]*testimonial_title\\.[a-f0-9]{8}"[^>]*>[^<]*)</h3>', 'g');
let total = 0;
for (const rel of files) {
  const p = path.join(root, rel);
  const src = fs.readFileSync(p, 'utf8');
  const out = src.replace(re, '$1</h2>');
  if (out !== src) {
    fs.writeFileSync(p, out, 'utf8');
    const n = (src.match(re) || []).length;
    total += n;
    console.log(`fixed ${n} in ${rel}`);
  } else {
    console.log(`no match in ${rel}`);
  }
}
console.log(`Total: ${total}`);
