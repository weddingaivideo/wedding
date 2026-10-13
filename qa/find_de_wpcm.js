const fs = require('fs');
const html = fs.readFileSync('C:/Users/qiaoshan/.openclaw/workspace/weddingai/qa/.de-tools-now.html', 'utf8');

// Apply same regex strip
let visible = html
  .replace(/<script[^>]*type=["']application\/ld\+json["'][^>]*>[\s\S]*?<\/script>/g, '')
  .replace(/<meta\b[^>]*>/g, '')
  .replace(/\s(?:title|alt|aria-label|content)=(?:"[^"]*"|'[^']*')/g, '');

console.log('has WPCM before strip:', html.includes('Wedding Photo Collage Maker'));
console.log('has WPCM after strip:', visible.includes('Wedding Photo Collage Maker'));
console.log('count after strip:', (visible.match(/Wedding Photo Collage Maker/g) || []).length);

if (visible.includes('Wedding Photo Collage Maker')) {
  const idx = visible.indexOf('Wedding Photo Collage Maker');
  console.log('--- context (idx=' + idx + ') ---');
  console.log(visible.substring(Math.max(0, idx - 200), idx + 100));
}
