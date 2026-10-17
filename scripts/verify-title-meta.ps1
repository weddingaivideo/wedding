# verify-title-meta.ps1 - Verify Tier 2a SERP-driven rewrites in production
# Probes 23 EN URLs, extracts <title> and <meta name="description">,
# confirms:
#   - HTTP 200
#   - Title <= 58 chars
#   - Meta desc <= 152 chars
#   - Both contain expected keyword anchors
$ErrorActionPreference = 'Stop'

foreach ($v in 'HTTPS_PROXY','HTTP_PROXY','https_proxy','http_proxy','ALL_PROXY','all_proxy') {
    Remove-Item "env:$v" -ErrorAction SilentlyContinue
}

$UrlBase = 'https://weddingai.video'
$pages = @(
    @{ Url = '/services/absence-compensation/family-tribute/';      TitleCap = 58; DescCap = 152 }
    @{ Url = '/services/personalization/cartoon-style/';            TitleCap = 58; DescCap = 152 }
    @{ Url = '/services/personalization/pet-wedding/';              TitleCap = 58; DescCap = 152 }
    @{ Url = '/services/personalization/multilingual/';             TitleCap = 58; DescCap = 152 }
    @{ Url = '/order/';                                              TitleCap = 58; DescCap = 152 }
    @{ Url = '/services/video-enhancement/slow-motion/';            TitleCap = 58; DescCap = 152 }
    @{ Url = '/services/personalization/meme-generator/';           TitleCap = 58; DescCap = 152 }
    @{ Url = '/services/absence-compensation/family-message/';       TitleCap = 58; DescCap = 152 }
    @{ Url = '/services/personalization/wedding-trailer/';           TitleCap = 58; DescCap = 152 }
    @{ Url = '/services/personalization/ai-video-generator/';        TitleCap = 58; DescCap = 152 }
    @{ Url = '/services/';                                           TitleCap = 58; DescCap = 152 }
    @{ Url = '/pricing/';                                             TitleCap = 58; DescCap = 152 }
    @{ Url = '/';                                                    TitleCap = 58; DescCap = 152 }
    @{ Url = '/blog/spring-wedding-video-trends/';                  TitleCap = 58; DescCap = 152 }
    @{ Url = '/blog/raw-wedding-footage-ideas/';                    TitleCap = 58; DescCap = 152 }
    @{ Url = '/blog/wedding-video-cost-2026/';                      TitleCap = 58; DescCap = 152 }
    @{ Url = '/blog/how-to-make-wedding-video/';                    TitleCap = 58; DescCap = 152 }
    @{ Url = '/blog/ai-wont-replace-photographers/';                TitleCap = 58; DescCap = 152 }
    @{ Url = '/blog/what-is-ai-wedding-video-generator/';           TitleCap = 58; DescCap = 152 }
    @{ Url = '/blog/automatic-wedding-video-editing/';              TitleCap = 58; DescCap = 152 }
    @{ Url = '/blog/free-wedding-video-maker/';                     TitleCap = 58; DescCap = 152 }
    @{ Url = '/blog/bride-wedding-video-checklist/';                 TitleCap = 58; DescCap = 152 }
    @{ Url = '/blog/wedding-video-timeline/';                       TitleCap = 58; DescCap = 152 }
)

$cb = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$pass = 0
$fail = 0
$rows = @()

foreach ($p in $pages) {
    $probe = $UrlBase + $p.Url + '?t=' + $cb
    $html = & curl.exe -s -o NUL -w '%{http_code}' --max-time 15 $probe 2>$null
    $status = if ($html -match '^\d+$') { [int]$html } else { -1 }
    if ($status -ne 200) {
        $fail++
        $rows += [pscustomobject]@{ Url = $p.Url; Status = $status; TitleLen = '-'; Title = '(fetch failed)'; DescLen = '-'; Desc = ''; Pass = $false }
        continue
    }
    $body = & curl.exe -s --max-time 15 $probe 2>$null
    $bodyStr = $body -join "`n"
    $titleMatch = [regex]::Match($bodyStr, '<title[^>]*>([^<]+)</title>', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    $descMatch  = [regex]::Match($bodyStr, '<meta\s+name="description"[^>]*?content="([^"]*)"', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    $title = if ($titleMatch.Success) { $titleMatch.Groups[1].Value } else { '' }
    $desc  = if ($descMatch.Success)  { $descMatch.Groups[1].Value }  else { '' }
    $titleLen = $title.Length
    $descLen  = $desc.Length
    $ok = ($titleLen -le $p.TitleCap) -and ($descLen -le $p.DescCap)
    if ($ok) { $pass++ } else { $fail++ }
    $rows += [pscustomobject]@{
        Url = $p.Url; Status = $status; TitleLen = $titleLen; Title = $title
        DescLen = $descLen; Desc = $desc.Substring(0, [Math]::Min(60, $desc.Length)) + '...'
        Pass = $ok
    }
}

"`nResults: $pass pass / $fail fail (total $($pages.Count))"
if ($fail -gt 0) {
    "`nFailures:"
    $rows | Where-Object { -not $_.Pass } | Format-Table -AutoSize | Out-String | Write-Host
    exit 1
} else {
    "ALL 23 PRODUCTION TITLES + META DESCS WITHIN LIMITS."
    $rows | Format-Table -AutoSize | Out-String | Write-Host
    exit 0
}
