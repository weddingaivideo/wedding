# Free Tools Suite — Full Optimization & Upgrade Backlog

**Date:** 2026-11-09 · **Scope:** the 13 `/tools/*` pages + the shared layer they
depend on (`js/tools/common.js`, `styles/tools.css`, `js/i18n.js`, the i18n
shards, the CSP, and the pre-deploy gate).

**Why this file exists:** every item below was measured in the repository or
read from a vendor's own pricing page. Nothing here is a guess. The user
decides item by item, so each row carries its own cost and its own cost of
**not** doing it.

**Cost legend**

| mark | meaning |
|---|---|
| 🟢 | **$0** — no purchase, no vendor, no upload |
| 🔵 | **$0 but carries a cost** — bandwidth, bundle weight, CSP change, or a licence constraint |
| 🟡 | **pay-as-you-go** — a real per-unit price, listed below |
| 🔴 | **breaks the "nothing leaves the device" promise** — needs an explicit product decision |

> `VERIFIED` = read on the vendor's own pricing/docs page on 2026-11-09.
> `UNVERIFIED` = could not be confirmed on an official page.

---

## EXECUTION STATUS (same day, commit `e2e9d1a8`)

The owner approved the 🟢 and 🔵 classes for execution. Here is what landed.

| item | status | note |
|---|---|---|
| **44 of 144 tool pages were dead** | ✅ **fixed** | not in this list — the machine translator had translated the CODE (`function` → `Funktion`), so the whole inline script was a SyntaxError and the tool was inert while the page still returned 200. The English page is now the single source of truth; `scripts/propagate-tool-js.py` + `scripts/check-tool-script-syntax.py` (286 scripts, 0 broken). |
| §1.1 real ZIP | ✅ | fflate 0.8.3, `common.js downloadZip()` |
| §1.2 PDF export | ✅ | collage + budget + seating chart (jsPDF 4.2.1); the tables claimed PDF and there was none |
| §1.4 share-link claim | ✅ **aligned, not built** | the seating chart claimed a "share link" that does not exist → the claim now reads "Printable PNG + PDF". A server-side share link would break the no-upload promise, so it stays in §5 for the owner. |
| §1.5 print styles | ✅ | full `@media print` block in `styles/tools.css` |
| §2.1 interactive crop | ✅ | **native drag frame, not Cropper.js v2** — v2 keeps its UI in shadow DOM and ships zero aria-labels, so its handles could not be localized or named |
| §2.10 Service Worker | ✅ | all 144 tool pages |
| §2.5–2.9 engineering | ✅ | **Worker** for the pixel loop (`js/tools/pixel-worker.js`, buffer transferred, progress in ~24 chunks) · **createImageBitmap** with an explicit `{imageOrientation:'from-image'}` · **memory hygiene** — every decoded image is now released through `releaseImage()`, including on the error path (the release used to sit at the end of the `try` block, so an exception skipped it) · **real progress** — the rows show a percentage instead of an indefinite spinner. `fileToImage()` changed CONTRACT: it returns an `ImageBitmap`, `loaded.url` is `null`, and `loaded.release()` is the teardown call. |
| §3.1 HEIC decode | ✅ | heic2any + Safari-native-first; the "only works in Safari" prose was rewritten in 11 languages |
| §3.2 real MP4 | ✅ | **mediabunny 1.65.2 (MPL-2.0), 706 KB ESM** — loaded on demand from `/js/tools/movie-loader.js`, so nobody downloads it unless they ask for the MP4. The clip is 5 s, 1080×1920, 30 fps, with the motion **interpolated** between the five key frames (a fractional `frame` value). The button appears only where `VideoEncoder.isConfigSupported()` says H.264 is available — a native, free probe — so no browser loses the PNG frames. |
| §3.3 pica resampling | ✅ | compress + HEIC |
| §3.4 MODNet AI matting | ✅ | 6.3 MB quantized ONNX + ONNX Runtime Web. **First run downloads ~17 MB** from this origin. The colour key stays the default so nobody gets a surprise download. |
| §3.5 CSP | ✅ | `'wasm-unsafe-eval'` **and** `worker-src 'self' blob:` in `functions/_middleware.js` + `_headers`. The second is not optional — pica and heic2any both build their Worker from a `blob:` URL, and without it pica silently degrades. |
| runtime string i18n | ✅ | middleware injects `tools.copy`; `common.js` exposes `t(alias, fallback, params)`; 31 new keys × 11 languages |

**Verification:** the AI path and the crop frame were driven end-to-end in
Chromium under the **live** CSP (`scripts/verify-ai-background.py`,
`scripts/verify-crop-stage.py`). The pre-deploy gate is green: 0 errors,
0 warnings, READY TO DEPLOY.

The §2.5–2.9 pass added three more browser checks, because none of those
four items can be verified by reading the code:

