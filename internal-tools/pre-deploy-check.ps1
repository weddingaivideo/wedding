# WeddingAI.video — Pre-Deploy Check
# Run this BEFORE deploying to catch common bugs.
# Exits with non-zero if any check fails.
#
# Path resolution: $root is the repo root. We default to the parent of this
# script's directory so the same script works both on the dev box
# (C:\Users\qiaoshan\...\weddingai\internal-tools\pre-deploy-check.ps1)
# and on CI runners (D:\a\wedding\wedding\internal-tools\...).
# Override with $env:WEDDINGAI_ROOT if you need a different layout.

if ($env:WEDDINGAI_ROOT) {
    $root = $env:WEDDINGAI_ROOT
} else {
    $root = Split-Path -Parent $PSScriptRoot
}
$errors = 0
$warnings = 0

function Fail($msg) {
    Write-Host "  [FAIL] $msg" -ForegroundColor Red
    $script:errors++
}
function Warn($msg) {
    Write-Host "  [WARN] $msg" -ForegroundColor Yellow
    $script:warnings++
}
function Pass($msg) {
    Write-Host "  [PASS] $msg" -ForegroundColor Green
}
# Safe wrapper for Get-Content -Raw that returns "" for missing/empty files
# instead of $null (which causes .NET regex to throw "Value cannot be null").
# Added after pre-existing 0-byte files (e.g. es/blog/wedding-video-trends-
# 2026/index.html, broken in commit fcf2c80) caused the CSP nonces check
# to abort. local-only — internal-tools/ is in .assetsignore, not deployed.
function Get-RawSafe($path) {
    if (-not (Test-Path $path)) { return "" }
    $content = Get-Content $path -Raw -ErrorAction SilentlyContinue
    if ($null -eq $content) { return "" }
    return $content
}

Write-Host ""
Write-Host "=== WeddingAI.video Pre-Deploy Check ===" -ForegroundColor Cyan
Write-Host ""

# ---------- 1. HTML title tag integrity ----------
Write-Host "[1/9] HTML <title> tag integrity"
# Exclude the GSC verification template (legacy; production uses bca20c476d04af209950cbf5921e821d.txt)
# and the Service Worker offline fallback (intentionally no GA — no network to send beacons).
#
# Also exclude every directory that is NEVER deployed to the edge.
# TRAP: a `*\tmp\*` pattern does NOT match `\.tmp\` — the dot-prefixed
# scratch dir holds 1400+ captured HTML files (post-middleware dumps). Left
# unfiltered, those produced 300+ FALSE failures here — hard-coded nonces,
# FAQ mismatches, stale GA4 loaders — and blocked the deploy gate for
# changes that were perfectly fine.
$scratchDirs = @('*\tmp\*', '*\.tmp\*', '*\private\*', '*\qa\*', '*\internal-docs\*',
                 '*\node_modules\*', '*\.wrangler\*', '*\.git\*', '*\__pycache__\*')
function Test-DeployedPath([string]$p) {
    foreach ($pat in $scratchDirs) { if ($p -like $pat) { return $false } }
    return $true
}
$htmlFiles = Get-ChildItem $root -Recurse -Filter "*.html" -File | Where-Object {
    $_.Name -ne "google-site-verification.html" -and $_.Name -ne "offline.html" -and
    (Test-DeployedPath $_.FullName)
}
$badTitles = 0
foreach ($f in $htmlFiles) {
    $c = Get-RawSafe $f.FullName
    if ($c -match '<title>[\s\S]*?<meta\s+property="og:image"[\s\S]*?</title>') {
        Fail "$($f.Name): og:image nested inside <title>"
        $badTitles++
    }
    if ($c -match 'property="og:image"\s+property="og:image"') {
        Fail "$($f.Name): duplicate property= attribute on og:image"
    }
}
if ($badTitles -eq 0) { Pass "All $($htmlFiles.Count) HTML files have clean <title> tags" }

