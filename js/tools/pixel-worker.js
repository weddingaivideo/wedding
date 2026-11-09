/*!
 * WeddingAI tools — pixel worker (v1.0.0)
 *
 * Runs the per-pixel background-removal loop OFF the main thread.
 *
 * WHY
 * ---
 * The colour-key algorithm in `remove-background-wedding-portrait` walks
 * every pixel of the photo and computes a colour distance. On a 12 MP
 * wedding photo that is 12 million iterations of a sqrt - roughly 200-500 ms
 * of blocked main thread, during which the tab cannot scroll, the progress
 * bar cannot move and the page looks frozen. On a phone it is much worse.
 *
 * Moving the loop into a Worker is the difference between "the tab died"
 * and "the page stayed responsive". The pixel buffer is TRANSFERRED in both
 * directions, so nothing is copied: the main thread hands over the buffer
 * and gets the finished one back.
 *
 * CSP: `worker-src 'self' blob:` allows this same-origin worker. It was
 * added on 2026-11-09 together with 'wasm-unsafe-eval'.
 *
 * The maths is byte-for-byte the same as the main-thread version that it
 * replaces, so the output is identical:
 *   dist <= innerT              -> alpha 0   (background)
 *   innerT < dist < outerT      -> feathered alpha
 *   dist >= outerT              -> alpha 255 (subject)
 * with outerT = tolerance + feather * 8.
 *
 * PROGRESS (§2.9)
 * --------------
 * The loop is cut into chunks. After every chunk the worker posts a
 * `{progress: 0-100}` message, so the row can show a real percentage
 * instead of an indefinite spinner. The final message carries the finished
 * buffer; the progress messages carry nothing.
 */
'use strict';

var CHUNKS = 24;   // ~24 progress updates per image, independent of size

self.onmessage = function (e) {
  var d = e.data || {};
  var data = new Uint8ClampedArray(d.buffer);
  var bgR = d.bgR, bgG = d.bgG, bgB = d.bgB;
  var innerT = d.innerT;
  var outerT = d.outerT;
  var bandWidth = d.bandWidth;
  var mode = d.mode;
  var total = data.length;
  var i = 0;

  // At least one pixel per chunk, and always a whole number of pixels
  // (4 bytes each) so the loop never stops mid-pixel.
  var pixels = total / 4;
  var perChunk = Math.max(1, Math.floor(pixels / CHUNKS)) * 4;

  while (i < total) {
    var end = Math.min(total, i + perChunk);
    for (; i < end; i += 4) {
      var dr = data[i] - bgR;
      var dg = data[i + 1] - bgG;
      var db = data[i + 2] - bgB;
      var dist = Math.sqrt(dr * dr + dg * dg + db * db);
      var alpha;
      if (dist <= innerT) {
        alpha = 0;
      } else if (dist < outerT) {
        alpha = Math.round(((dist - innerT) / bandWidth) * 255);
      } else {
        alpha = 255;
      }
      if (mode === 'png') {
        // Multiply alpha into existing alpha (preserve any pre-existing transparency in source)
        var prevA = data[i + 3];
        data[i + 3] = Math.round((prevA / 255) * alpha);
      } else {
        // JPG mode: where we'd be transparent, fill with white
        if (alpha < 255) {
          // partial fade: blend toward white by (1 - alpha/255)
          var k = 1 - (alpha / 255);
          data[i] = Math.round(data[i] * (1 - k) + 255 * k);
          data[i + 1] = Math.round(data[i + 1] * (1 - k) + 255 * k);
          data[i + 2] = Math.round(data[i + 2] * (1 - k) + 255 * k);
        }
        data[i + 3] = 255;
      }
    }
    self.postMessage({ progress: (i / total) * 100 });
  }

  self.postMessage({ buffer: data.buffer }, [data.buffer]);
};
