/*!
 * WeddingAI tools — MP4 encoder loader (v1.0.0)
 *
 * Mounts `window.weddingAIMovie` on the page and fetches the encoder
 * (mediabunny, MPL-2.0) ONLY when the visitor actually asks for an MP4.
 *
 * WHY THIS IS A SEPARATE MODULE
 * ------------------------------
 * mediabunny ships no UMD/global build - it is ESM only - so it cannot be
 * loaded the way the other vendored libraries are (`<script src>` +
 * `window.global`). It has to be imported by a `<script type="module">`.
 *
 * That module is THIS file, and it is tiny (a few hundred bytes). The 706
 * KB encoder itself is behind a dynamic import, so a visitor who only wants
 * the PNG frames never downloads it. Every other vendored library on this
 * site follows the same rule: fetch it on first use, not on page load.
 *
 * CSP: the dynamic import is same-origin, which `script-src 'self'` allows.
 * The page needs no other change.
 *
 * The dynamic import() is the one ES2020 feature in the repository. It
 * lives in this .js module file, not in a tool page's inline script, so the
 * "no ES2020 syntax in the inline scripts" rule still holds where it
 * matters. `window.weddingAIMovie` is the public surface.
 */
'use strict';

(function () {
  var promise = null;
  var MEDIA_URL = '/js/vendor/mediabunny/mediabunny.min.mjs?v=1.65.2';

  window.weddingAIMovie = {
    /**
     * Load mediabunny. Resolves with the module namespace.
     * A failed load clears the cached promise, so a second click retries
     * instead of failing forever.
     */
    load: function () {
      if (!promise) {
        promise = import(MEDIA_URL).catch(function (err) {
          promise = null;
          throw err;
        });
      }
      return promise;
    }
  };

  // The page's inline script may run BEFORE this deferred module does, so
  // it listens for this event instead of assuming window.weddingAIMovie
  // already exists.
  window.dispatchEvent(new Event('weddingai-movie-ready'));
})();
