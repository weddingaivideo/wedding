// Wrap each <img src="/images/blog/inline/X.jpg" ...> with <picture><source AVIF><source WebP><img JPG></picture>
// - Preserves all original img attributes
// - Indents picture block to match original img indentation
// - Preserves CRLF line endings
// - Idempotent: skips if already wrapped
// - Targets HTML files in blog subtrees (en + 8 langs)
const { readdirSync, readFileSync, writeFileSync, statSync } = require("node:fs");
const { join, relative } = require("node:path");

const ROOT = "C:/Users/qiaoshan/.openclaw/workspace/weddingai";
const SKIP = new Set(["tmp", "qa", "admin", ".wrangler", "node_modules", ".git", "scripts"]);

function walk(d, out) {
  for (const e of readdirSync(d, { withFileTypes: true })) {
    if (SKIP.has(e.name)) continue;
    const p = join(d, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (e.name === "index.html") out.push(p);
  }
}

// Match an <img> that:
//   - Has src under /images/blog/inline/
//   - Ends with .jpg
//   - Is NOT already inside a <picture> (cheap guard: check for "picture" on a previous line)
// Capture leading whitespace and the full opening tag
const IMG_RE = /(^([ \t]*))<img\s+src="(\/images\/blog\/inline\/([^"]+)\.jpg)"([^>]*?)\/?>/gm;

const files = [];
walk(ROOT, files);

let totalFiles = 0, totalImgs = 0, totalSkipped = 0, totalErrors = 0;

for (const file of files) {
  const original = readFileSync(file, "utf8");
  if (!IMG_RE.test(original)) continue;
  IMG_RE.lastIndex = 0; // reset after .test()

  // Quick guard: skip if any <picture> already wraps blog inline img in this file
  // (idempotency). Cheap check: look for "blog/inline/" string followed within ~200 chars by </picture>
  if (/\/images\/blog\/inline\/[^"]+\.jpg[\s\S]{0,400}?<\/picture>/.test(original)) {
    totalSkipped++;
    continue;
  }

  let fileImgs = 0;
  const updated = original.replace(IMG_RE, (match, leadingWS, indent, srcPath, baseName, restAttrs) => {
    fileImgs++;
    // Build the picture block, keeping same indent for the wrapping <picture>
    // and adding 4 more spaces for the inner content (matches project's <picture> style)
    const innerIndent = indent + "    ";
    return `${leadingWS}<picture>\r\n${innerIndent}<source srcset="${srcPath.replace(/\.jpg$/, ".avif")}" type="image/avif">\r\n${innerIndent}<source srcset="${srcPath.replace(/\.jpg$/, ".webp")}" type="image/webp">\r\n${innerIndent}<img src="${srcPath}"${restAttrs.replace(/\s+$/, "")} />\r\n${indent}</picture>`;
  });

  if (fileImgs > 0 && updated !== original) {
    try {
      writeFileSync(file, updated, "utf8");
      totalFiles++;
      totalImgs += fileImgs;
    } catch (e) {
      totalErrors++;
      console.error(`  ERROR writing ${relative(ROOT, file)}: ${e.message}`);
    }
  }
}

console.log(`Files modified: ${totalFiles}`);
console.log(`Total <img> wrapped: ${totalImgs}`);
console.log(`Files skipped (already wrapped): ${totalSkipped}`);
console.log(`Errors: ${totalErrors}`);
