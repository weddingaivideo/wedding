# scripts/submit-indexnow.ps1
# 通过 IndexNow API 通知 Bing / Yandex / Seznam / Naver 站点地图已更新。
# IndexNow 替代了已停用的 bing.com/ping 端点。
#
# IndexNow API 文档: https://www.indexnow.org/
# 端点:             POST https://api.indexnow.org/IndexNow
#
# 一次性设置:
#   1. 随机生成一个 key (32+ hex 字符) — 此脚本首次运行会自动生成
#   2. 在站点根目录创建 <key>.txt 文件, 内容就是 key 本身
#   3. 部署后调用此脚本即可批量提交 URL
#
# 用法:
#   powershell -ExecutionPolicy Bypass -File scripts\submit-indexnow.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\submit-indexnow.ps1 -SitemapPath "C:\path\sitemap.xml"
#   powershell -ExecutionPolicy Bypass -File scripts\submit-indexnow.ps1 -DryRun           # 只跑 preflight + live check, 不 POST
#   powershell -ExecutionPolicy Bypass -File scripts\submit-indexnow.ps1 -SkipLiveCheck   # 跳过 live GET (例如本地测试)

param(
    [string]$SitemapPath = "",
    [string]$SiteHost = "weddingai.video",
    [string]$SitemapUrl = "",
    [switch]$DryRun = $false,
    [switch]$SkipLiveCheck = $false
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

# ---------- 颜色辅助 ----------
function Write-PreflightPass { param($msg) Write-Host "  [PASS] $msg" -ForegroundColor Green }
function Write-PreflightWarn { param($msg) Write-Host "  [WARN] $msg" -ForegroundColor Yellow }
function Write-PreflightFail { param($msg) Write-Host "  [FAIL] $msg" -ForegroundColor Red }
function Write-PreflightInfo { param($msg) Write-Host "  [INFO] $msg" -ForegroundColor Gray }

# ---------- 1. 准备 key ----------
$indexNowKeyFile = Join-Path $root "indexnow-key.txt"
$keyTxtFileName = ""
$apiKey = ""

if (Test-Path $indexNowKeyFile) {
    $apiKey = (Get-Content $indexNowKeyFile -Raw).Trim()
    # .Trim() 也会干掉末尾 \r\n, 但如果文件以 BOM 开头 (PS 5.1 Get-Content 不会自动去 BOM) — 这里额外清理一次
    if ($apiKey.Length -gt 0 -and $apiKey[0] -eq [char]0xFEFF) {
        $apiKey = $apiKey.Substring(1)
    }
    $keyTxtFileName = "$apiKey.txt"
    $keyTxtOnDisk = Join-Path $root $keyTxtFileName
    if (-not (Test-Path $keyTxtOnDisk)) {
        # 写 key 文件用 [System.IO.File], 强制 UTF-8 无 BOM, 末尾不换行
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($keyTxtOnDisk, $apiKey, $utf8NoBom)
        Write-Host "  + Created verification file: $keyTxtFileName" -ForegroundColor Gray
    }
} else {
    # Generate a 32-char hex key
    $bytes = New-Object byte[] 16
    (New-Object Random).NextBytes($bytes)
    $apiKey = -join ($bytes | ForEach-Object { $_.ToString("x2") })
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($indexNowKeyFile, $apiKey, $utf8NoBom)
    $keyTxtFileName = "$apiKey.txt"
    [System.IO.File]::WriteAllText((Join-Path $root $keyTxtFileName), $apiKey, $utf8NoBom)
    Write-Host "  + Generated new IndexNow key: $apiKey" -ForegroundColor Green
    Write-Host "  + Created indexnow-key.txt (private, contains the key)" -ForegroundColor Gray
    Write-Host "  + Created $keyTxtFileName (public, must be deployed so IndexNow can verify)" -ForegroundColor Gray
    Write-Host "  ! Don't forget to git add BOTH files and push — this script does not commit for you" -ForegroundColor Yellow
}

$keyLocation = "https://$SiteHost/$keyTxtFileName"

# ---------- 1.5. Preflight — 6 项检查, 任一 FAIL 立即退出 ----------
Write-Host ""
Write-Host "=== Preflight checks (6) ===" -ForegroundColor Cyan
$preflightFailures = 0

# (1) <key>.txt 文件内容 == key (字节级)
$expectedBytes = [System.Text.Encoding]::UTF8.GetBytes($apiKey)
$actualBytes   = [System.IO.File]::ReadAllBytes($keyTxtOnDisk)
if ($expectedBytes.Length -eq $actualBytes.Length -and -not ($expectedBytes | Where-Object { $actualBytes -notcontains $_ })) {
    # 上面的 -notcontains 在 byte 数组上不可靠, 改用 SequenceEqual
    $seqEqual = $true
    for ($i = 0; $i -lt $expectedBytes.Length; $i++) {
        if ($expectedBytes[$i] -ne $actualBytes[$i]) { $seqEqual = $false; break }
    }
    if ($seqEqual) {
        Write-PreflightPass "(1) $keyTxtFileName content matches key ($($expectedBytes.Length) bytes, UTF-8 no BOM)"
    } else {
        Write-PreflightFail "(1) $keyTxtFileName content MISMATCH — expected [$apiKey] but file has different bytes"
        $preflightFailures++
    }
} else {
    Write-PreflightFail "(1) $keyTxtFileName size mismatch — expected $($expectedBytes.Length) bytes, got $($actualBytes.Length)"
    $preflightFailures++
}

# (2) <key>.txt 已在 git tracked (否则 CF Pages 不会部署)
# PowerShell 的 NativeCommandError 在 $ErrorActionPreference='Stop' 下会抛, 用 try/catch 包一层
$gitTracked = $false
try {
    $null = & git ls-files --error-unmatch $keyTxtFileName 2>&1
    if ($LASTEXITCODE -eq 0) { $gitTracked = $true }
} catch {
    $gitTracked = $false
}
if ($gitTracked) {
    Write-PreflightPass "(2) $keyTxtFileName is tracked in git"
} else {
    Write-PreflightFail "(2) $keyTxtFileName is NOT tracked in git — CF Pages will not deploy it"
    Write-PreflightInfo "    Fix: git add $keyTxtFileName && git commit && git push"
    $preflightFailures++
}

# (3) <key>.txt 没被 .assetsignore 排除 (CF Pages 4.114+ 会读 .assetsignore 删文件)
$assetsignorePath = Join-Path $root ".assetsignore"
$assetsBlocked = $false
if (Test-Path $assetsignorePath) {
    $ai = Get-Content $assetsignorePath -Raw
    $patterns = $ai -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -and -not $_.StartsWith("#") }
    foreach ($p in $patterns) {
        # 简单 glob 转 regex (只处理 *, 不处理 ?/[]): 还原字面量后 \Q...\E 跳过 regex
        if ($p -eq $keyTxtFileName) { $assetsBlocked = $true; break }
        if ($p.Contains("*")) {
            $regex = [regex]::Escape($p).Replace("\*", ".*").Replace("\?", ".")
            if ($keyTxtFileName -match "^$regex$") { $assetsBlocked = $true; break }
        }
    }
}
if ($assetsBlocked) {
    Write-PreflightFail "(3) $keyTxtFileName is excluded by .assetsignore — CF Pages will not deploy it"
    $preflightFailures++
} else {
    Write-PreflightPass "(3) $keyTxtFileName is NOT in .assetsignore (will deploy)"
}

