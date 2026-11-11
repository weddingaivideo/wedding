/*!
 * WeddingAI tools — GIF encoder loader (v1.0.0)
 *
 * Mounts `window.weddingAIGif` on the page and fetches the encoder
 * (gifenc, MIT) ONLY when the visitor actually asks for a GIF.
 *
 * WHY THIS IS A SEPARATE MODULE
 * ------------------------------
 * gifenc ships no UMD/global build - dist/gifenc.js is CommonJS and
 * dist/gifenc.esm.js is an ES module - so it cannot be loaded the way
 * the other vendored libraries are (`<script src>` + `window.global`).
 * It has to be imported by a `<script type="module">`.
 *
 * That module is THIS file, and it is tiny (a few hundred bytes). The
 * 9 KB encoder itself is behind a dynamic import, so a visitor who only
 * wants the PNG frames never downloads it. Every other vendored library
 * on this site follows the same rule: fetch it on first use, not on
 * page load.
 *
 * This mirrors js/tools/movie-loader.js (mediabunny), which is the same
 * pattern for the MP4 encoder.
 *
 * The ESM bundle is self-contained - no bare specifiers, so no import
 * map is needed (unlike the jsquash packages).
 *
 * CSP: the dynamic import is same-origin, which `script-src 'self'`
 * allows. The page needs no other change.
 *
 * The dynamic import() is the one ES2020 feature in the repository. It
 * lives in this .js module file, not in a tool page's inline script, so
 * the "no ES2020 syntax in the inline scripts" rule still holds where
 * it matters. `window.weddingAIGif` is the public surface.
 */
'use strict';

(function () {
  var promise = null;
  var GIF_URL = '/js/vendor/gifenc/1.0.3/gifenc.esm.js?v=1.0.3';

  window.weddingAIGif = {
    /**
     * Load gifenc. Resolves with the module namespace
     * (GIFEncoder, applyPalette, quantize, nearestColorIndex, ...).
     * A failed load clears the cached promise, so a second click retries
     * instead of failing forever.
     */
    load: function () {
      if (!promise) {
        promise = import(GIF_URL).catch(function (err) {
          promise = null;
          throw err;
        });
      }
      return promise;
    }
  };

  // The page's inline script may run BEFORE this deferred module does, so
  // it listens for this event instead of assuming window.weddingAIGif
  // already exists.
  window.dispatchEvent(new Event('weddingai-gif-ready'));
})();