# ---------- 1b. Hard-coded CSP nonces in HTML ----------
# Catch the bug where someone saves post-middleware rendered HTML back to
# source files (e.g. `curl https://site.com/ > index.html`). The middleware
# only does `text.split("__CSP_NONCE__").join(perRequestNonce)`, so any
# hard-coded nonce value (20+ base64 chars that isn't __CSP_NONCE__) will
# survive untouched. The CSP response header still gets a fresh per-request
# nonce → HTML nonce ≠ CSP nonce → 'strict-dynamic' blocks every script
# (i18n.js, main.min.js, dropdowns, all silently dead).
#
# Lesson from 2026-07-29: home page dropdown broke because index.html had
# 11 hard-coded nonces ("7SzVyMUvldAItYr5uAaSKw=="). Other pages worked
# because they used the __CSP_NONCE__ placeholder.
Write-Host "[1b/9] Hard-coded CSP nonces in HTML"
# Use the same htmlFiles list as #1, but also exclude paths that are never
# deployed (tmp/ scratch, i18n/ translation files, etc.).
$deployedHtml = $htmlFiles | Where-Object {
    $_.FullName -notlike "*\tmp\*" -and
    $_.FullName -notlike "*\i18n\*" -and
    $_.FullName -notlike "*\qa\*" -and
    $_.FullName -notlike "*\admin\*" -and
    $_.FullName -notlike "*\scripts\*" -and
    $_.FullName -notlike "*\node_modules\*" -and
    $_.FullName -notlike "*\.wrangler\*" -and
    $_.FullName -notlike "*\functions\*"
}
$noncePattern = '<script\b[^>]*\snonce="([^"]{20,})"'
$badNonces = 0
foreach ($f in $deployedHtml) {
    $c = Get-RawSafe $f.FullName
    $hits = [regex]::Matches($c, $noncePattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    foreach ($h in $hits) {
        $val = $h.Groups[1].Value
        # __CSP_NONCE__ is the placeholder — only flag REAL nonces
        if ($val -eq '__CSP_NONCE__') { continue }
        $relPath = $f.FullName.Substring($root.Length + 1)
        Fail "$relPath : hard-coded CSP nonce '$val' (should be __CSP_NONCE__ placeholder)"
        $badNonces++
    }
}
if ($badNonces -eq 0) { Pass "All $($deployedHtml.Count) deployed HTML files use __CSP_NONCE__ placeholder" }

# ---------- 1c. h1 / first-body-h2 duplicate (Semrush audit) ----------
# The page <h1> in the page-hero should be the only top-level heading for the
# title. If the article body re-renders the same title as <h2> at the top
# (e.g. a leading `# Title` in the blog markdown that the generator emits
# without dedup), the page has two visible top-level headings pointing at
# the same text — confusing for screen readers and an audit-flag in Semrush
# / Ahrefs. Check covers all deployed pages, not just /blog/*.
#
# Lesson: 15 second-batch blog posts shipped with this dup (2026-08-04). The
# `scripts/generate-blog.py` _drop_dup_body_heading safeguard plus this
# check is the two-layer defense.
$dupH1H2 = 0
$tagStrip = { param($s) $s -replace '<[^>]+>', '' -replace '\s+', ' ' }
foreach ($f in $deployedHtml) {
    $c = Get-RawSafe $f.FullName
    $h1 = [regex]::Match($c, '<h1[^>]*>(.*?)</h1>', 'IgnoreCase, Singleline')
    if (-not $h1.Success) { continue }
    $h1Text = (& $tagStrip $h1.Groups[1].Value).Trim()
    if (-not $h1Text) { continue }
    # Find the first <h2> in the document. Footer doesn't use h2 (only h3+)
    # so this is always a body h2.
    $h2 = [regex]::Match($c, '<h2[^>]*>(.*?)</h2>', 'IgnoreCase, Singleline')
    if (-not $h2.Success) { continue }
    $h2Text = (& $tagStrip $h2.Groups[1].Value).Trim()
    if ($h2Text -and ($h2Text.ToLower() -eq $h1Text.ToLower())) {
        $relPath = $f.FullName.Substring($root.Length + 1)
        Fail "$relPath : <h1> '$h1Text' duplicated as first body <h2>"
        $dupH1H2++
    }
}
if ($dupH1H2 -eq 0) { Pass "No <h1>/first-<h2> duplicates in $($deployedHtml.Count) deployed pages" }

# ---------- 1d. <hN>...</hM> opening/closing tag mismatch (i18n regex breakage) ----------
# The Cloudflare Pages middleware runs a server-side i18n regex that replaces
# data-i18n-bearing elements' text content. The regex requires the opening
# and closing hN tags to match (uses back-reference \1). When they don't, the
# regex SKIPS the element — leaving English text on non-EN pages — and the
# next matching element (whose inner content gets eaten up to the next valid
# </hN>) replaces large swaths of HTML, breaking the related-cards "Pair It
# With..." grid layout in particular.
#
# This was the root cause of the 2026-08-04 "non-EN related-cards layout is
# broken" incident. The bug source was `<h3>...</h4>` (8 files) and
# `<h2>...</h3>` (8 files) in 8 service pages — a 9th (family-tribute) used
# the correct `<h4>...</h4>` and was fine.
#
# Catch: any element opening with `<hN` (with or without data-i18n) and
# closing with `</hM>` where N != M. We deliberately skip the h2 false
# positives inside testimonial quote strings (where the inner text contains
# literal "<h3" without being a tag) by requiring the captured opening tag
# to have at least one attribute after the tag name.
Write-Host "[1d/9] <hN>...</hM> open/close tag mismatch (i18n regex breakage)"
$hTagMismatches = 0
# Match: <h<1-6><attrs>...></h<1-6>> with N != M, where the opening tag has
# at least one attribute (excludes bare inner-text "<h3" inside an h2 testimonial).
$hTagRe = '<h([1-6])\s+[^>]*>\s*([^<]|<(?!/h\1>))*?</h([1-6])>'
foreach ($f in $deployedHtml) {
    $c = Get-RawSafe $f.FullName
    $matches = [regex]::Matches($c, $hTagRe, 'IgnoreCase, Singleline')
    foreach ($m in $matches) {
        $openTag = $m.Groups[1].Value
        $closeTag = $m.Groups[3].Value
        if ($openTag -ne $closeTag) {
            $relPath = $f.FullName.Substring($root.Length + 1)
            $line = ($c.Substring(0, $m.Index) -split "`n").Count
            $inner = $m.Groups[2].Value -replace '\s+', ' ' | Select-Object -First 60
            Fail "$relPath :$line <h$openTag>...<${closeTag}> tag mismatch (inner: '$inner') — i18n regex will skip and EN text will leak through"
            $hTagMismatches++
        }
    }
}
if ($hTagMismatches -eq 0) { Pass "All hN open/close tag pairs match in $($deployedHtml.Count) deployed pages" }

# ---------- 1d. Inline event handlers (CSP nonce-only enforcement) ----------
# The active CSP on HTML pages is nonce-only (delivered via
# <meta http-equiv="Content-Security-Policy"> from middleware).
# Any <element on*="..."> attribute — onclick, onload, onerror, onmouseover,
# onfocus, onblur, onchange, onsubmit, oninput, onkey* — gets BLOCKED by
# the browser because there's no nonce. The old
# `<link media="print" onload="this.media='all'">` async-stylesheet trick
# is no longer allowed; the same for any vendor snippet that injects an
# onclick. Anything that needs to react to a user event MUST use
# addEventListener in /js/main.js (or a dedicated module) — never inline.
#
# This check is the regression guard: catches the new <button onclick=...>
# that someone added "to make the demo work" before remembering the CSP
# just got tightened.
#
# Regex requires a quote char RIGHT AFTER the `=` to distinguish HTML
# attributes (value is a quoted string) from JS property assignment
# (e.g. `s.onload = function() {` — no quote, not a CSP concern).
$inlineHandlers = 0
foreach ($f in $deployedHtml) {
    $c = Get-RawSafe $f.FullName
    # (?<!data-) skips Angular-style data-onclick (not a real event handler).
    # [="'] requires the value to start with a quote — rules out
    # `s.onload = function() {...}` JS patterns inside <script> blocks.
    $hits = [regex]::Matches(
        $c,
        '(?<!data-)on(?:click|dblclick|mousedown|mouseup|mousemove|mouseover|mouseout|focus|blur|change|input|submit|reset|select|keydown|keyup|keypress|load|error|unload|resize|scroll|touchstart|touchend|touchmove|pointerdown|pointerup|pointermove|wheel|animationend|transitionend)\s*=[''"]',
        'IgnoreCase'
    )
    foreach ($h in $hits) {
        $relPath = $f.FullName.Substring($root.Length + 1)
        Fail "$relPath : inline event handler '$($h.Value.Trim())' (CSP blocks un-nonced inline JS — use addEventListener in /js/)"
        $inlineHandlers++
    }
}
if ($inlineHandlers -eq 0) { Pass "No inline event handlers in $($deployedHtml.Count) deployed pages" }

# ---------- 2. Service page image paths ----------
Write-Host "[2/9] Service page image paths"
$serviceDirs = @("video-enhancement","absence-compensation","personalization")
$badImgs = 0
foreach ($d in $serviceDirs) {
    $htmls = Get-ChildItem "$root\services\$d" -Filter "*.html" -File
    foreach ($h in $htmls) {
        $c = Get-RawSafe $h.FullName
        $imgs = [regex]::Matches($c, '<img[^>]+src="([^"]+)"')
        foreach ($m in $imgs) {
            $src = $m.Groups[1].Value
            # Exclude ../../-relative and http(s):// URLs. Web-absolute paths
            # starting with `/` (e.g. /images/logo-full.jpeg) are resolved
            # against the repo root, NOT the file's directory — otherwise
            # `Join-Path services /images/foo` produces
            # `services/images/foo` which doesn't exist (false positive).
            # Conversely, simply skipping `/` paths hides real broken
            # images (e.g. /images/foo-360.jpg that was never uploaded),
            # so we DO want to check them — just against the right base.
            if ($src -notmatch '^\.\./\.\./|^https?:') {
                if ($src -match '^/') {
                    $fullPath = Join-Path $root $src.TrimStart('/')
                } else {
                    $fullPath = Join-Path $h.DirectoryName $src
                }
                if (-not (Test-Path $fullPath)) {
                    Fail "$($h.Name): broken image $src"
                    $badImgs++
                }
            }
        }
    }
}
if ($badImgs -eq 0) { Pass "All service page images resolve" }

# ---------- 2.5. srcset / picture hygiene (catches flatten-avatar-wrapper bugs) ----------
Write-Host "[2.5/9] srcset / picture hygiene"
$hygieneIssues = 0
$htmls = Get-ChildItem "$root" -Recurse -Filter "*.html" | Where-Object {
    (Test-DeployedPath $_.FullName) -and
    $_.FullName -notlike "*\tmp\*" -and
    $_.FullName -notlike "*\private\*" -and
    $_.FullName -notlike "*\i18n\*" -and
    $_.FullName -notlike "*\qa\*" -and
    $_.FullName -notlike "*\admin\*" -and
    $_.FullName -notlike "*\scripts\*" -and
    $_.FullName -notlike "*\node_modules\*" -and
    $_.FullName -notlike "*\.wrangler\*" -and
    $_.FullName -notlike "*\functions\*" -and
    $_.Name -ne "google-site-verification.html"
}
foreach ($h in $htmls) {
    $relPath = $h.FullName.Substring($root.Length + 1)
    $c = Get-RawSafe $h.FullName
    # Relative path inside srcset= (e.g. srcset="logo-full-178.avif 178w")
    $relInSrcset = [regex]::Matches($c, 'srcset="(?![/h])[^"]*\.(avif|webp|jpg|jpeg|png)[^"]*"')
    foreach ($m in $relInSrcset) {
        # Allow attributes like href="..." or srcset that are inside style="" or data- attrs (rare)
        # We catch the first filename token to identify it
        $first = ([regex]::Match($m.Value, '[a-zA-Z][a-zA-Z0-9_-]*\.(?:avif|webp|jpg|jpeg|png)')).Value
        if ($first -and $c -notmatch [regex]::Escape("data-srcset=")) {
            Fail "$relPath : relative path in srcset: $first"
            $hygieneIssues++
        }
    }
    # Doubled /images/X-/images/ (a Python Path-on-Windows bug we hit before)
    $doubled = [regex]::Matches($c, '/images/[a-z]+-/images/')
    foreach ($m in $doubled) {
        Fail "$relPath : doubled /images/ path: $($m.Value)"
        $hygieneIssues++
    }
    # Nested <picture><source>...<picture> (flatten-avatar-wrapper leftover)
    $nestedPic = [regex]::Matches($c, '<picture[^>]*>[^<]{0,200}<picture')
    foreach ($m in $nestedPic) {
        Fail "$relPath : nested <picture> detected: $($m.Value.Substring(0, [Math]::Min(80, $m.Value.Length)))"
        $hygieneIssues++
    }
}
if ($hygieneIssues -eq 0) { Pass "All srcset/picture tags use absolute paths and proper structure" }

# ---------- 3. CSS empty rules ----------
Write-Host "[3/9] CSS empty rules and missing braces"
$cssPath = "$root\styles.css"
$css = Get-RawSafe $cssPath
# Look for selector followed by newline and another selector (missing { ... } block)
$emptyRules = [regex]::Matches($css, '\}\s*\n[ \t]*([\.\#\:\>\w\+\~\*\s,]+)[ \t]*\n[ \t]*([\.\#\:\>\w\+\~\*\s,]+)[ \t]*\n[ \t]*\{')
$suspicious = 0
foreach ($m in $emptyRules) {
    $sel1 = $m.Groups[3].Value.Trim()
    $sel2 = $m.Groups[4].Value.Trim()
    # Filter out false positives from multi-line values like linear-gradient(...)
    if ($sel1 -match 'to bottom|rgba' -or $sel2 -match 'to bottom|rgba') { continue }
    Fail "styles.css: possible empty rule '$sel1' -> '$sel2'"
    $suspicious++
}
if ($suspicious -eq 0) { Pass "No empty CSS rules detected" }

# Check .btn-primary has actual styles
if ($css -match '\.btn-primary\s*\{\s*background:\s*var\(--color-primary\)') {
    Pass ".btn-primary has background rule"
} else {
    Fail ".btn-primary may be missing styles (background rule not found)"
}

# Check @media print closes properly
$printStart = $css.IndexOf('@media print {')
if ($printStart -gt 0) {
    # Find next major section after @media print
    $afterPrint = $css.Substring($printStart)
    $nextSection = $afterPrint.IndexOf('/* ----------', 50)
    if ($nextSection -gt 0) {
        $block = $afterPrint.Substring(0, $nextSection)
        $openBraces = ($block.ToCharArray() | Where-Object { $_ -eq '{' }).Count
        $closeBraces = ($block.ToCharArray() | Where-Object { $_ -eq '}' }).Count
        if ($openBraces -ne $closeBraces) {
            Fail "@media print: brace mismatch ($openBraces open vs $closeBraces close)"
        } else {
            Pass "@media print brace count balanced"
        }
    }
}

# ---------- 4. Critical files present ----------
# Top-level *.html files were removed 2026-07-28 to fix SEO duplicate content
# (see _redirects for back-compat 308 redirects). The directory versions
# (<page>/index.html) are now the single source of truth.
Write-Host "[4/9] Critical files present"
$critical = @(
    "index.html",
    "about/index.html",
    "gallery/index.html",
    "order/index.html",
    "success/index.html",
    "privacy/index.html",
    "terms/index.html",
    "styles.css",
    "js/main.js"
)
foreach ($f in $critical) {
    $p = "$root\$f"
    if (Test-Path $p) {
        Pass "$f exists"
    } else {
        Fail "$f MISSING"
    }
}

# ---------- 5. No remaining <a href="#"> dead links in critical places ----------
Write-Host "[5/9] Critical dead links check"
foreach ($f in $htmlFiles) {
    $c = Get-RawSafe $f.FullName
    # Privacy Policy / Terms of Service should NOT be href="#"
    if ($c -match '<a href="#">Privacy Policy</a>') {
        Fail "$($f.Name): Privacy Policy still href=#"
    }
    if ($c -match '<a href="#">Terms of Service</a>') {
        Fail "$($f.Name): Terms of Service still href=#"
    }
}
Pass "No dead Privacy/Terms links"

# ---------- 6. Retired analytics stay removed ----------
# GA4 (property G-4FE7KSJDNB) was deactivated and Baidu Tongji was dropped
# (the site no longer targets the domestic China market) on 2026-10-28.
# This check is a hard FAIL so a later edit cannot silently re-introduce
# either loader. The old check was the mirror image — it FAILED when the
# GA4 ID was missing from pages.
Write-Host "[6/9] Retired analytics removed (GA4 + Baidu Tongji)"
$ga4Hits = 0
$baiduHits = 0
$ga4Page = ""
$baiduPage = ""
foreach ($f in $htmlFiles) {
    $c = Get-RawSafe $f.FullName
    if ($c -match 'googletagmanager\.com/gtag/js|G-4FE7KSJDNB|__loadGtag') {
        $ga4Hits++
        if (-not $ga4Page) { $ga4Page = $f.FullName }
    }
    if ($c -match 'hm\.baidu\.com/hm\.js|_hmt\s*=') {
        $baiduHits++
        if (-not $baiduPage) { $baiduPage = $f.FullName }
    }
}
if ($ga4Hits -eq 0) {
    Pass "No GA4 loader in any of the $($htmlFiles.Count) pages"
} else {
    Fail "$ga4Hits page(s) still contain the GA4 loader (first: $ga4Page)"
}
if ($baiduHits -eq 0) {
    Pass "No Baidu Tongji loader in any of the $($htmlFiles.Count) pages"
} else {
    Fail "$baiduHits page(s) still contain the Baidu Tongji loader (first: $baiduPage)"
}

# The CSP must not whitelist the retired origins either — a stale
# script-src entry leaves the door open for a re-injected loader.
$cspStale = 0
foreach ($cf in @("$root\_headers", "$root\functions\_middleware.js")) {
    $cc = Get-RawSafe $cf
    foreach ($pat in @('googletagmanager\.com', 'google-analytics\.com', 'analytics\.google\.com', 'hm\.baidu\.com')) {
        if ($cc -match $pat) {
            Fail "CSP still whitelists '$pat' in $cf"
            $cspStale++
        }
    }
}
if ($cspStale -eq 0) {
    Pass "CSP whitelists no retired analytics origin"
}

# The vendors that ARE still allowed must stay allowed — dropping these
# would silently kill ad revenue / heatmaps rather than fail a deploy.
$clarityHits = 0
$adsenseHits = 0
foreach ($f in $htmlFiles) {
    $c = Get-RawSafe $f.FullName
    if ($c -match 'clarity\.ms/tag/') { $clarityHits++ }
    if ($c -match 'pagead2\.googlesyndication\.com') { $adsenseHits++ }
}
if ($clarityHits -gt 0) {
    Pass "Microsoft Clarity present on $clarityHits page(s)"
} else {
    Warn "Microsoft Clarity not found on any page — heatmaps / session replay would be dead"
}
if ($adsenseHits -gt 0) {
    Pass "Google AdSense present on $adsenseHits page(s)"
} else {
    Fail "Google AdSense not found on any page — ad revenue would be dead"
}

# ---------- 7. (REMOVED) Netlify config ----------
# Project migrated from Netlify to Cloudflare Pages (2026-07-27). netlify.toml
# and wrangler.toml are both dead configs — the current deployment is a pure
# GitHub → CF Pages git-deploy (push to main triggers auto-build from the
# GitHub integration). KV bindings / cron triggers / secrets are configured
# in the Cloudflare dashboard, not in any toml file in the repo.
# The legacy [[redirects]] + [[headers]] blocks lived in netlify.toml only;
# current production uses _redirects + _headers (see Step 1 above).
# Keeping a no-op marker here so the rest of the numbering stays stable.

# ---------- 8. Page count ----------
Write-Host "[8/9] Page and asset counts"
$htmlCount = $htmlFiles.Count
$imgCount = (Get-ChildItem "$root\images" -File).Count
Write-Host "  HTML pages: $htmlCount (was 19, +privacy +terms = 21 expected)"
Write-Host "  Images: $imgCount"
if ($htmlCount -ge 19) { Pass "$htmlCount HTML files present" } else { Fail "Only $htmlCount HTML files (expected 19+)" }

# ---------- 9. SEO lengths (title ≤ 60, description ≤ 160) ----------
Write-Host "[9/9] SEO title/description lengths"
$seoScript = "$root\scripts\check-seo-lengths.py"
if (Test-Path $seoScript) {
    $py = $null
    foreach ($candidate in @("python", "python3", "py")) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) { $py = $candidate; break }
    }
    if ($py) {
        $seoOutput = & $py $seoScript 2>&1
        $seoExit = $LASTEXITCODE
        # 只输出最后几行（避免淹没 pre-deploy-check 自身输出）
        $tail = $seoOutput | Select-Object -Last 22
        foreach ($line in $tail) { Write-Host "  $line" }
        if ($seoExit -eq 0) {
            Pass "All page titles ≤ 60 chars and descriptions ≤ 160 chars"
        } else {
            Fail "Some page titles or descriptions exceed Google SEO limits. See output above. Run 'python scripts/check-seo-lengths.py' for full details."
        }
    } else {
        Warn "Python not found in PATH; skipping SEO length check. Install Python or run 'python scripts/check-seo-lengths.py' manually."
    }
} else {
    Warn "scripts\check-seo-lengths.py not found; skipping SEO length check"
}