| script | what it proves |
|---|---|
| `scripts/verify-worker-progress.py` | the Worker's output is **byte-for-byte identical** to the main-thread maths (both `png` and `jpg` mode), the worker was actually **fetched**, and the progress bar appeared. Asserting only the output would pass with the worker disabled — the fallback produces the same bytes and the same green row. |
| `scripts/verify-tool-suite-smoke.py` | all seven tools that decode a file through `fileToImage()` still work after the contract change. The contract change is silent: an `ImageBitmap` has no `.complete`, and `URL.revokeObjectURL(null)` is a no-op, so a tool that was not updated still shows a green row. |
| `scripts/verify-exif-orientation.py` | a portrait phone photo is not rendered sideways: `<img>` → 100×200, `createImageBitmap(blob, {imageOrientation:'from-image'})` → 100×200. |
| `scripts/verify-mp4-export.py` | the MP4 is a **real** file: it is read back with mediabunny itself (5.00 s, 1080×1920, `avc`), and the exported PNG is compared against the on-screen preview — the mean difference must stay under 12/255, because the export used to draw the 540×960 layout into the top-left quarter of a 1080×1920 canvas. |

**Still needs the owner:** §4 (paid services) and §5 (promise-breaking
options) were deliberately NOT executed, and §9 still has five open
questions.

---

## 0. The four constraints every option inherits

These are not preferences; they are what the repo actually allows.

1. **CSP** — `script-src 'self' 'nonce-…'` (`functions/_middleware.js:77`) plus a
   short allowlist. **No CDN script can be loaded.** A library must be
   self-hosted under `/js/`. There is **no `'wasm-unsafe-eval'`** in either
   `buildCsp()` or `_headers`, so **every WebAssembly library is blocked**
   until that is added to *both* places.
2. **No build step** — no `package.json`, no bundler. A library needs a
   UMD/global build, or an ESM file loaded with `<script type="module">`.
3. **11 languages** — tool pages are localized through `data-i18n`; any library
   with its own visible strings needs 11-language overrides.
4. **No price on a tool page** — per AGENTS.md. This also means no library
   that renders an upgrade prompt, and no "free tier / pay" UI.

**Also true of this repo:** `functions/_middleware.js` calls `shouldSkip()`
(`functions/_middleware.js:291`), which returns `true` for any path with a
file extension and for `/i18n/`, `/api/`, `/admin/`. So **static assets and
shard fetches do not consume the Workers Free quota** — only HTML page views
and API calls do.

---

## 1. 🟢 Fix "it looks like it does it, but it doesn't" — $0, highest ROI

These are the items where the site currently *claims* a capability that the
code does not implement. Each is cheap to fix and each removes a
claim/implementation mismatch (the same class of defect as the stale-figure
traps in AGENTS.md).

| # | Item | Evidence | Cost | Notes |
|---|---|---|---|---|
| 1.1 | **Make "Save all" produce a real ZIP** | `js/tools/common.js:252` `downloadZip()` fires sequential auto-downloads 120 ms apart. Browsers block or spam multiple downloads; the user gets N loose files | **$0** + `fflate` 32 KB UMD (MIT) | Replaces the stub in one function. Affects compress / crop / heic / add-text / remove-bg |
| 1.2 | **Add a real PDF export** | `photo-collage` ("PNG + PDF + 4K + print + share"), `seating-chart` ("PNG + PDF + share link"), `budget-calculator` all say PDF; the only buttons are `Download PNG` / `Export PNG` / `Export CSV` / `Print` | **$0** + `jspdf` 410 KB UMD (MIT) | One `addImage(canvas, 'PNG', …)` per exported canvas |
| 1.3 | **Or drop the PDF claim** | same | **$0** | Cheaper. But the comparison tables sell "PNG + PDF" as the differentiator vs Canva — dropping it weakens the page |
| 1.4 | **Implement the seating chart's "share link" / "QR"** | The comparison table claims "Printable PNG + PDF + share link" for us and "PNG + PDF + QR share" for SeatPlan.io; there is no share button, no `navigator.share`, no `clipboard`, no QR. All state is `localStorage` only | **$0** | A share link needs a server-side store → see §4.3 |
| 1.5 | **Fix `@media print`** | The only print rule in `styles.css` hides `.site-header`, `.mobile-menu-toggle`, `.hero-cta`, `.faq-item summary::after`. The **ad slots, the tool control panel, the Export/Print buttons and the tool footer all print** | **$0** | `styles/tools.css` has no `@media print` at all. Two `Print` buttons ship a broken print |
| 1.6 | **Reconcile the "5 frames, not a video" copy** | `video-invitation-maker` is honest about it (documented trade-off). Verify it stays honest if mediabunny lands | **$0** | — |

---

## 2. 🟢 Capability upgrades — $0, self-hosted libraries

