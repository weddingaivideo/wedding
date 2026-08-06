# scripts/submit-indexnow.ps1
# 通过 IndexNow API 通知 Bing / Yandex / Seznam / Naver 站点地图已更新。
# IndexNow 替代了已停用的 bing.com/ping 端点。
#
# IndexNow API 文档: https://www.indexnow.org/
# 端点:             POST https://api.indexnow.org/IndexNow
#
# 一次性设置:
#   1. 随机生成一个 key（32+ hex 字符）—— 此脚本首次运行会自动生成
#   2. 在站点根目录创建 <key>.txt 文件，内容就是 key 本身
#   3. 部署后调用此脚本即可批量提交 URL
#
# 用法:
#   powershell -ExecutionPolicy Bypass -File scripts\submit-indexnow.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\submit-indexnow.ps1 -SitemapPath "C:\path\sitemap.xml"

param(
    [string]$SitemapPath = "",
    [string]$SiteHost = "weddingai.video",
    [string]$SitemapUrl = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

if (-not $SitemapPath) {
    $SitemapPath = Join-Path $root "sitemap.xml"
}
if (-not $SitemapUrl) {
    $SitemapUrl = "https://$SiteHost/sitemap.xml"
}

# ---------- 1. 准备 key ----------
$indexNowKeyFile = Join-Path $root "indexnow-key.txt"
$keyTxtFileName = ""
$apiKey = ""

if (Test-Path $indexNowKeyFile) {
    $apiKey = (Get-Content $indexNowKeyFile -Raw).Trim()
    $keyTxtFileName = "$apiKey.txt"
    $keyTxtOnDisk = Join-Path $root $keyTxtFileName
    if (-not (Test-Path $keyTxtOnDisk)) {
        Set-Content -Path $keyTxtOnDisk -Value $apiKey -NoNewline -Encoding UTF8
        Write-Host "  + Created verification file: $keyTxtFileName" -ForegroundColor Gray
    }
} else {
    # Generate a 32-char hex key
    $bytes = New-Object byte[] 16
    (New-Object Random).NextBytes($bytes)
    $apiKey = -join ($bytes | ForEach-Object { $_.ToString("x2") })
    Set-Content -Path $indexNowKeyFile -Value $apiKey -NoNewline -Encoding UTF8
    $keyTxtFileName = "$apiKey.txt"
    Set-Content -Path (Join-Path $root $keyTxtFileName) -Value $apiKey -NoNewline -Encoding UTF8
    Write-Host "  + Generated new IndexNow key: $apiKey" -ForegroundColor Green
    Write-Host "  + Created indexnow-key.txt (private, contains the key)" -ForegroundColor Gray
    Write-Host "  + Created $keyTxtFileName (public, must be deployed so IndexNow can verify)" -ForegroundColor Gray
}

$keyLocation = "https://$SiteHost/$keyTxtFileName"

# ---------- 2. 解析 sitemap ----------
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

# ---------- 3. 提交（IndexNow 单次最多 10,000 URL，本项目远低于此）----------
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
