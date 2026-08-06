# scripts/ping-bing.ps1
# 通知 Bing 站点地图已更新。
# Bing 支持 sitemap ping endpoint（Google 已停用）。
#
# 用法:
#   .\scripts\ping-bing.ps1                          # 用默认 sitemap URL
#   .\scripts\ping-bing.ps1 -SitemapUrl "..."        # 指定 sitemap URL
#   .\scripts\ping-bing.ps1 -Production               # 用生产域名
#
# 返回 XML 响应表示成功。

param(
    [string]$SitemapUrl = "",
    [switch]$Production
)

$ErrorActionPreference = "Stop"

if ($Production -or $SitemapUrl -eq "") {
    $SitemapUrl = "https://weddingai.video/sitemap.xml"
}

$pingUrl = "https://www.bing.com/ping?sitemap=" + [System.Uri]::EscapeDataString($SitemapUrl)

Write-Host "Pinging Bing: $pingUrl" -ForegroundColor Cyan

try {
    $response = Invoke-WebRequest -Uri $pingUrl -UseBasicParsing -TimeoutSec 30
    $body = $response.Content
    if ($body -match "<success>") {
        Write-Host ""
        Write-Host "OK - Bing accepted the sitemap." -ForegroundColor Green
        Write-Host "Response:" -ForegroundColor Gray
        Write-Host $body
    } elseif ($body -match "<failure") {
        Write-Host ""
        Write-Host "FAIL - Bing rejected the sitemap." -ForegroundColor Red
        Write-Host "Response:" -ForegroundColor Gray
        Write-Host $body
        exit 1
    } else {
        Write-Host ""
        Write-Host "Ping returned status $($response.StatusCode) but unexpected body." -ForegroundColor Yellow
        Write-Host "Body:" -ForegroundColor Gray
        Write-Host $body
    }
} catch {
    Write-Host ""
    Write-Host "Error pinging Bing: $_" -ForegroundColor Red
    exit 1
}