All four are MIT/Apache, UMD, and **carry no user-facing UI strings** (verified
by grepping the shipped dist), so they cost 0 extra i18n work.

| # | Tool | Upgrade | Library | Size | Cost |
|---|---|---|---|---|---|
| 2.1 | `crop-wedding-photo-for-reels` | Interactive crop: drag the frame, zoom, rotate, pan. Today it is a fixed ratio + an off-centre bias heuristic, so a couple near the edge gets cut off | `cropperjs@2.3.1` | 50 KB | 🟢 $0 |
| 2.2 | `add-text-to-wedding-photo` | Drag / rotate / freely place the text block. Today: 9 preset positions + auto-shrink | `cropperjs` (crop a text canvas) or `fabric` | 50 KB / 292 KB | 🟢 $0 |
| 2.3 | `wedding-photo-collage` | Drag photos between cells, reorder, per-cell zoom. Today: 6 fixed grids, auto-placed | `fabric` / `konva` | 292 / 193 KB | 🟢 $0 |
| 2.4 | `wedding-photo-book-planner` | Same free placement for page layouts | `fabric` / `konva` | 292 / 193 KB | 🟢 $0 |

> ⚠️ **Cropper.js v2 is a rewrite, not an upgrade.** v2 GA'd as Web
> Components with shadow DOM; the v1 API (`getCroppedCanvas`, `aspectRatio`)
> is gone. Budget a day, and do not paste v1 snippets.

> 💡 **The pie chart already exists.** `budget-calculator` draws a hand-written
> canvas pie (`<canvas id="bg-chart">` + `renderChart()`) with an HTML legend.
> It needs **no** Chart.js — the only real gaps there are an accessible
> text/table alternative and label i18n. Chart.js would cost 205 KB *and*
> 11 languages of English-default overrides (tooltip / legend / axis).

**Also free, no library:**

| # | Item | Detail |
|---|---|---|
| 2.5 | **Web Worker for pixel loops** | `remove-background` runs a per-pixel loop on the main thread; a 12 MP photo freezes the tab. `default-src 'self'` covers `worker-src`, so a same-origin Worker is allowed — no CSP change |
| 2.6 | **`createImageBitmap` + `OffscreenCanvas`** | `common.js:51` `fileToImage()` uses `new Image()` + object URL. `createImageBitmap` decodes off the main thread and applies EXIF orientation explicitly |
| 2.7 | **EXIF orientation correctness** | The compress page *honestly* says the Canvas API drops EXIF. But orientation is a different matter — verify portrait iPhone photos are not rendered sideways |
| 2.8 | **Memory hygiene** | `URL.revokeObjectURL` is called on some paths but not all (e.g. `heic-to-jpg` `processOne` never revokes the preview URL it created in `addFiles`). Large batches leak |
| 2.9 | **Real progress reporting** | Long operations show a spinner, not a percentage. `heic2any` and mediabunny both expose progress callbacks |
| 2.10 | **Service Worker on tool pages** | `sw.js` exists and 1,428 pages register it, but **no tool page does** (`serviceWorker` hits = 0). Its precache list has no tool assets, so tools do not work offline |
| 2.11 | **Face-aware auto-crop** | Replace the off-centre heuristic with actual face detection (mediapipe face detection / face-api.js) so the couple is always framed |
| 2.12 | **AVIF / WebP-lossless output** | `compress` emits jpeg/png/webp only. AVIF is the current best compression for delivery |
| 2.13 | **EXIF read/keep/strip as a first-class option** | `exifr` is a small, dependency-free EXIF parser | Would let the compress tool *keep* EXIF instead of only documenting that it drops it |
| 2.14 | **Target-size mode** | "Compress to exactly 2 MB" is what users actually ask for; today the control is a quality slider |
| 2.15 | **DOM→PNG renderer** | `save-the-date`, `invitation`, `photo-book`, `seating-chart` all hand-roll canvas rendering. `modern-screenshot` (29 KB UMD, MIT) renders the DOM directly and keeps the HTML/CSS as the single source of truth |

> ✅ **2.5 – 2.9 were implemented on 2026-11-09** (execution status above).
> Three corrections to the analysis above, found while building them:
>
> * **2.5: `worker-src` was NOT covered by `default-src 'self'`.** The
>   vendored libraries build their Worker from a `blob:` URL, and `blob:`
>   is not `'self'`. The explicit `worker-src 'self' blob:` directive is
>   required — without it pica silently degrades to its JS resampler.
> * **2.6: `createImageBitmap` needs the EXPLICIT
>   `{imageOrientation: 'from-image'}` option.** The plain call did not
>   reliably apply the EXIF rotation, so a portrait phone photo would have
>   been rendered sideways. `OffscreenCanvas` was NOT needed and is not
>   used: the pixel buffer is transferred to a Worker instead, and the
>   canvas has to stay on the main thread anyway to be encoded and
>   downloaded.
> * **2.8: the release used to sit at the END of the `try` block**, so an
>   exception skipped it and the decoded image stayed alive for the rest
>   of the session. It is now in a `finally`.