# (4) _redirects 没把 /<key>.txt 拦到 404 (否则线上 404, IndexNow 验证失败)
$redirectsPath = Join-Path $root "_redirects"
$redirectsBlocked = $false
if (Test-Path $redirectsPath) {
    $rd = Get-Content $redirectsPath -Raw
    # _redirects 格式: 每行 "/pattern  /target  [code]"
    # 简单匹配: 找以 "/<key>.txt" 开头 (允许前导空格) 的行, 然后看 code 是不是 4xx
    $lines = $rd -split "`n"
    foreach ($line in $lines) {
        $trimmed = $line.Trim()
        if ($trimmed.StartsWith("#") -or -not $trimmed) { continue }
        $parts = $trimmed -split '\s+' | Where-Object { $_ }
        if ($parts.Count -lt 2) { continue }
        $from = $parts[0]
        # _redirects 支持通配符, 但我们的 <key>.txt 是字面量, 直接比较
        if ($from -eq "/$keyTxtFileName" -or $from -eq "/$keyTxtFileName/") {
            $code = if ($parts.Count -ge 3) { $parts[2] } else { "301" }
            if ($code -match '^4') {
                $redirectsBlocked = $true
                Write-PreflightFail "(4) _redirects blocks /$keyTxtFileName with code $code (line: $trimmed)"
            } else {
                Write-PreflightInfo "    _redirects has /$keyTxtFileName → $($parts[1]) $code (not 4xx, allowed)"
            }
            break
        }
    }
}
if (-not $redirectsBlocked) {
    Write-PreflightPass "(4) _redirects does NOT block /$keyTxtFileName"
}

