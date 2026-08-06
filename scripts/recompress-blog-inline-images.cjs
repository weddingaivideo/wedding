// Recompress: convert blog inline JPGs to AVIF + WebP
// Per memory: AVIF q=42 chromaSubsampling 4:2:0, WebP q=75, preserve source dimensions
// Windows EBUSY fix: copyFileSync + unlinkSync instead of rename
// Skip files where target already exists and is newer than source (idempotent)
const sharp = require("C:/Users/qiaoshan/AppData/Roaming/npm/node_modules/wrangler/node_modules/sharp");
const { readdirSync, statSync, copyFileSync, unlinkSync, existsSync } = require("node:fs");
const { join, basename } = require("node:path");

const ROOT = "C:/Users/qiaoshan/.openclaw/workspace/weddingai/images/blog/inline";
const files = readdirSync(ROOT).filter(f => f.toLowerCase().endsWith(".jpg"));
console.log(`Found ${files.length} JPGs to process`);

let avifBytes = 0, webpBytes = 0, jpgBytes = 0;
let avifSaved = 0, webpSaved = 0;
let skipped = 0, errors = 0;
const start = Date.now();

// Process in batches to avoid sharp memory pressure
const BATCH = 8;
async function processOne(src) {
  const name = basename(src, ".jpg");
  const outAvif = join(ROOT, `${name}.avif`);
  const outWebp = join(ROOT, `${name}.webp`);
  const srcStat = statSync(src);
  jpgBytes += srcStat.size;

  // Idempotency: skip if both outputs exist and are newer than source
  if (existsSync(outAvif) && existsSync(outWebp) &&
      statSync(outAvif).mtimeMs >= srcStat.mtimeMs &&
      statSync(outWebp).mtimeMs >= srcStat.mtimeMs) {
    skipped++;
    avifBytes += statSync(outAvif).size;
    webpBytes += statSync(outWebp).size;
    return;
  }

  try {
    // AVIF
    const avifTmp = outAvif + ".tmp";
    await sharp(src)
      .avif({ quality: 42, effort: 4, chromaSubsampling: "4:2:0" })
      .toFile(avifTmp);
    copyFileSync(avifTmp, outAvif);
    unlinkSync(avifTmp);
    const avifSize = statSync(outAvif).size;
    avifBytes += avifSize;
    avifSaved += srcStat.size - avifSize;

    // WebP
    const webpTmp = outWebp + ".tmp";
    await sharp(src)
      .webp({ quality: 75, effort: 4 })
      .toFile(webpTmp);
    copyFileSync(webpTmp, outWebp);
    unlinkSync(webpTmp);
    const webpSize = statSync(outWebp).size;
    webpBytes += webpSize;
    webpSaved += srcStat.size - webpSize;
  } catch (e) {
    errors++;
    console.error(`  ERROR on ${name}: ${e.message}`);
  }
}

(async () => {
  for (let i = 0; i < files.length; i += BATCH) {
    const slice = files.slice(i, i + BATCH);
    await Promise.all(slice.map(f => processOne(join(ROOT, f))));
    const done = Math.min(i + BATCH, files.length);
    if (done % 40 === 0 || done === files.length) {
      const elapsed = (Date.now() - start) / 1000;
      const rate = done / elapsed;
      console.log(`  ${done}/${files.length}  (${elapsed.toFixed(1)}s, ${rate.toFixed(1)} files/s)`);
    }
  }
  console.log("---");
  console.log(`Source JPG total: ${(jpgBytes/1024/1024).toFixed(1)} MB`);
  console.log(`AVIF total:       ${(avifBytes/1024/1024).toFixed(1)} MB  (saved ${(avifSaved/1024/1024).toFixed(1)} MB, ${(100*avifSaved/jpgBytes).toFixed(0)}%)`);
  console.log(`WebP total:       ${(webpBytes/1024/1024).toFixed(1)} MB  (saved ${(webpSaved/1024/1024).toFixed(1)} MB, ${(100*webpSaved/jpgBytes).toFixed(0)}%)`);
  console.log(`Skipped (already up-to-date): ${skipped}, errors: ${errors}`);
})();