---

## 3. 🔵 $0 but with a real cost attached

| # | Item | Cost | The trade-off |
|---|---|---|---|
| 3.1 | **HEIC decoding in every browser** — `heic2any@0.0.4`, MIT, 1.32 MB, **asm.js** | 🔵 $0 | The single biggest real user loss today: only Safari decodes HEIC, so the tool is dead on Chrome/Edge/Firefox. heic2any is **CSP-clean** (0 `WebAssembly` hits, 2 `asm[` hits in the shipped dist → no `'wasm-unsafe-eval'` needed). Costs 1.32 MB on first use. Unmaintained since 2023-03 → vendor it, freeze the version. Drops EXIF, animation → first frame only. `libheif-js` direct is LGPL-3.0 → not worth the licence question |
| 3.2 | **Real MP4 export** — `mediabunny@1.65.2`, MPL-2.0 | 🔵 $0 | 706 KB, **ESM only** (no UMD) → `<script type="module">`. WebCodecs `VideoEncoder` is Chrome/Edge 94+, Safari 16.4+, Firefox 130+, **but not Firefox for Android**. Turns "5 PNG frames + go edit it in CapCut" into an actual downloadable video. MPL-2.0 is file-level copyleft — fine as a dependency |
| 3.3 | **High-quality resize** — `pica@10.0.3`, MIT, 53 KB | 🔵 $0 | The wasm resampler is **inlined in the bundle**; under the current CSP the constructor throws, `has_wasm()` returns false, and it **silently falls back to the plain JS resampler** — the page works and the quality quietly degrades. Either add `'wasm-unsafe-eval'` or accept the JS path |
| 3.4 | **Browser-side AI segmentation** | 🔵 $0 | See §4.1 for the model choice. Needs `'wasm-unsafe-eval'` (ONNX Runtime Web) and a one-time model download |
| 3.5 | **Self-host the vendored libraries** | 🔵 $0 | Cloudflare Pages overrides `Cache-Control`, so the cache-bust mechanism is the `?v=` query string (as already used for `/js/main.min.js?v=3.21`). Every vendored file needs a `?v=` bump on change. `_headers` gives `/js*` a 4-hour CDN TTL — a 1.32 MB library therefore re-downloads for every visitor whose cache expires |

---

## 4. 🟡 Paid services — unit prices, and what they cost at this site's scale

Assume a small site: **100–2,000 tool uses/month** (a guess; the site's own
analytics should confirm it).

### 4.1 AI background removal — the one place a paid API would buy real capability

**Today:** `remove-background-wedding-portrait` is a color-distance cut. The
page says so honestly: *"Outdoor scenes and textured walls won't strip
cleanly with a backdrop-color remover; those need a full AI semantic
segmentor."*

#### 4.1a — Keep it on-device (🟢 $0, no upload, no licence risk) — **recommended**

| Model | Licence | Size | Verdict |
|---|---|---|---|
| **`Xenova/modnet`** | **Apache-2.0** | ONNX 25.9 MB · fp16 13.0 MB · **quantized 6.6 MB** | **Best commercial-safe browser option.** 6.6 MB is a plausible first-run download on mobile |
| `imgly/isnet-general-onnx` | MIT | ONNX 176.1 MB | Higher quality, far heavier |
| `BritishWereWolf/IS-Net`, `Carve/isnet`, `jellybox/isnet-general-use` | Apache-2.0 | — | Other ISNet ports |
| `briaai/RMBG-1.4` | **bria-rmbg-1.4 — non-commercial** | quantized 44.4 MB | ❌ Cannot ship on a commercial site without a BRIA agreement |
| `onnx-community/ISNet-ONNX` | **AGPL-3.0** | — | ❌ Copyleft |
| `@imgly/background-removal` (the library) | **AGPL-3.0** | lib 167 KB + ORT wasm 11.3 MB + model ~44 MB | ❌ Copyleft + ~45 MB. Note: several 2026 blogs and search snippets call it **MIT** — the package's own `LICENSE.md` is the full AGPL-3.0 text |

Runs via `@huggingface/transformers@4.3.2` (Apache-2.0, 574 KB + ORT wasm),
which supports **self-hosting the model** (`env.allowRemoteModels=false`,
`env.localModelPath='/models/'`) — required to keep the "no upload" promise and
to avoid a runtime dependency on a CDN. Cost: **$0 marginal + 6.6–44 MB first-run
download + `'wasm-unsafe-eval'` in the CSP**.

#### 4.1b — Cloud API (🟡 pays per image, 🔴 breaks the promise)