# (5) _headers 包含 /<key>.txt 路径 (cache-control 显式禁用缓存, 推荐)
# PowerShell -match 默认单行模式, ^/$ 只匹配整个字符串首行, 必须用 (?m) 多行模式
$headersPath = Join-Path $root "_headers"
$headersConfigured = $false
if (Test-Path $headersPath) {
    $hd = Get-Content $headersPath -Raw
    if ($hd -match "(?m)^/$([regex]::Escape($keyTxtFileName))\s*$") {
        $headersConfigured = $true
        Write-PreflightPass "(5) _headers configures /$keyTxtFileName (Cache-Control: no-store)"
    } else {
        Write-PreflightWarn "(5) _headers does NOT configure /$keyTxtFileName — add Cache-Control: no-store, must-revalidate"
        # 这是 warn 不是 fail, 因为 CF Pages 默认就不会缓存 text/plain
    }
}
if (-not $headersConfigured -and -not (Test-Path $headersPath)) {
    Write-PreflightWarn "(5) _headers not found — OK if not needed, but consider adding Cache-Control: no-store for the key file"
}

# (6) indexnow-key.txt 自身被 .assetsignore 排除 (key 不应该被公开)
$privateKeyExcluded = $false
if (Test-Path $assetsignorePath) {
    $ai = Get-Content $assetsignorePath -Raw
    $patterns = $ai -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -and -not $_.StartsWith("#") }
    foreach ($p in $patterns) {
        if ($p -eq "indexnow-key.txt") { $privateKeyExcluded = $true; break }
    }
}
if ($privateKeyExcluded) {
    Write-PreflightPass "(6) indexnow-key.txt IS excluded by .assetsignore (private key not deployed)"
} else {
    Write-PreflightWarn "(6) indexnow-key.txt NOT excluded by .assetsignore — private key may leak. Add 'indexnow-key.txt' to .assetsignore."
}

Write-Host ""
if ($preflightFailures -gt 0) {
    Write-Host "Preflight FAILED with $preflightFailures error(s). Fix the issues above before submitting." -ForegroundColor Red
    Write-Host "  - Run with -DryRun to skip the POST." -ForegroundColor Gray
    exit 1
} else {
    Write-Host "Preflight OK." -ForegroundColor Green
}

# ---------- 1.6. Live URL check — 部署后 GET <keyLocation> 验证真的返回 key ----------
if (-not $SkipLiveCheck) {
    Write-Host ""
    Write-Host "=== Live URL check: GET $keyLocation ===" -ForegroundColor Cyan
    try {
        $live = Invoke-WebRequest -Uri $keyLocation -UseBasicParsing -TimeoutSec 15
        $liveBody = ($live.Content -replace '^\xEF\xBB\xBF', '').Trim()
        if ($live.StatusCode -eq 200 -and $liveBody -eq $apiKey) {
            Write-Host "  [PASS] Live GET returns the key as plain text" -ForegroundColor Green
        } elseif ($live.StatusCode -eq 200) {
            Write-Host "  [FAIL] Live GET returned 200 but body is [$liveBody], expected [$apiKey]" -ForegroundColor Red
            Write-Host "          The file is being served but content is wrong." -ForegroundColor Yellow
            exit 1
        } else {
            Write-Host "  [FAIL] Live GET returned $($live.StatusCode) — file not deployed yet" -ForegroundColor Red
            Write-Host "          Did you push to remote? Wait for CF Pages deploy to finish, then re-run." -ForegroundColor Yellow
            exit 1
        }
    } catch {
        $sc = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 'err' }
        Write-Host "  [FAIL] Live GET failed with $sc — file not deployed" -ForegroundColor Red
        Write-Host "          IndexNow will reject the submission. Push + wait for deploy, then re-run." -ForegroundColor Yellow
        Write-Host "          Or use -SkipLiveCheck if you're running locally before deploy." -ForegroundColor Gray
        exit 1
    }
}

