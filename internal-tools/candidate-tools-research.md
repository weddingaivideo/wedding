# Candidate tools — technical decisions, measured 2026-11-10

Five tools the owner picked from the candidate list. For each: the chosen
solution, and the measured reason it beats the alternatives.

**How every claim below was checked.** Every candidate was downloaded with
`npm pack`, and the **shipped** files were read — not the npm `license`
field, not a search summary:

| check | method |
|---|---|
| licence | the LICENCE file **inside the tarball** |
| CSP | `eval(`, `new Function`, `WebAssembly`, `asm[` counted in the file that would actually be served |
| entry | the shipped bundle's format (UMD global / ESM / CommonJS-only) |
| UI debt | visible strings in the bundle (`Cancel`, `Confirm`, `Reset`, `aria-label`, `placeholder`, `Loading`) |

---

## 1. Wedding stationery set (invitation / place card / table card / poster / menu)

### Decision: NO new dependency — reuse the canvas renderer + `downloadPdfPages`

### Why not a text-based PDF engine (pdfmake, jsPDF text layer)

jsPDF's standard fonts carry only `WinAnsiEncoding`, `StandardEncoding`
and `MacRomanEncoding`. There is **no CJK** in the build: `UniGB-UCS2-H`,
`Big5`, `Shift-JIS`, `MS-Gothic` and `MS-Mincho` are all absent. Chinese
text needs `Identity-H` plus an embedded TTF.

This site serves **11 languages across 6 writing systems**:

| script | languages |
|---|---|
| Latin | en, es, fr, de, pt |
| CJK | zh, ja |
| Cyrillic | ru |
| Arabic (RTL + shaping) | ar |
| Thai | th |
| Devanagari | hi |

A text-based PDF engine would need **six embedded font files** (each
5–20 MB) or five languages would print wrong. The canvas path lets the
browser do the typesetting, so the glyphs are **pixels** — every script is
correct, at 300 DPI.

### The foundation is already here

`js/tools/common.js` → `downloadPdfPages(items, filename, opts)` already
does the hard part:

- renders one page at a time and **releases the bitmap** right after it
  goes into the PDF (a 40-page album at 2400×2400 would otherwise hold
  ~900 MB of canvas);
- calls `pdf.addPage([pw, ph], orientation)` — jsPDF's `addPage`,
  `insertPage` and `movePage` are all present in the vendored build, so
  **mixed page sizes work**;
- `unit: 'in'` makes a 2400 px canvas land at 300 DPI on an 8×8 inch page.

**One thing has to be extended.** `common.js:645-646`:

```js
var pw = opts.pageWidth || canvas.width;
var ph = opts.pageHeight || canvas.height;
```

`opts.pageWidth` / `opts.pageHeight` are **global to the document**. A PDF
that mixes A5 invitations, 90×55 mm place cards and an A3 poster cannot
give each page its own size. The fix is to let each item carry its own
`{width, height}` **in the PDF unit** while its canvas is still rendered
at 300 DPI. That is a change to one function, not a new engine.

`save-the-date-maker` already has a canvas engine (`renderTemplateGrid()`,
`drawCover()`); `wedding-invitation-maker` already renders a 375×525
canvas.

### What actually decides the quality (not the library)

1. **One set of design tokens** — colour, type, spacing shared across the
   five items. This is exactly what §2.15 just did for the seating chart:
   one `CHART` object feeding both the DOM and the canvas.
2. **Real finished sizes + bleed + crop marks** — invitation A5
   148×210 mm, place card 90×55 mm, table card (folding) 90×55 mm, poster
   A3, menu A5. At 300 DPI an A5 page is 1748×2480 px.
3. **One PDF, several sizes, print-shop ready** — crop marks, a 300 DPI
   note, CMYK guidance.

### A real font trap found on the way

`styles.css` declares

```css
--font-heading: 'Playfair Display', Georgia, serif;
--font-body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
```

but the repository contains **no `@font-face`, no font file and no Google
Fonts `<link>`**, and the CSP says `font-src 'self' data:` — Google Fonts
is not allowed either. **Neither font has ever loaded.** The whole site
renders in Georgia + the system sans, which is why every canvas tool
hard-codes `Georgia, serif`.

So the print output must use the fonts that actually render, or the screen
preview and the paper will differ. Self-hosting one OFL font (Playfair
Display woff2 ≈ 120 KB) would fix the site's headings *and* the print
output at once — but that is a site-wide fix, not this tool's business.

**New dependency: 0.**

---

## 2. PDF merge / split / reorder

### Decision: `@cantoo/pdf-lib` 2.11.1 (MIT) — not the original pdf-lib