| Service | Unit price (VERIFIED) | Free tier | 100/mo | 2,000/mo | Licence / catch |
|---|---|---|---|---|---|
| Replicate `lucataco/remove-bg` | **~$0.00022/run** | — | **~$0.02** | **~$0.44** | Apache-2.0. Cheapest by 100× |
| Replicate `851-labs/background-remover` | ~$0.00046/run | — | ~$0.05 | ~$0.92 | — |
| Segmind `bg-removal` | $0.0072/GPU-s ≈ **$0.00224/req** | "free tier" (numeric allowance UNVERIFIED) | ~$0.22 | ~$4.48 | ⚠️ **Model card is CC BY-NC-ND — non-commercial.** Not shippable |
| Replicate `cjwbw/rmgb` (RMBG 1.4) | ~$0.00098/run | — | ~$0.10 | ~$1.96 | bria-rmbg-1.4 — non-commercial |
| **IMG.LY AI Gateway** (Rmbg 2.0) | **$0.022/req** | not stated | ~$2.20 | ~$44 | dedicated BG-removal price page 404s; this is the AI Gateway rate |
| **Replicate `bria/remove-background`** | **$0.018/output image** | — | ~$1.80 | ~$36 | RMBG 2.0, commercial use |
| **fal.ai `bria/background/remove`** | **$0.018/gen** ($0.03 guided) | sandbox preview | ~$1.80 | ~$36 | commercial use w/ licensed training data |
| **Bria AI** | **$0.018/img** (guided $0.025, Eraser $0.032, Erase FG $0.05, **video $0.04/s**) | 100 generations, no card | ~$1.80 | ~$36 | Self-host option needs a paid licence + NVIDIA GPU |
| **Photoroom API** | Basic **$0.02/image**, Plus **$0.10/image** | 10 free prod calls + 1,000 sandbox/mo | ~$2.00 | ~$40 | Monthly only, no annual |
| **remove.bg** | 40 cr/$9 … 2,800 cr/$389 … 50,000 cr/$3,950 per month | first 50 API calls/mo free | ~$19.50 | ~$389 | ❌ **Service ends 1 Dec 2026** (BG removal moves to Leonardo.Ai/Canva). Do not build on it |
| Adobe Firefly Services / Photoshop API v2 | **no public price** (enterprise rate card) | none | — | — | "Remove background" confirmed as a v2 service; price is contract-only |
| Clipdrop API | **no public price** (contact sales) | consumer quotas only | — | — | — |
| Pillow AI | **pricing page returns HTTP 500** | — | — | — | — |

> **The arithmetic that matters:** the cheapest shippable cloud path is
> ~$0.00022–$0.018/image → **$0.44–$36/month at 2,000 uses**. The on-device
> MODNet path is **$0** and keeps the promise. The cloud path also has to be
> *labelled* as uploading the image — which AGENTS.md's no-price rule and the
> "nothing leaves your device" copy both push back against.

### 4.2 Video encoding — only relevant if §3.2 lands

**The browser is the answer.** WebCodecs / MediaRecorder encode at **$0** with
no upload. Every server-side option below also breaks the "100 % client-side"
copy (AGENTS.md) for no capability gain.

| Service | Price (VERIFIED) | Free tier | Notes |
|---|---|---|---|
| **mediabunny (browser)** | **$0** | — | 706 KB ESM, WebCodecs hardware encode. **The right answer** |
| **Cloudflare Stream** | storage **$5/mo per 1,000 min**; delivery **$1 per 1,000 min** | pay-as-you-go, no free tier | **Ingress + encoding free**, no egress fee. Cheapest host if finished videos live on CF. No Pages binding — call the REST API |
| **Mux** | on-demand 1080p: input **$0**, storage **$0.003/min/mo**, delivery **$0.001/min** after 100K free; live 1080p + input $0.03125/min | 100K free delivery min/mo, ≤10 videos stored, on-demand only | Launch $20/mo → $100 credit; Scale $500/mo → $1,000 credit. Only if you want managed streaming |
| **Transloadit** | **Community: free forever, 5 GB/mo**, 0.5 GB max file, no overage (it stops at 5 GB) | Lite $29/mo (15 GB, overage $2/GB); Pro $54/mo annual / $69 monthly (40 GB, overage $1.80/GB) | Billed **per GB processed, not per minute** |
| **AWS MediaConvert** | Basic **$0.0075**/normalized-min (first 100K), $0.0053 (next 900K); Professional $0.0120 → $0.0036 | none published | HD = 2× multiplier. Overkill, complex pricing |
| **Shotstack** | PAYG 50 min/$10 = **$0.20/min**; Starter $39/mo 250 min ($0.156); Pro $99/mo 750 min ($0.132); Scale $199/mo 2,000 min ($0.10); Volume $499/mo 10,000 min ($0.05) | 10 credits, 30 days | Agency-scale |
| **Creatomate** | Essential $45/mo annual ($54 monthly) 2,000 credits; Growth $108/mo 10,000; Beyond $274/mo 50,000. A 30 s 720p render = **6.91 credits** | 50 credits, no card — **but preview quality only, ≤480 px** | The free tier cannot produce a deliverable |
| **Cloudinary** | $0 + **25 monthly credits**; Plus $99/mo ($89 annual) 225 credits; Advanced $249/mo ($224) 600 credits | 1 credit = 1,000 transforms **or** 1 GB bandwidth (paid: 2 GB video BW) | Only if media moves to Cloudinary |