# ---------- 2. 解析 sitemap ----------
if (-not $SitemapPath) {
    $SitemapPath = Join-Path $root "sitemap.xml"
}
if (-not $SitemapUrl) {
    $SitemapUrl = "https://$SiteHost/sitemap.xml"
}

if (-not (Test-Path $SitemapPath)) {
    Write-Host "ERROR: Sitemap not found at $SitemapPath" -ForegroundColor Red
    exit 1
}

[xml]$sitemap = Get-Content $SitemapPath -Raw
$urls = @()
$ns = @{ s = "http://www.sitemaps.org/schemas/sitemap/0.9" }
$locs = Select-Xml -Xml $sitemap -XPath "//s:loc" -Namespace $ns
foreach ($node in $locs) {
    $u = $node.Node.InnerText.Trim()
    if ($u) { $urls += $u }
}

if ($urls.Count -eq 0) {
    Write-Host "ERROR: No URLs found in sitemap." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Submitting $($urls.Count) URLs to IndexNow for host '$SiteHost'..." -ForegroundColor Cyan
Write-Host "  Key location: $keyLocation" -ForegroundColor DarkGray

if ($DryRun) {
    Write-Host ""
    Write-Host "[DRY RUN] Skipping POST. All checks above passed — safe to re-run without -DryRun." -ForegroundColor Yellow
    exit 0
}

# ---------- 3. POST ----------
$payload = @{
    host        = $SiteHost
    key         = $apiKey
    keyLocation = $keyLocation
    urlList     = $urls
} | ConvertTo-Json -Depth 5 -Compress

try {
    $response = Invoke-WebRequest -Uri "https://api.indexnow.org/IndexNow" `
        -Method Post `
        -ContentType "application/json; charset=utf-8" `
        -Body $payload `
        -UseBasicParsing `
        -TimeoutSec 60

    $code = $response.StatusCode
    if ($code -eq 200) {
        Write-Host ""
        Write-Host "OK - IndexNow accepted all $($urls.Count) URLs." -ForegroundColor Green
        Write-Host "Bing/Yandex/Seznam/Naver will recrawl these URLs in the next few minutes." -ForegroundColor Gray
    } else {
        Write-Host ""
        Write-Host "IndexNow returned status $code" -ForegroundColor Yellow
        Write-Host "Body: $($response.Content)" -ForegroundColor Gray
    }
} catch {
    $statusCode = $null
    if ($_.Exception.Response) {
        $statusCode = [int]$_.Exception.Response.StatusCode
    }
    $errBody = ""
    try {
        $stream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $errBody = $reader.ReadToEnd()
    } catch {}

    Write-Host ""
    if ($statusCode -eq 200) {
        Write-Host "OK - IndexNow accepted the submission." -ForegroundColor Green
    } elseif ($statusCode -eq 202) {
        Write-Host "OK - IndexNow accepted; will process soon." -ForegroundColor Green
    } elseif ($statusCode -eq 400) {
        Write-Host "FAIL (400) - Bad request. Check key format and keyLocation URL." -ForegroundColor Red
        Write-Host "  Verify $keyLocation is publicly accessible (returns the key as plain text)." -ForegroundColor Yellow
    } elseif ($statusCode -eq 403) {
        Write-Host "FAIL (403) - Key not verified yet. Make sure $keyTxtFileName is deployed to the site root." -ForegroundColor Red
    } elseif ($statusCode -eq 422) {
        Write-Host "FAIL (422) - urlList empty or malformed." -ForegroundColor Red
    } elseif ($statusCode -eq 429) {
        Write-Host "FAIL (429) - Rate limited (too many submissions). Try again later." -ForegroundColor Red
    } else {
        Write-Host "FAIL ($statusCode) - $errBody" -ForegroundColor Red
    }
    exit 1
}
