// Test the middleware's i18n regex against the actual HTML structure
const sample = `<a class="related-card" style="display:block;">
                        <h3 style="font-size:1rem;" data-i18n="x.y.h4_text.card1_title.zz">Pet Wedding Video</h4>
                        <p style="font-size:0.875rem;" data-i18n="x.y.p_text.card1_desc.zz">Mix in pet-reaction GIFs for the family group chat gold.</p>
                    </a>
                    <a class="related-card" style="display:block;">
                        <h3 style="font-size:1rem;" data-i18n="x.y.h4_text.card2_title.zz">Cinematic Wedding Trailer</h4>
                        <p style="font-size:0td:0.875rem;" data-i18n="x.y.p_text.card2_desc.zz">Have a.
                    </a>
                    <div class="footer-col">
                        <h3>Unternehmen</h3>
                        <ul>`;

console.log('--- input length', sample.length);
console.log('input:');
console.log(sample);
console.log('---');

const re = /<(\w+)\b[^>]*\bdata-i18n="[^"]+"[^>]*>([^<]*?)<\/\1>/gi;
let m;
while ((m = re.exec(sample)) !== null) {
  console.log('Match: open=' + m[1] + ' close=' + m[4] + ' inner=' + JSON.stringify(m[2]) + ' idx=' + m.index + ' lastIdx=' + re.lastIndex);
}
console.log('done');