### 4.3 Storing user artefacts (invitation cards, seating charts, share links)

| Service | Free | Paid | Verdict |
|---|---|---|---|
| **Cloudflare R2** | **10 GB-month storage · 1M Class A · 10M Class B ops/mo · egress FREE** | $0.015/GB-mo · $4.50/M Class A · $0.36/M Class B | ✅ **Best.** Store the PNG in R2, the design JSON in D1, serve through a Pages Function R2 binding so it stays on `'self'` and the CSP needs no edit |
| **Cloudflare D1** | 5M rows read/day · 100k rows written/day · 5 GB · 10 DBs | $0.001/M reads · $1.00/M writes · $0.75/GB-mo | ✅ Holds the small design JSON. Rows are **scanned**, not returned — a big row costs the same as a small one |
| **Cloudflare KV** | 100k reads/day · 1k writes/day · 1 GB | $0.50/M reads · $5.00/M writes | Already wired (`functions/api/quote.js:178`). Poor fit for blobs (per-key accounting) |
| Durable Objects | 100k req/day · 13,000 GB-s/day · SQLite 5 GB | $0.15/M req · $12.50/M GB-s | Overkill here |
| Backblaze B2 | first **10 GB always free** | $0.00695/GB-mo, $0.01/GB egress past 3× | The only alternative that also matches $0, but adds an S3/credential path |
| Supabase Storage | 1 GB · 5 GB egress · 50 MB max upload | Pro $25/mo | ❌ Free projects **pause after 1 week inactivity** |
| Bunny Storage | — | $0.01/GB per region, **$1/mo minimum** | ❌ $1/mo for 10 MB — 3× Cloudflare at this scale |

### 4.4 Cloudflare platform items

| Product | Free tier | Paid |
|---|---|---|
| **Workers AI** | **10,000 Neurons/day** | $0.011/1,000 Neurons. Catalog has **no background-removal model**; closest is `stable-diffusion-v1-5-inpainting` + a moondream detection mask. `m2m100-1.2b` translation $0.342/M tokens (input *and* output). `resnet-50` $2.51/M images |
| **Cloudflare Images** | 5,000 unique transformations/mo | $0.50/1,000 transformed · $5/100,000 stored images/mo (→ **$5/mo minimum**) · $1/100,000 delivered |
| **Pages Functions** | 100,000 requests/day (Workers Free) | Static assets and `/i18n/` bypass the middleware (`shouldSkip`), so only page views and API calls consume it |

### 4.5–4.7 — fonts, CDN, observability, email

#### 4.5 Fonts (the tools render text onto canvas, so fonts must load in the browser)

| Service | Price (VERIFIED) | Notes |
|---|---|---|
| **Google Fonts** | **$0** | Most fonts SIL OFL 1.1, some Apache-2.0. The *Developer API* needs a key, but **self-hosting the woff2 needs nothing**. Best choice |
| **Bunny Fonts** | **$0** | "use them without any fees in any of your products & projects". Privacy-friendly Google-Fonts drop-in |
| **Fontshare** | **$0** | Good wedding-script fonts. Commercial clause UNVERIFIED (license page is JS-rendered) |
| **Fontself** | Software one-time: Maker for Illustrator $98 (→$39 promo), bundle $78 (→$59) | Only if you author your own fonts |
| **Adobe Fonts** | 5,000+ fonts free *with an Adobe account*, but **full web embedding needs a paid Creative Cloud plan** (exact rule UNVERIFIED) | Not needed for a free tool |
| Cloudflare font proxying | no dedicated product; a Worker proxy = Workers requests (Free 100K req/day; Paid $5/mo min, 10M req/mo incl., +$0.30/M) | Possible privacy win, but adds a hop |

#### 4.6 CDN / static hosting