| | `pdf-lib` 1.17.1 | `@cantoo/pdf-lib` 2.11.1 |
|---|---|---|
| licence (in the tarball) | MIT ✓ (`LICENSE.md`) | MIT ✓ (`LICENSE.md`) |
| `dist/pdf-lib.min.js` | 525 KB | 617 KB |
| CSP (`eval` / `new Function` / WASM) | 0 / 0 / 0 | 0 / 0 / 0 |
| `copyPages` / `embedPages` / `removePage` / `insertPage` | ✓ | ✓ |
| `setRotation` / `flatten` / `setTitle` | ✓ | ✓ |
| **decrypt an encrypted PDF** | ✗ | ✓ `decrypt` + AES |

### Why the fork and not the original

Not the size — the **encryption**. The original raises
`Input document to PDFDocument.load is encrypted. You can use
PDFDocument.load(..., { ignoreEncryption: true }) if you wish to load the
document anyways.` and then cannot read it. The fork can **open a
password-protected PDF with the password**. That is a real wedding case:
photographers and planners routinely send protected PDFs.

Both are pure JS, both are UMD (`dist/pdf-lib.min.js`), both are
CSP-clean, and the fork is actively maintained while the original is
archived.

### What it can do

merge (`copyPages` + `embedPages`), split out pages, reorder
(`removePage` + `insertPage`), rotate, crop, encrypt the output, set
metadata, flatten form fields.

### "Split" means two different things, and they need two libraries

- **into another PDF** (structural) → pdf-lib alone, no extra dependency;
- **into images** (pixels) → **pdfjs-dist 6.5.438 (Apache-2.0)**:
  `build/pdf.min.mjs` 474 KB + `build/pdf.worker.min.mjs` 1.27 MB. The
  worker loads from this origin, and `worker-src 'self'` is **already in
  the CSP** (§3.5 added it). The shipped build has 0 `eval`, 0
  `new Function`, 0 `WebAssembly`.

So the complete answer is **pdf-lib for structure + pdfjs-dist for
raster**.

**New dependency: 617 KB (+1.7 MB if it must also produce images).**

---

## 3. Photo contact sheet

### Decision: NO new dependency — canvas → PDF, reusing `downloadPdfPages`

The cheapest of the five: no format problem, no codec problem, no licence
question. It is N images drawn into one canvas.

What actually makes it good:

1. **Auto-crop that preserves the ratio** — `drawCover()` already exists
   in the album and in `save-the-date-maker`. No stretching.
2. **Both a file name and an index number** — this sheet exists so a
   photographer can circle picks, so the printed index must match the
   number in the file name ("12 / 84"). Lightroom's contact sheets work
   the same way.
3. **One A4 page at 300 DPI** — 2480×3508 px, `unit: 'in'`,
   `pageWidth: 8.27`, `pageHeight: 11.69`.
4. **Two layouts from the same engine** — 5×7 in prints (20 per A4) and
   a dense thumbnail grid (48 per A4). Same renderer, different layout
   parameters.

The only optional extra is **exifr** (print the capture date and camera
under each frame). exifr is already used by §2.13, and it can be loaded
on demand.

**New dependency: 0.**

---

## 4. GIF export

### Decision: `gifenc` 1.0.3 (MIT) — not gif.js, not the WASM build

| | `gifenc` | `gifenc.optimized` (WASM) | `gif.js` |
|---|---|---|---|
| size | **22 KB** (ESM) | ~200 KB + WASM | ~500 KB + Worker |
| licence | MIT ✓ | MIT ✓ | MIT/Apache |
| needs a Worker | no | no | **yes** |
| needs `'wasm-unsafe-eval'` | no | yes | no |
| own UI strings | none | none | none |

### Why plain JS wins here

The frame count is tiny (5) and the size is moderate (1080×1920). A WASM
accelerator saves little at that scale and costs ten times the bytes plus a
WASM runtime. `gifenc.optimized` stays available later — the API is
compatible — if hundreds of frames ever show up.

### The detail that decides whether the GIF looks right

A GIF holds 256 colours and the frames are *photo + text*. The palette must
be computed **per frame** (`quantize(frame, 256)` + `applyPalette`), not
once globally — a global palette locks every later frame to the first
frame's colours and the whole clip shifts. gifenc hands that decision to
you; `gif.js` does not.

The package ships exactly the primitives needed: `GIFEncoder`, `quantize`,
`applyPalette`, `nearestColorIndex`, `transparent`, `writeFrame`, `finish`.

**New dependency: 22 KB** (ESM — `<script type="module">` that hangs
`window.*`).

---

## 5. Video editing / format conversion