# ---------- 9a. JSON-LD schema consistency (FAQPage vs visible FAQ) ----------
# Catches the silent drift between visible <details class="faq-item"> blocks
# and the FAQPage JSON-LD mainEntity. They MUST match in count: when they
# diverge, Google either surfaces stale rich results or never indexes the
# extra visible questions, both of which hurt SEO. The script also catches
# JSON parse errors in any schema block (would have failed silently in prod
# before this check existed).
#
# On mismatch: run `python scripts/sync-faq-schema.py --apply` to auto-fix.
# This step is FATAL — the deploy aborts until the schema is consistent.
Write-Host "[9a/9] JSON-LD schema consistency"
$schemaScript = "$root\scripts\verify-schemas.py"
if (Test-Path $schemaScript) {
    $py = $null
    foreach ($candidate in @("python", "python3", "py")) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) { $py = $candidate; break }
    }
    if ($py) {
        # --quiet trims the per-block @type listing; we only need the
        # summary lines (files / parse failures / FAQ mismatches).
        $schemaOutput = & $py $schemaScript --quiet 2>&1
        $schemaExit = $LASTEXITCODE
        # Show the 4 lines the operator needs to diagnose.
        $key = $schemaOutput | Select-String -Pattern 'HTML files with JSON-LD|Total JSON-LD|JSON parse failures|FAQ consistency|^\s+- ' | Select-Object -First 10
        foreach ($line in $key) { Write-Host "  $($line -replace '^\s*','')" }
        if ($schemaExit -eq 0) {
            Pass "All JSON-LD blocks parse and FAQ counts match visible FAQ"
        } else {
            Fail "JSON-LD schema is inconsistent. See lines above. Run 'python scripts/sync-faq-schema.py --apply' to auto-align FAQPage, then re-run this check."
        }
    } else {
        Warn "Python not found in PATH; skipping JSON-LD schema check. Install Python or run 'python scripts/verify-schemas.py --quiet' manually."
    }
} else {
    Warn "scripts\verify-schemas.py not found; skipping JSON-LD schema check"
}