| Service | Price (VERIFIED) | Notes |
|---|---|---|
| **Cloudflare Pages** | **$0** — 20,000 files/site, **25 MiB max single asset**, 500 builds/mo; Functions on Workers Free 100K req/day | A 1.3 MB heic2any bundle fits easily → **just commit it to the repo** |
| **Cloudflare R2** | 10 GB-mo free, 1M Class A, 10M Class B/mo; $0.015/GB-mo, $4.50/M Class A, $0.36/M Class B, **egress free** | Only if a separate asset origin is needed |
| **jsDelivr** | **$0** — "a free, fast, and reliable CDN for JS and open source" | Hotlink rules / rate limits UNVERIFIED (AUP is JS-rendered). Self-host instead |
| **unpkg** | **$0** — "provided free, as-is, **without a contractual SLA**" | No SLA — do not hotlink a commercial site |
| **Bunny CDN** | **$1/mo minimum**; EU&NA **$0.01/GB**, Asia&Oceania $0.03, S America $0.045, ME&Africa $0.06; volume network from $0.005/GB | Asia traffic is 3× R2. Only if you leave Cloudflare |

#### 4.7 Observability, email, and other Cloudflare

| Service | Free tier | Paid price | Fit |
|---|---|---|---|
| **Sentry** | Developer $0: 1 user, **5,000 errors/mo**, 5 GB logs, 5M spans, 30-day lookback | Team **$26/mo annual** ($29 monthly) 50K errors; Business $80/mo annual ($89); overage $0.0003625/error | Free tier is plenty |
| **Better Stack** | $0: 10 monitors/heartbeats, 100K exceptions/mo, 5K replays, 3 GB logs (3 days) | from **$34/mo ($29 annual)** per responder license; status page +$15/mo | Free tier covers uptime |
| **Cloudflare Web Analytics** | **free**, cookie-free | $0 | Already injected at the edge |
| **Resend** | $0: **3,000/mo, 100/day**, 3 domains, 3 inboxes, 30-day retention | Pro **$20/mo**: 50,000/mo, extra $0.90/1,000, 10 domains, **no daily cap**; Scale $90/mo 100,000/mo; domains add-on $20/mo; dedicated IP $30/mo | Already wired. The **100/day cap** is the risk to watch — but note the Oct 2026 lead losses in AGENTS.md were caused by the MX deletion and Resend's suppression list, **not** by this cap. $20/mo is the cheapest insurance against a silent-suppression incident |
| **Postmark** | $0: **100 emails/mo, no overages** | Basic $15/mo 10,000 + $1.80/1,000; Pro $16.50/mo + $1.30/1,000 | Free tier unusable; ~10× Resend per email |
| **AWS SES** | new-account $200 credits / 6-month free plan (SES-specific allowance UNVERIFIED) | **$0.10/1,000 outbound** + $0.12/GB attachments; Global Endpoints +$0.03/1,000 | Cheapest per email, worst ops/deliverability story |
| **Argo Smart Routing** | — | starts $5/mo; **per-GB rate not published publicly** (dashboard only) | Don't buy — the 2026-10-28 outage was DNS/custom-domain deactivation, not routing |
| **Cloudflare Images** | 5,000 unique transformations/mo free | $0.50/1,000 unique transforms, $5/100K images stored/mo (→ **$5/mo minimum**), $1/100K delivered/mo | Only if an image pipeline is added |

---

## 5. 🔴 Options that break the "nothing leaves your device" promise

Each of these needs an explicit product decision, not a technical one.

| # | Option | What it costs | What it breaks |
|---|---|---|---|
| 5.1 | **Cloud AI background removal** (§4.1b) | $0.44–$36/mo at 2,000 uses | The photo is uploaded to a third party. Every tool page currently says "Files never leave your device" — that copy becomes false, in 11 languages, plus the privacy policy |
| 5.2 | **Put ads on the 13 tool pages** | $0 | Currently **0 of 13 tool pages carry an AdSense unit**, while 69 of 2,172 site pages do (homepage and pricing carry 2 each). The free tools are the top of the funnel and earn nothing. But the pages' whole pitch is "free, no signup, no watermarks" — in-page ads undercut the "free" promise on the page that says it loudest. AGENTS.md's rule bans *prices* on tool pages, not ads — so this is allowed but is a positioning decision |
| 5.3 | **Server-side share links** for the seating chart / invitation (§1.4) | R2+D1 = **$0** at this scale | Guest names leave the browser. The seating chart's FAQ explicitly says *"the tool never sends the guest list, names, or table assignments to any server"* — that claim would have to change |
| 5.4 | **Third-party CDN for the vendored libraries** | Bunny $0.01–0.03/GB (Asia $0.03/GB, 3× R2), $1/mo min | The 1.32 MB HEIC library would be served by a third party. It is not user data, but it breaks the "no third party" pattern and the `script-src 'self'` guarantee |
| 5.5 | **Cloud translation for i18n** | Workers AI `m2m100-1.2b` $0.342/M tokens | The site already has 11 human-reviewed dictionaries. Only worth it for the ~36k missing Russian blog keys |

---

## 6. 🔴 One thing that is not in the tools list but blocks them

The **`_middleware.js` catch-all** and the **i18n shard system** (step 9d of the
pre-deploy gate) both work — verified. But note:

