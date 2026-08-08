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

Write-Host ""
Write-Host "=== WeddingAI.video Pre-Deploy Check ===" -ForegroundColor Cyan
Write-Host ""

# ---------- 1. HTML title tag integrity ----------
Write-Host "[1/9] HTML <title> tag integrity"
# Exclude the GSC verification template (legacy; production uses bca20c476d04af209950cbf5921e821d.txt)
# and the Service Worker offline fallback (intentionally no GA — no network to send beacons).
$htmlFiles = Get-ChildItem $root -Recurse -Filter "*.html" -File | Where-Object { $_.Name -ne "google-site-verification.html" -and $_.Name -ne "offline.html" }
$badTitles = 0
foreach ($f in $htmlFiles) {
    $c = Get-Content $f.FullName -Raw
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
    $c = Get-Content $f.FullName -Raw
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
    $c = Get-Content $f.FullName -Raw
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
    $c = Get-Content $f.FullName -Raw
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
    $c = Get-Content $f.FullName -Raw
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
        $c = Get-Content $h.FullName -Raw
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
    $_.FullName -notlike "*\tmp\*" -and $_.FullName -notlike "*\qa\*" -and $_.Name -ne "google-site-verification.html"
}
foreach ($h in $htmls) {
    $c = Get-Content $h.FullName -Raw
    # Relative path inside srcset= (e.g. srcset="logo-full-178.avif 178w")
    $relInSrcset = [regex]::Matches($c, 'srcset="(?![/h])[^"]*\.(avif|webp|jpg|jpeg|png)[^"]*"')
    foreach ($m in $relInSrcset) {
        # Allow attributes like href="..." or srcset that are inside style="" or data- attrs (rare)
        # We catch the first filename token to identify it
        $first = ([regex]::Match($m.Value, '[a-zA-Z][a-zA-Z0-9_-]*\.(?:avif|webp|jpg|jpeg|png)')).Value
        if ($first -and $c -notmatch [regex]::Escape("data-srcset=")) {
            Fail "$($h.Name): relative path in srcset: $first"
            $hygieneIssues++
        }
    }
    # Doubled /images/X-/images/ (a Python Path-on-Windows bug we hit before)
    $doubled = [regex]::Matches($c, '/images/[a-z]+-/images/')
    foreach ($m in $doubled) {
        Fail "$($h.Name): doubled /images/ path: $($m.Value)"
        $hygieneIssues++
    }
    # Nested <picture><source>...<picture> (flatten-avatar-wrapper leftover)
    $nestedPic = [regex]::Matches($c, '<picture[^>]*>[^<]{0,200}<picture')
    foreach ($m in $nestedPic) {
        Fail "$($h.Name): nested <picture> detected: $($m.Value.Substring(0, [Math]::Min(80, $m.Value.Length)))"
        $hygieneIssues++
    }
}
if ($hygieneIssues -eq 0) { Pass "All srcset/picture tags use absolute paths and proper structure" }

# ---------- 3. CSS empty rules ----------
Write-Host "[3/9] CSS empty rules and missing braces"
$cssPath = "$root\styles.css"
$css = Get-Content $cssPath -Raw
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
    $c = Get-Content $f.FullName -Raw
    # Privacy Policy / Terms of Service should NOT be href="#"
    if ($c -match '<a href="#">Privacy Policy</a>') {
        Fail "$($f.Name): Privacy Policy still href=#"
    }
    if ($c -match '<a href="#">Terms of Service</a>') {
        Fail "$($f.Name): Terms of Service still href=#"
    }
}
Pass "No dead Privacy/Terms links"

# ---------- 6. GA4 ID ----------
Write-Host "[6/9] Google Analytics 4 ID"
$gaCount = 0
$legacySyncGtag = 0  # pages still using <script async src="googletagmanager..."> synchronously
foreach ($f in $htmlFiles) {
    $c = Get-Content $f.FullName -Raw
    if ($c -match 'G-4FE7KSJDNB') {
        $gaCount++
    }
    if ($c -match '<script async src="https://www\.googletagmanager\.com/gtag/js\?id=') {
        $legacySyncGtag++
    }
}
if ($gaCount -eq $htmlFiles.Count) {
    Pass "GA4 ID present in all $gaCount pages (using production ID G-4FE7KSJDNB)"
} else {
    Warn "GA4 ID found in $gaCount / $($htmlFiles.Count) pages"
}
if ($legacySyncGtag -gt 0) {
    Fail "$legacySyncGtag page(s) still loading gtag.js synchronously — re-run internal-tools/inject-lazy-gtag.ps1 to defer it"
} else {
    Pass "All pages use the lazy-load gtag pattern (no synchronous <script async src=\"googletagmanager\"> tags)"
}
# Note: G-4FE7KSJDNB is the confirmed production GA4 ID (per stakeholder, 2026-07-20).
# To swap to a different ID later: powershell -ExecutionPolicy Bypass -File scripts/standardize-ga4.ps1 -NewId 'G-XXXXXXXXXX'

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
$htmlCount = (Get-ChildItem $root -Recurse -Filter "*.html" -File).Count
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

# ---------- Cloudflare Pages Functions ----------
$fnPath = "$root\functions"
if (Test-Path $fnPath) {
    $fnCount = (Get-ChildItem $fnPath -Recurse -Filter "*.js" -File).Count
    if ($fnCount -gt 0) {
        Pass "Cloudflare Functions: $fnCount endpoint(s) in /functions"

        # 检查 order 表单 form action (目录版本 2026-07-28 起)
        $orderForm = Get-Content "$root\order\index.html" -Raw
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
    Where-Object { $_.FullName -notlike "*\i18n\*" -and $_.FullName -notlike "*\qa\*" -and $_.FullName -notlike "*\tmp\*" -and $_.FullName -notlike "*\admin\*" }
foreach ($f in $htmlFiles) {
    $raw = Get-Content $f.FullName -Raw
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