# ---------- 9b. Live i18n title/description lengths ----------
# The check in step 9 measures the STATIC html. For the 525 pages whose
# title carries data-i18n and whose description carries
# data-i18n-attr="content:…", the value a visitor receives comes from
# i18n/<lang>.json — the static file only holds the English source. That
# layer was completely invisible to this gate until now.
#
# REPORT-ONLY on purpose: the backlog is a translation/rewriting job per
# language, not a deploy blocker. Switch this step to Fail once a language
# has been cleaned up (the script also accepts --strict).
Write-Host "[9b/9] Live i18n title/description lengths"
$i18nMetaScript = "$root\scripts\check-i18n-meta-lengths.py"
if (Test-Path $i18nMetaScript) {
    $py = $null
    foreach ($candidate in @("python", "python3", "py")) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) { $py = $candidate; break }
    }
    if ($py) {
        $i18nMetaOutput = & $py $i18nMetaScript 2>&1
        $i18nMetaExit = $LASTEXITCODE
        $key = $i18nMetaOutput | Select-String -Pattern 'bound title keys|live values over|^\S+\s+\d+\s+\d+$' | Select-Object -First 16
        foreach ($line in $key) { Write-Host "  $($line -replace '^\s*','')" }
        # Decide on the COUNTS, not on the exit code: the script is report-only
        # by default, so a non-zero exit never happens here.
        # NB: MatchInfo.Matches.Count is the number of MATCHES (1), not the
        # number of capture groups - test the groups themselves.
        $overCount = 0
        $overLine = $i18nMetaOutput | Select-String -Pattern 'live values over the limit:\s*(\d+)\s+titles,\s*(\d+)\s+descriptions' | Select-Object -First 1
        if ($overLine -and $overLine.Matches[0].Groups[1].Success -and $overLine.Matches[0].Groups[2].Success) {
            $overCount = [int]$overLine.Matches[0].Groups[1].Value + [int]$overLine.Matches[0].Groups[2].Value
        }
        if ($i18nMetaExit -eq 0 -and $overCount -eq 0) {
            Pass "All live i18n title/description values within limits"
        } else {
            Warn "Live i18n metadata over the limit ($overCount values). These are the values the middleware serves to non-English visitors - see scripts/check-i18n-meta-lengths.py. Report-only by design."
        }
    } else {
        Warn "Python not found in PATH; skipping live i18n metadata check."
    }
} else {
    Warn "scripts\check-i18n-meta-lengths.py not found; skipping live i18n metadata check"
}

