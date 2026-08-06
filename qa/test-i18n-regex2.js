// Test the middleware's i18n regex against a faithful reproduction
// of what the source file has at the related-cards section: the
// h3 element OPENS with <h3> but CLOSES with </h4> (typo in source).

const sample = `garbage before
<a class="related-card" style="x">
                        <h3 style="font-size:1rem;" data-i18n="x.y.h4_text.card1_title.zz">Pet Wedding Video</h4>
                        <p style="font-size:0.875rem;" data-i18n="x.y.p_text.card1_desc.zz">Mix in pet-reaction GIFs for the family group chat gold.</p>
                    </a>
                    <a class="related-card" style="y">
                        <h3 style="font-size:1rem;" data-i18n="x.y.h4_text.card2_title.zz">Cinematic Wedding Trailer</h4>
                        <p style="font-size:0.875rem;" data-i18n="x.y.p_text.card2_desc.zz">Have a serious cinematic trailer plus a fun memes pack — covers every audience.</p>
                    </a>
garbage after`;

// Simulate the middleware's applyDataI18n logic
const dict = {
  'x.y.h4_text.card1_title.zz': 'Hochzeitsvideo mit Haustieren',
  'x.y.p_text.card1_desc.zz':   'Mix in pet-reaction GIFs für den Familienchat.',
  'x.y.h4_text.card2_title.zz': 'Cinematic Wedding Trailer (DE)',
  'x.y.p_text.card2_desc.zz':   'Ernsthaftes Kinotrailer plus ein witziges Memes-Paket — passt zu jedem Publikum.',
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