### Decision: `mediabunny` 1.65.2 — **already vendored** at
`/js/vendor/mediabunny/mediabunny.min.mjs` (723 KB, MPL-2.0)

The only one of the five whose best solution is already in the repository.

### Every alternative, and why it fails here

| option | why not |
|---|---|
| **ffmpeg.wasm** | the default build is **GPL-2.0**; and it needs `SharedArrayBuffer`, which needs `Cross-Origin-Opener-Policy: same-origin` + `Cross-Origin-Embedder-Policy: require-corp` on **every response** — that breaks the AdSense and Clarity iframes. Plus 30 MB. Not "hard" on this site — **impossible**. |
| **WebCodecs by hand** | WebCodecs encodes and decodes frames and packets, nothing else. There is **no demuxer and no muxer** — writing an MP4 muxer is months of work, not a tool. |
| **Whammy** | WebM output only; cannot read MP4; no transcoding. |
| **mp4box.js** | muxing only; no decoding. |
| **mediabunny** | one library covers demux → decode → edit → encode → mux. |

### What the shipped build actually exposes

Measured over the vendored `mediabunny.min.mjs` (145 exported names):

- `Input`, `Output`, `Conversion` — the whole pipeline;
- `EncodedVideoPacketSource`, `EncodedAudioPacketSource` — **concatenate
  without re-encoding** (keeps the quality, takes seconds);
- `CanvasSource`, `AudioBufferSource`, `SubtitleSource`,
  `TextSubtitleSource` — overlay text, music, subtitles;
- `VideoSampleSink`, `AudioSampleSink`, `CanvasSink` — extract frames,
  extract audio;
- `trim`, `Rotation`, `registerVideoSampleTransformer` — cut, rotate,
  change speed;
- **10 output formats**: `Mp4OutputFormat`, `WebMOutputFormat`,
  `MovOutputFormat`, `MkvOutputFormat`, `HlsOutputFormat`,
  `CmafOutputFormat`, `Mp3OutputFormat`, `WavOutputFormat`,
  `OggOutputFormat`, `FlacOutputFormat`;
- **12 input formats**: MP4, WebM, QuickTime, MPEG-TS, Matroska, MP3, WAV,
  OGG, FLAC, ADTS, HLS, ISOBMFF;
- `canDecode`, `canEncode`, `canDecodeVideo`, `canEncodeVideo` — **native
  capability probes**. §3.2 already uses exactly this to decide whether to
  show the MP4 button at all.

### The honest limits

- H.264 **encoding** inside MP4 is hardware-accelerated in Chrome, Edge
  and Safari; **Firefox cannot encode it**. The UI must probe
  `canEncodeVideo('avc')` before offering the button.
- **Firefox for Android has no WebCodecs** → that path falls back to the
  PNG frame sequence, exactly as the video invitation tool does today.
- 723 KB of ESM, loaded **on demand** (`js/tools/movie-loader.js` already
  does this) → nobody pays for it unless they ask.

**New dependency: 0.**

---

## Summary

| tool | solution | new bytes | the deciding reason |
|---|---|---|---|
| stationery set | canvas renderer + jsPDF (both in the repo) | **0** | a text-based PDF engine needs six embedded fonts for six writing systems; the canvas lets the browser typeset, so every script is right |
| PDF merge/split/reorder | `@cantoo/pdf-lib` | 617 KB | the only one that opens an encrypted PDF with its password; pure JS, CSP-clean |
| (…into images) | + `pdfjs-dist` | +1.7 MB | the worker is same-origin and `worker-src 'self'` is already allowed |
| contact sheet | canvas + jsPDF | **0** | no format, codec or licence problem; the work is layout and indexing |
| GIF export | `gifenc` | 22 KB | pure JS, no Worker, and the per-frame palette is under our control |
| video editing | `mediabunny` (in the repo) | **0** | the only option that survives COOP/COEP being impossible on this site |

### Three findings that are worth more than the tools

1. **The site's Playfair Display and Inter have never loaded.** No
   `@font-face`, no font file, no Google Fonts `<link>`, and
   `font-src 'self' data:` forbids Google Fonts. The site renders in
   Georgia + the system sans. One self-hosted OFL woff2 (≈120 KB) fixes
   the headings and the print output together.
2. **`downloadPdfPages` has one page size for the whole document**
   (`common.js:645`). It is already the site's best PDF pipeline; before
   any stationery tool ships it needs per-item page sizes.
3. **COOP/COEP is a dead end on this site.** ffmpeg.wasm needs
   SharedArrayBuffer, which needs those headers, which break the AdSense
   and Clarity iframes. Any future "use ffmpeg" proposal is not a
   difficulty, it is a no.