# ---------- 9c. Lead mail routing + delivery truth ----------
# Background (2026-10-29): two weeks of leads were lost because the domain had
# no MX record for 17 days, and because /api/quote.js recorded a 2xx from the
# mail API as "delivered" — a 2xx only means "accepted"; a suppressed or
# later-bounced address answers 2xx as well.
#
# Check 1: the domain must have MX records at all (the 2026-10-12 failure).
# Check 2: the code must not write "delivered" straight from a 2xx, the cron
#          must read the provider's delivery event back, and the admin
#          endpoint must know the "sent" state.
$leadDomain = "weddingai.video"
$mxSeen = @()
try {
    # Inline DoH query (the Get-DohJson helper is defined further down, in the
    # production-domain section, so it is not in scope here).
    $mxResp = Invoke-WebRequest -Uri "https://dns.google/resolve?name=$leadDomain&type=MX" -Headers @{ accept = "application/dns-json" } -UseBasicParsing -TimeoutSec 25
    $mxText = if ($mxResp.Content -is [byte[]]) { [System.Text.Encoding]::UTF8.GetString($mxResp.Content) } else { [string]$mxResp.Content }
    $mxJson = $mxText | ConvertFrom-Json
    $mxSeen = @($mxJson.Answer | Where-Object { $_.type -eq 15 } | ForEach-Object { $_.data })
} catch {
    Write-Host "  MX lookup for $leadDomain failed: $($_.Exception.Message -replace '\s+',' ')" -ForegroundColor DarkGray
}
if ($mxSeen.Count -eq 0) {
    Fail "$leadDomain has NO MX record - no mail can be delivered and every lead notification bounces. Add MX records in Cloudflare (DNS -> Records)."
} else {
    Pass "$leadDomain MX records: $($mxSeen -join ', ')"
    if (-not ($mxSeen -join ' ') -match 'mxbiz[12]\.qq\.com') {
        Warn "$leadDomain MX points somewhere other than the Tencent 企业邮 hosts (mxbiz1/mxbiz2.qq.com). Fine if the mail provider changed deliberately - just make sure the mailbox really exists there."
    }
}