- **New tool UI strings require a shard rebuild.** `scripts/verify-i18n-shards.py`
  is a **fatal** gate. For a handful of keys use
  `python scripts/add-shards-for-keys.py i18n/<lang>.json i18n/<lang>.manifest.json`
  (atomic, idempotent, byte-identical to a full rebuild), then run the verifier.
- **A stale shard set ships the OLD text with a 200 response** — the change
  looks like it did nothing. This is the single most likely way a tool
  improvement silently fails to appear.

---

## 7. Recommended order of work

**Tier 1 — $0, no CSP change, no licence question, fixes false claims**
1.1 real ZIP · 1.2 PDF export (or 1.3 drop the claim) · 1.4 seating-chart share
copy · 1.5 print CSS · 2.10 SW on tool pages

**Tier 2 — $0, one library each**
3.1 HEIC via `heic2any` (biggest real user loss) · 2.1–2.4 interactive
crop / text / collage placement via `cropperjs` + `fabric`/`konva`

**Tier 3 — $0, needs a CSP decision**
2.5–2.8 Worker + OffscreenCanvas + EXIF + memory · 3.2 real MP4 via
`mediabunny` · 3.3 `pica` (only if `'wasm-unsafe-eval'` is added)

**Tier 4 — $0 but product-shaped**
4.1a on-device MODNet AI segmentation (needs `'wasm-unsafe-eval'`) ·
2.14 target-size compression · 2.11 face-aware crop

**Tier 5 — only after a decision**
§5.1–5.5 (cloud AI, ads on tool pages, server-side share links, third-party
CDN, cloud translation)

---

## 8. Total cost view — what does each outcome actually cost

| Outcome | Monthly cost | Annual cost | What it buys |
|---|---|---|---|
| **Tier 1 + Tier 2** (fix the false claims + HEIC + interactive crop/text/collage) | **$0** | **$0** | The suite stops over-promising, HEIC works in every browser, and the three photo tools become usable instead of automatic |
| **+ Tier 3** (Worker, OffscreenCanvas, real MP4, `pica`) | **$0** (+ a CSP edit) | **$0** | Real video export, no UI freeze on large photos |
| **+ Tier 4** (on-device AI segmentation via MODNet) | **$0** (+ 6.6 MB model hosted on R2, whose egress is free) | **$0** | The one capability that cannot be faked locally |
| **+ cloud AI fallback** | **$0.44 – $36/mo** (cheapest shippable → best quality) | **$5 – $432/yr** | Only if on-device quality proves insufficient |
| **+ server-side share links** | **$0** (R2 10 GB + D1 5 GB free) | **$0** | Shareable links — at the cost of the "nothing leaves the device" claim |
| **+ ads on the 13 tool pages** | depends on AdSense RPM | — | The tools are currently **0/13** for ads while 69/2,172 site pages carry them |
| **+ Resend Pro** (removes the 100/day cap) | **$20/mo** | **$240/yr** | Lead-capture insurance |

**The honest headline: the entire recommended plan costs $0.** The only
decisions with a price tag are the ones that trade the privacy promise for a
capability, and for the one capability that matters (AI background removal)
there is a **$0, licence-safe, on-device path** — MODNet, Apache-2.0,
quantized to 6.6 MB.

**What is deliberately NOT in this plan:** anything that uploads a wedding
photo to a third party by default, any server-side rendering of a design, any
library whose UI would need 11 translations, and any paid plan whose only
benefit is removing a cap that has never been hit.

---

## 9. Open questions for the owner

1. **Does the site add `'wasm-unsafe-eval'` to the CSP?** It gates Tier 3 and
   Tier 4. It is a real (if small) widening of the security posture, and it
   must land in **both** `functions/_middleware.js` `buildCsp()` **and**
   `_headers`.
2. **Are the tool pages allowed to carry ads?** 0 of 13 do today. The tools
   are the free, high-intent entry point and currently earn nothing — but
   they are also the pages that say "free, no signup" loudest.
3. **Is "nothing leaves the device" a hard product promise, or a default that
   a paid HD mode may override?** Every cloud option in §5 hangs on this one
   answer.
4. **Is a real MP4 export worth the Firefox-Android gap?** `mediabunny` needs
   WebCodecs, which Firefox for Android does not have. Today the tool's
   "5 PNG frames" workaround is actually *more* universal.
   → **RESOLVED 2026-11-11, no trade-off needed.** The MP4 is offered
   ONLY where an H.264 encoder can actually produce one, and the native
   `VideoEncoder.isConfigSupported()` probe costs nothing. A browser
   without an encoder — Firefox for Android included — simply keeps the
   PNG sequence it has always had. **No browser loses a feature**, so the
   question does not have to be answered.
5. **Should the PDF claim be met or dropped?** Met = `jspdf` 410 KB.
   Dropped = $0 and a slightly weaker comparison table.
