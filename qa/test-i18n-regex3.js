const sample = `garbage before
<a class="related-card" style="x">
                        <h3 style="font-size:1rem;" data-i18n="x.y.h4_text.card1_title.zz">Pet Wedding Video</h4>
                        <p style="font-size:0.875rem;" data-i18n="x.y.p_text.card1_desc.zz">Mix in pet-reaction GIFs for the family group chat gold.</p>
                    </a>
                    <a class="related-card" style="y">
                        <h3 style="font-size:1rem;" data-i18n="x.y.h4_text.card2_title.zz">Cinematic Wedding Trailer</h4>
                        <p style="font-size:0.875rem;" data-i18n="x.y.p_text.card2_desc.zz">Have a serious cinematic trailer plus a fun memes pack.</p>
                    </a>
                    <h3 data-i18n="404.h3_text.company.x">Company</h3>
                    <h3 data-i18n="404.h3_text.contact.x">Contact</h3>
garbage after`;

console.log('=== input length', sample.length, '===');
console.log(sample);
console.log('===');

const dict = {
  'x.y.h4_text.card1_title.zz': 'Hochzeitsvideo mit Haustieren',
  'x.y.p_text.card1_desc.zz':   'Mix in لpet-reaction GIFs fur Familienchat.',
  'x.y.h4_text.card2_title.zz': 'Cinematic Wedding Trailer (DE)',
  'x.y.p_text.card2_desc.zz':   'Ernsthaftes Kinotrailer plus ein witziges Memes-Paket.',
  '404.h3_text.company.x': 'Unternehmen',
  '404.h3_text.contact.x': 'Kontakt',
};

let result = sample.replace(
  /<(\w+)\b[^>]*\bdata-i18n="([^"]+)"([^>]*)>([\s\S]*?)<\/\1>/g,
  (m, tag, key, restAttrs, inner) => {
    const v = dict[key];
    if (v == null) return m;
    const cleanOpen = m.slice(0, m.indexOf('>') + 1).replace(/\s*data-i18n="[^"]*"/, '');
    return cleanOpen + v + `</${tag}>`;
  }
);
console.log('=== output ===');
console.log(result);