$quotePath = "$root\functions\api\quote.js"
$schedPath = "$root\functions\scheduled.js"
$dlqPath = "$root\functions\api\dead-letters.js"
if ((Test-Path $quotePath) -and (Test-Path $schedPath) -and (Test-Path $dlqPath)) {
    $quoteSrc = Get-RawSafe $quotePath
    $schedSrc = Get-RawSafe $schedPath
    $dlqSrc = Get-RawSafe $dlqPath
    $falseGreen = @()
    if ($quoteSrc -match 'updateLeadStatus\([^)]*,\s*"delivered"') { $falseGreen += "quote.js writes email_status=delivered directly from the send request" }
    if ($schedSrc -match 'getDeliveryEvent' -and $schedSrc -match 'getSuppressedAddresses') {
        # the read-back and the suppression guard are both present
    } else {
        $falseGreen += "scheduled.js does not read the provider's delivery event back (getDeliveryEvent) and/or does not check the suppression list (getSuppressedAddresses)"
    }
    if ($dlqSrc -notmatch '"sent"') { $falseGreen += "dead-letters.js does not know the 'sent' state" }
    if ($falseGreen.Count -eq 0) {
        Pass "Lead delivery states are honest: 2xx -> 'sent', provider event -> 'delivered'/'failed'"
    } else {
        foreach ($g in $falseGreen) { Fail "Lead delivery can still be recorded as delivered without proof - $g" }
    }
} else {
    Warn "Lead-mail state files not found; skipping the delivery-truth check"
}

