/*!
 * WeddingAI tools — AVIF encoder loader (v1.0.0)
 *
 * Mounts `window.weddingAIImageCodecs` on the page and fetches the AVIF
 * encoder ONLY when the visitor actually asks for an AVIF.
 *
 * WHY AN ENCODER IS NEEDED AT ALL
 * ------------------------------
 * Measured 2026-11-11 on the bundled Chromium, the installed Chrome and the
 * installed Edge, all on a secure origin:
 *
 *   canvas.toBlob(canvas, 'image/avif')  ->  a blob whose `.type` is
 *       image/png. NO browser encodes AVIF through the Canvas API, and it
 *       does not fail loudly - it silently hands back PNG bytes. So a probe
 *       that only asks "did I get a blob?" is a FALSE POSITIVE. The probe
 *       has to look at the blob's TYPE.
 *
 *   canvas.toBlob(canvas, 'image/webp', 1.0)  ->  LOSSLESS. The file
 *       carries a VP8L chunk and decodes back pixel-for-pixel (measured:
 *       worst channel delta 0 on per-pixel noise). Chromium and Firefox
 *       both switch to lossless WebP at quality 1, so the browser's own
 *       encoder is enough for lossless WebP and this tool needs no second
 *       encoder for it.
 *
 *   canvas.toBlob(canvas, 'image/webp') in SAFARI  ->  a PNG. WebKit's
 *       canvas cannot write WebP at all and says nothing about it. A tool
 *       that writes that blob out under a .webp name hands the user a PNG
 *       with the wrong extension, so the tool PROBES the format first and
 *       only offers what the browser can really produce.
 *
 * The encoder is @jsquash/avif (Apache-2.0, verified from the LICENSE
 * inside the package): 3.49 MB of WASM.
 *
 * WHY THIS IS A SEPARATE MODULE
 * ------------------------------
 * The encoder package is ESM and its `encode.js` imports the BARE
 * specifier 'wasm-feature-detect'. A bare specifier only resolves through
 * an import map, so the page carries one:
 *
 *   <script type="importmap">
 *   {"imports":{"wasm-feature-detect":"/js/vendor/jsquash-wfd-1.2.11/index.js"}}
 *   </script>
 *
 * The import map must come before any module script in the document. The
 * middleware's injectScriptNonce() adds a nonce to EVERY <script> opening
 * tag, the import map included, so the inline map is allowed by
 * `script-src 'self' 'nonce-…'`.
 *
 * The 3.4 MB encoder sits behind a dynamic import, so a visitor who only
 * wants JPG, PNG or WebP never downloads it.
 *
 * CSP: the dynamic import is same-origin, which `script-src 'self'` allows,
 * and the WebAssembly instantiation needs 'wasm-unsafe-eval' - which the CSP
 * already carries in both functions/_middleware.js (buildCsp) and _headers.
 * The emscripten glue contains no eval() and no new Function(), so
 * 'unsafe-eval' is NOT needed and must NOT be added.
 *
 * The dynamic import() is the one ES2020 feature in the repository. It lives
 * in this .js module file, not in a tool page's inline script, so the
 * "no ES2020 syntax in the inline scripts" rule still holds where it
 * matters. `window.weddingAIImageCodecs` is the public surface.
 */
'use strict';

(function () {
  var AVIF_URL = '/js/vendor/jsquash-avif-2.1.1/encode.js';

  var cache = {};

  /**
   * Load the encoder package. Resolves with its default export (the
   * encode function). A failed load clears the cached promise, so a second
   * attempt retries instead of failing forever.
   */
  function load(url) {
    if (!cache[url]) {
      cache[url] = import(url).then(function (mod) {
        return mod.default || mod;
      }).catch(function (err) {
        cache[url] = null;
        throw err;
      });
    }
    return cache[url];
  }

  /**
   * Encode an ImageData as AVIF.
   *
   * `quality` is 0..100 (jsquash's own scale, not the Canvas 0..1 one).
   * `speed` is libavif's 0..10, where LOWER is slower and better; 6 is the
   * default and the sweet spot for a tool that has to finish a batch.
   *
   * Returns a Blob. The bytes really are AVIF: an AVIF file is an
   * ISO-BMFF box whose brand is `avif`.
   */
  function encodeAvif(imageData, options) {
    return load(AVIF_URL).then(function (encode) {
      var opts = options || {};
      return encode(imageData, {
        quality: opts.quality === undefined ? 50 : opts.quality,
        qualityAlpha: -1,
        denoiseLevel: 0,
        tileColsLog2: 0,
        tileRowsLog2: 0,
        speed: opts.speed === undefined ? 6 : opts.speed,
        subsample: opts.subsample === undefined ? 1 : opts.subsample,
        chromaDeltaQ: false,
        sharpness: 0,
        tune: 0,
        enableSharpYUV: false,
        bitDepth: 8,
        lossless: false
      }).then(function (buf) {
        return new Blob([buf], { type: 'image/avif' });
      });
    });
  }

  window.weddingAIImageCodecs = {
    encodeAvif: encodeAvif,
    /**
     * True when the loader module itself has run. A tool page can check
     * this before offering the format, so the visitor never picks an
     * option that cannot work.
     */
    ready: true
  };

  // The page's inline script may run BEFORE this deferred module does, so
  // it listens for this event instead of assuming the global already exists.
  window.dispatchEvent(new Event('weddingai-codecs-ready'));
})();
