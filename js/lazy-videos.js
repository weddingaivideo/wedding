/*!
 * lazy-videos.js — defer all <video> downloads until window.load.
 *
 * Why:
 *  - Videos compete with the LCP image (the <video poster>) for bandwidth.
 *    We want the image first, the video bytes after the page is otherwise idle.
 *  - With autoplay + preload="metadata" (the previous default), the browser
 *    fetches the video header immediately on parse, even before images.
 *
 * Behavior:
 *  1. Each <video data-lazy-video> is served with preload="none" so the
 *     browser fetches ZERO bytes until we tell it to.
 *  2. On window.load, we flip preload to "metadata", call .load() to start
 *     the header fetch, and .play() to begin the body download + autoplay.
 *  3. If autoplay is blocked (rare — these are muted), .catch() the rejection
 *     silently. The poster image stays visible, and the user can still hit
 *     play on the controls overlay.
 *
 * Why "metadata" (not "auto") in step 2:
 *  - "auto" = browser fetches the whole video right away. We don't need that
 *    for short looping clips (hero is ~12s). "metadata" + .play() = same
 *    end result for autoplay muted loops, with less wasted bandwidth if the
 *    user leaves the tab.
 *
 * Compatibility:
 *  - document.readyState, window.addEventListener("load"): all browsers.
 *  - video.play() returns a Promise in all evergreen browsers (Chrome 66+,
 *    Firefox 71+, Safari 14.1+). Older browsers no-op on .catch().
 */
(function () {
    "use strict";

    function deferVideos() {
        var videos = document.querySelectorAll("video[data-lazy-video]");
        for (var i = 0; i < videos.length; i++) {
            var v = videos[i];
            // Already deferred (e.g. dynamic injection) — skip.
            if (v.dataset.lazyLoaded === "1") continue;
            v.dataset.lazyLoaded = "1";

            // Step 1: tell the browser metadata is now OK to fetch.
            v.preload = "metadata";
            // Step 2: explicit load() so the metadata request goes out now.
            v.load();
            // Step 3: for autoplay muted videos, kick off the body fetch.
            if (v.autoplay) {
                var p = v.play();
                if (p && typeof p.catch === "function") {
                    p.catch(function () {
                        /* autoplay blocked — poster stays, user can hit play */
                    });
                }
            }
        }
    }

    if (document.readyState === "complete") {
        deferVideos();
    } else {
        window.addEventListener("load", deferVideos, { once: true });
    }
})();