# ---------- Cloudflare Pages Functions ----------
$fnPath = "$root\functions"
if (Test-Path $fnPath) {
    $fnCount = (Get-ChildItem $fnPath -Recurse -Filter "*.js" -File).Count
    if ($fnCount -gt 0) {
        Pass "Cloudflare Functions: $fnCount endpoint(s) in /functions"

        # 检查 order 表单 form action (目录版本 2026-07-28 起)
        $orderForm = Get-RawSafe "$root\order\index.html"
        if ($orderForm -match 'action="/api/quote"') {
            Pass "order form posts to /api/quote"
        } else {
            Fail "order.html form does not POST to /api/quote (Cloudflare Functions endpoint)"
        }

        # 检查是否还残留 Netlify 专属属性
        if ($orderForm -match 'data-netlify|netlify-honeypot') {
            Fail "order form still has Netlify-specific form attributes (data-netlify / netlify-honeypot)"
        } else {
            Pass "No Netlify-specific form attributes in order form"
        }

        # ---- Hardcoded-secret scanner (all .js under functions/) ----
        # Patterns matched:
        #   - Resend API key:  re_[A-Za-z0-9]{20,}
        #   - OpenAI / Anthropic / etc.:  sk-[A-Za-z0-9]{20,}
        #   - AWS access key:  AKIA[0-9A-Z]{16}
        #   - GitHub PAT:      ghp_[A-Za-z0-9]{36}
        #   - Google API key:  AIza[A-Za-z0-9]{35}
        #   - Slack token:     xox[baprs]-[A-Za-z0-9-]+
        # Plus a generic "secret-looking long string assigned to a constant" heuristic
        # for services we don't have a specific pattern for.
        $secretPatterns = @(
            're_[A-Za-z0-9_]{20,}',
            'sk-[A-Za-z0-9]{20,}',
            'AKIA[0-9A-Z]{16}',
            'ghp_[A-Za-z0-9]{36}',
            'AIza[A-Za-z0-9_-]{35}',
            'xox[baprs]-[A-Za-z0-9-]{10,}',
            # Generic: a string literal > 30 chars assigned to a name with "key|token|secret|password" in it
            '(?:KEY|TOKEN|SECRET|PASSWORD)\s*=\s*["'']([A-Za-z0-9_\-\/+=]{30,})["'']'
        )
        $combined = ($secretPatterns -join '|')
        $secretsFound = 0
        Get-ChildItem $fnPath -Recurse -Filter "*.js" -File | ForEach-Object {
            # Use [System.IO.File]::ReadAllText instead of Get-Content. PowerShell 5.1
            # mis-parses filenames with literal '[' / ']' (e.g. functions/docs/[id].js)
            # as wildcard patterns under -LiteralPath, throwing ObjectNotFound.
            # ReadAllText is a direct .NET call that does no wildcard interpretation.
            # (Bug caught 2026-07-28: secret scanner was silently skipping
            # functions/docs/[id].js because the underlying read failed.)
            $code = [System.IO.File]::ReadAllText($_.FullName)
            $hits = [regex]::Matches($code, $combined, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
            foreach ($h in $hits) {
                $relPath = $_.FullName.Substring($root.Length + 1)
                Fail "$relPath :$($h.Index) hardcoded secret-looking string: '$($h.Value.Substring(0, [Math]::Min(20, $h.Value.Length)))...' (rotate any leaked keys at the provider's dashboard)"
                $secretsFound++
            }
        }
        if ($secretsFound -eq 0) {
            Pass "No hardcoded API keys/tokens detected in functions/"
        } else {
            Write-Host ""
            Write-Host "  Run a regex like 'rg -nP \"${combined}\" functions/' to find them." -ForegroundColor DarkGray
        }
    } else {
        Warn "functions/ directory exists but contains no .js files"
    }
} else {
    Warn "functions/ directory not found — form submission will not work on Cloudflare Pages"
}

# ---------- Relative paths in <script src> (B1.i18n.js bug lesson) ----------
# Relative paths in <script src="..."> break on /xx/<subdir>/ i18n redirect
# (e.g. /zh/gallery/ resolves js/i18n.js to /zh/gallery/js/i18n.js = 404).
# All <script src> must be absolute. Link hrefs for assets (favicon, manifest)
# are allowed relative since they're not part of the i18n critical path.
$relativeScriptIssues = 0
$htmlFiles = Get-ChildItem -Recurse -Filter "*.html" -File |
    Where-Object { (Test-DeployedPath $_.FullName) -and $_.FullName -notlike "*\i18n\*" -and $_.FullName -notlike "*\qa\*" -and $_.FullName -notlike "*\tmp\*" -and $_.FullName -notlike "*\admin\*" }
foreach ($f in $htmlFiles) {
    $raw = Get-RawSafe $f.FullName
    # Match <script src="X..."> where X doesn't start with http(s)://, /, or #
    $matches = [regex]::Matches($raw, '<script[^>]+src="(?!https?://|/|#)([^"]+)"')
    foreach ($m in $matches) {
        $rel = $m.Groups[1].Value
        $relativeScriptIssues++
        if ($relativeScriptIssues -le 5) {
            Write-Host "  RELATIVE SCRIPT: $($f.Name) -> $rel" -ForegroundColor DarkGray
        }
    }
}
if ($relativeScriptIssues -gt 0) {
    Fail "$relativeScriptIssues relative <script src> found. On /xx/ subdirectory pages these 404. Use leading / to make absolute."
} else {
    Pass "All <script src> are absolute (or external)"
}

# ---------- Blog slug 301 retention check ----------
# 50 back-compat rules in _redirects for the 2026-07-23 blog slug migration.
# Safe to delete 2027-01-23. < 30 days to expiry escalates to WARN.
Write-Host "[10/10] Blog slug 301 retention"
$blogCheckScript = "$root\qa\check_blog_redirects.py"
if (Test-Path $blogCheckScript) {
    $py = $null
    foreach ($candidate in @("python", "python3", "py")) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) { $py = $candidate; break }
    }
    if ($py) {
        $blogOutput = & $py $blogCheckScript 2>&1
        $blogExit = $LASTEXITCODE
        # Show the key lines (skip the rule table to keep output scannable)
        $blogKey = $blogOutput | Select-String -Pattern "Days until safe-delete|Safe-delete|FAIL|>>>" | Select-Object -First 6
        foreach ($line in $blogKey) { Write-Host "  $($line -replace '^\s*','')" }
        if ($blogExit -eq 0) { Pass "Blog 301 retention check OK" }
        else { Fail "Blog 301 safe-delete date passed. Delete the 50 rules from _redirects." }
    } else {
        Warn "Python not found in PATH; skipping blog 301 retention check"
    }
} else {
    Warn "qa\check_blog_redirects.py not found; skipping blog 301 retention check"
}

# ---------- Production domain reachability (DNS over HTTPS + HTTPS) ----------
# Added 2026-10-28: the Cloudflare DNS records for the custom domain were
# removed from the zone, which took the whole site (722 pages, 11 languages)
# offline for the public while every other check in this script stayed green.
#
# The dev box runs Clash Verge (Mihomo) in TUN + fake-ip mode, so a normal
# resolver can still hand back a cached answer for a domain that no longer
# exists. Every lookup below therefore goes over DoH, and the HTTPS probe
# resolves through DoH as well (curl --doh-url), so no local cache can mask
# an outage. Cloudflare keeps serving the Pages custom domain at the edge
# even with the DNS record gone, which is exactly why "the browser still
# works" is not evidence that the site is up.
Write-Host "[11/11] Production domain DNS + HTTPS"
$prodDomain = "weddingai.video"
$pagesTarget = "weddingai-video.pages.dev"
$dohResolvers = @(
    @{ Name = "dns.google";     Url = "https://dns.google/resolve?name=$prodDomain&type=A" },
    @{ Name = "cloudflare-dns"; Url = "https://cloudflare-dns.com/dns-query?name=$prodDomain&type=A" }
)
$dnsOk = @()
$dnsMissing = @()
$dnsUnreachable = @()
# PowerShell 5.1 returns .Content as byte[] for non-text content types
# (application/dns-json), so decode it before parsing.
function Get-DohJson($uri) {
    $resp = Invoke-WebRequest -Uri $uri -Headers @{ accept = "application/dns-json" } -UseBasicParsing -TimeoutSec 25
    if ($resp.Content -is [byte[]]) {
        $text = [System.Text.Encoding]::UTF8.GetString($resp.Content)
    } else {
        $text = [string]$resp.Content
    }
    return ($text | ConvertFrom-Json)
}
foreach ($resolver in $dohResolvers) {
    try {
        $dohJson = Get-DohJson $resolver.Url
        $aRecords = @($dohJson.Answer | Where-Object { $_.type -eq 1 })
        if ($aRecords.Count -gt 0) {
            $ips = ($aRecords | ForEach-Object { $_.data }) -join ", "
            $dnsOk += "$($resolver.Name): A -> $ips"
        } elseif ($dohJson.Status -eq 3) {
            $dnsMissing += "$($resolver.Name): NXDOMAIN"
        } else {
            $dnsMissing += "$($resolver.Name): NODATA (no A record)"
        }
    } catch {
        $reason = $_.Exception.Message -replace '\s+', ' '
        $dnsUnreachable += "$($resolver.Name): unreachable ($reason)"
    }
}
foreach ($line in ($dnsOk + $dnsMissing + $dnsUnreachable)) { Write-Host "  $line" -ForegroundColor DarkGray }

