/*!
 * WeddingAI tools — on-device face detector (v1.0.0)
 *
 * Mounts `window.weddingAIFaces` on the page and finds faces in a photo
 * WITHOUT the photo ever leaving the device.
 *
 * WHY THIS IS A SEPARATE MODULE
 * ------------------------------
 * The detector is ~840 KB (648 KB of library + 190 KB of model). No visitor
 * who opens the crop tool should pay for it, so nothing is fetched until
 * `detect()` is actually called — the same rule the other vendored libraries
 * on this site follow.
 *
 * It is a separate FILE (not part of js/tools/common.js) for two reasons:
 * only the crop tool needs it, and a separate file has its own cache stamp.
 *
 * TWO BACKENDS, ONE API
 * ---------------------
 *   1. The browser's own `FaceDetector` (the Shape Detection API). Where it
 *      exists it costs NOTHING to download and it is the fastest option.
 *   2. face-api.js (MIT) with the tiny face detector model. This is the
 *      fallback, and it is the one this site can rely on everywhere.
 *
 * face-api.js was chosen over MediaPipe after measuring the shipped files:
 *
 *   @mediapipe/tasks-vision@1.2.2   156 KB JS + 14.6 MB of WASM + a model
 *   @mediapipe/face_detection@0.4   5.8 MB of WASM + 229 KB of model
 *   face-api.js@0.22.2              648 KB of JS + 189 KB of model
 *
 * face-api.js also has zero `eval(`, zero `new Function` and zero
 * `WebAssembly` in the shipped bundle, so it runs under this site's CSP
 * (`script-src 'self' 'nonce-…'`, no 'unsafe-eval') with no change to the
 * policy at all.
 *
 * CSP: the library is fetched with a dynamically inserted same-origin
 * `<script src>`, which `script-src 'self'` allows. The model is fetched
 * with `fetch()`, which `connect-src 'self'` allows. Nothing is requested
 * from a third-party host — not the code, not the model, not the photo.
 *
 * COORDINATES
 * -----------
 * `detect()` returns boxes in the SOURCE image's own pixels (x, y, w, h),
 * whatever size the photo is. The caller scales them to whatever space it
 * works in.
 */
'use strict';

(function () {
  var LIB_DIR = '/js/vendor/face-api-0.22.2';
  var LIB_URL = LIB_DIR + '/face-api.min.js?v=0.22.2';
  var MODEL_DIR = LIB_DIR + '/models';

  // The detector itself works on a 416x416 view of the image, so a bigger
  // input only costs resize time. 1024 keeps the small faces findable
  // without decoding a 24-megapixel original on a phone.
  var MAX_EDGE = 1024;

  var loadPromise = null;
  var backendName = null;

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = src;
      s.async = true;
      s.onload = function () { resolve(); };
      s.onerror = function () { reject(new Error('Could not load ' + src)); };
      document.head.appendChild(s);
    });
  }

  function nativeAvailable() {
    return typeof window.FaceDetector === 'function';
  }

  function loadFaceApi() {
    return loadScript(LIB_URL).then(function () {
      var faceapi = window.faceapi;
      if (!faceapi) throw new Error('face-api.js loaded but window.faceapi is missing');
      // The browser build of TensorFlow.js already knows it is in a
      // browser, but the documented call is harmless and makes the
      // backend explicit.
      if (faceapi.env && faceapi.env.browserEnvironment && faceapi.env.setEnv) {
        faceapi.env.setEnv(faceapi.env.browserEnvironment);
      }
      return faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_DIR).then(function () {
        return faceapi;
      });
    });
  }

  function loadBackend() {
    if (loadPromise) return loadPromise;
    loadPromise = Promise.resolve().then(function () {
      if (nativeAvailable()) {
        backendName = 'native';
        return 'native';
      }
      return loadFaceApi().then(function () {
        backendName = 'face-api';
        return 'face-api';
      });
    }).catch(function (err) {
      // A failed load must not poison the page: clear the cached promise so
      // a second attempt retries instead of failing forever.
      loadPromise = null;
      backendName = null;
      throw err;
    });
    return loadPromise;
  }

  // Draw the photo into a canvas that is small enough to detect on quickly.
  function prepare(img) {
    var w = img.naturalWidth || img.width || 0;
    var h = img.naturalHeight || img.height || 0;
    if (!w || !h) throw new Error('The image has no dimensions.');
    var scale = Math.min(1, MAX_EDGE / Math.max(w, h));
    var canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(w * scale));
    canvas.height = Math.max(1, Math.round(h * scale));
    var ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('This browser cannot read the photo (no 2D canvas).');
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    return { canvas: canvas, scale: scale };
  }

  function detectNative(canvas, scale) {
    var detector;
    try {
      detector = new window.FaceDetector({ fastMode: true, maxDetectedFaces: 20 });
    } catch (err) {
      return Promise.reject(err);
    }
    return detector.detect(canvas).then(function (faces) {
      return faces.map(function (f) {
        var b = f.boundingBox;
        return {
          x: b.x / scale,
          y: b.y / scale,
          w: b.width / scale,
          h: b.height / scale
        };
      });
    });
  }

  function detectWithFaceApi(canvas, scale) {
    var faceapi = window.faceapi;
    var options = new faceapi.TinyFaceDetectorOptions({
      inputSize: 416,
      scoreThreshold: 0.4
    });
    return faceapi.detectAllFaces(canvas, options).then(function (results) {
      return results.map(function (r) {
        return {
          x: r.box.x / scale,
          y: r.box.y / scale,
          w: r.box.width / scale,
          h: r.box.height / scale
        };
      });
    });
  }

  window.weddingAIFaces = {
    /**
     * Find the faces in a photo.
     *
     * @param {HTMLImageElement|HTMLCanvasElement|ImageBitmap} img
     * @returns {Promise<Array<{x:number,y:number,w:number,h:number}>>}
     *          the boxes, in the source image's own pixels. Empty when no
     *          face was found — that is a normal answer, not an error.
     */
    detect: function (img) {
      return loadBackend().then(function (name) {
        var prepared = prepare(img);
        var run = name === 'native'
          ? detectNative(prepared.canvas, prepared.scale)
          : detectWithFaceApi(prepared.canvas, prepared.scale);
        return run.catch(function (err) {
          // A backend that fails on this photo must not break the crop:
          // the caller falls back to the plain off-center bias.
          if (name === 'native') {
            // The native detector can refuse a given image. Retry with the
            // library before giving up - and load the library DIRECTLY,
            // because loadBackend() would pick the native branch again.
            loadPromise = null;
            backendName = null;
            return loadFaceApi().then(function () {
              backendName = 'face-api';
              var again = prepare(img);
              return detectWithFaceApi(again.canvas, again.scale);
            });
          }
          throw err;
        });
      });
    },

    /**
     * Which backend is in use: 'native', 'face-api', or null before the
     * first detection.
     */
    backend: function () { return backendName; },

    /**
     * True when the browser can do it without downloading anything.
     */
    isNative: function () { return nativeAvailable(); }
  };

  window.dispatchEvent(new Event('weddingai-faces-ready'));
})();