# ---------- HTTPS probe (runs before the verdict so the verdict can cite it) ----------
# Two resolution paths, several attempts each way: the system resolver and the
# DoH resolver. Either one alone can lie - the system resolver may serve a
# stale cache, and on this dev box the direct-to-Cloudflare-IP path is dropped
# by the local TUN proxy (measured: 2/8 successes for weddingai.video and
# 6/8 for cloudflare.com, so it is the path that fails, not the site).
# A single failed attempt must therefore never fail the gate; the authoritative
# DNS verdict above is what decides a real outage.
$curlExe = Get-Command curl.exe -ErrorAction SilentlyContinue
$httpsCode = ""
$httpsSeen = @()
if ($curlExe) {
    $probes = @(
        @{ Label = "system resolver"; Extra = @("-4") },
        @{ Label = "DoH";             Extra = @("-4", "--doh-url", "https://dns.google/dns-query") },
        @{ Label = "system resolver"; Extra = @("-4") },
        @{ Label = "DoH";             Extra = @("-4", "--doh-url", "https://dns.google/dns-query") }
    )
    foreach ($p in $probes) {
        $code = & curl.exe -s -o NUL -L -w "%{http_code}" --max-time 25 @($p.Extra) "https://$prodDomain/" 2>&1
        $exit = $LASTEXITCODE
        $httpsSeen += "$($p.Label)=$code(exit $exit)"
        if ("$code" -eq "200") { $httpsCode = "200"; break }
    }
} else {
    try {
        $httpsCode = (Invoke-WebRequest -Uri "https://$prodDomain/" -UseBasicParsing -TimeoutSec 30).StatusCode
        $httpsSeen += "Invoke-WebRequest=$httpsCode"
    } catch {
        $httpsSeen += "Invoke-WebRequest failed: $($_.Exception.Message -replace '\s+', ' ')"
    }
}
Write-Host ("  HTTPS attempts: " + ($httpsSeen -join ", ")) -ForegroundColor DarkGray

if ($dnsOk.Count -gt 0 -and $dnsMissing.Count -gt 0) {
    # A single resolver can answer oddly for some zones (Cloudflare's own
    # resolver does this for Cloudflare-owned domains). Do not hard-fail on a
    # disagreement alone.
    Warn "DoH resolvers disagree about $prodDomain. Some still resolve it while others report it missing - visitors with a cold cache may not reach the site."
} elseif ($dnsOk.Count -gt 0) {
    Pass "$prodDomain resolves via DoH"
} elseif ($dnsMissing.Count -gt 0) {
    # Authoritative truth: the domain has no address record, so visitors with
    # a cold cache cannot reach it - even if this machine still can.
    Fail "$prodDomain has NO A record at the authoritative nameservers (every DoH resolver agrees). The custom-domain DNS record was deleted - re-add it in Cloudflare (DNS -> Records: CNAME @ -> $pagesTarget, proxy ON). The site is unreachable for visitors."
} else {
    Fail "Could not verify $prodDomain via DoH (all resolvers unreachable). The domain health cannot be proven - fix the network or the DoH endpoint before deploying."
}

if ($httpsCode -eq "200") {
    Pass "https://$prodDomain/ returns 200"
} else {
    Fail "https://$prodDomain/ did not return 200 ($($httpsSeen -join '; '))."
}

# (the HTTPS probe now runs above, together with the DNS verdict)

# www is informational only: every canonical URL in the repo uses the apex,
# and www may legitimately never exist.
try {
    $wwwJson = Get-DohJson "https://dns.google/resolve?name=www.$prodDomain&type=A"
    $wwwA = @($wwwJson.Answer | Where-Object { $_.type -eq 1 })
    if ($wwwA.Count -gt 0) {
        Write-Host "  www.$prodDomain -> A record present" -ForegroundColor DarkGray
    } elseif ($wwwJson.Status -eq 3) {
        Write-Host "  www.$prodDomain -> NXDOMAIN (no www record; canonical URLs use the apex, so this is fine)" -ForegroundColor DarkGray
    } else {
        Write-Host "  www.$prodDomain -> no A record" -ForegroundColor DarkGray
    }
} catch {
    Write-Host "  www.$prodDomain -> lookup unavailable" -ForegroundColor DarkGray
}

# ---------- Summary ----------
Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "  Errors:   $errors" -ForegroundColor $(if ($errors -gt 0) { "Red" } else { "Green" })
Write-Host "  Warnings: $warnings" -ForegroundColor $(if ($warnings -gt 0) { "Yellow" } else { "Green" })
Write-Host ""
if ($errors -gt 0) {
    Write-Host "FAILED — fix errors above before deploying." -ForegroundColor Red
    exit 1
} else {
    Write-Host "READY TO DEPLOY" -ForegroundColor Green
    exit 0
}
