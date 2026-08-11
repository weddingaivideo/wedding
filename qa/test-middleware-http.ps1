#!/usr/bin/env pwsh
# HTTP probe for case-normalization middleware
$ErrorActionPreference = 'Stop'
$base = "http://127.0.0.1:8788"

function Test-Probe($url) {
    try {
        $r = Invoke-WebRequest -Uri $url -Method GET -MaximumRedirection 0 -UseBasicParsing `
            -Headers @{"User-Agent" = "Mavis-HTTP-Test/1.0"} -ErrorAction Stop
        return @($r.StatusCode, $r.Headers['Location'])
    } catch {
        $code = $null; $loc = $null
        $resp = $_.Exception.Response
        if ($resp) { $code = [int]$resp.StatusCode }
        try { if ($resp -and $resp.Headers) { $loc = $resp.Headers['Location'] } } catch {}
        return @($code, $loc)
    }
}

# path, expected_status, expected_location_substring (or "" for no check), label
$probes = @(
    @{ p = "/About/";                            want = 308; loc = "/about/"; label = "EN uppercase page" }
    @{ p = "/Pricing/";                          want = 308; loc = "/pricing/"; label = "EN uppercase pricing" }
    @{ p = "/BLOG/";                             want = 308; loc = "/blog/"; label = "EN uppercase blog" }
    @{ p = "/Order/";                            want = 308; loc = "/order/"; label = "EN uppercase order" }
    @{ p = "/ZH/Blog/Foo/";                      want = 308; loc = "/zh/blog/foo/"; label = "i18n mixed case" }
    @{ p = "/Ja/Blog/Bar/";                      want = 308; loc = "/ja/blog/bar/"; label = "i18n ja mixed case" }
    @{ p = "/STYLES.MIN.CSS";                    want = 308; loc = "/styles.min.css"; label = "asset uppercase" }
    @{ p = "/about/";                            want = 200; loc = ""; label = "EN lowercase (no redirect)" }
    @{ p = "/blog/";                             want = 200; loc = ""; label = "EN lowercase blog" }
    @{ p = "/zh/blog/restore-vhs-wedding-footage/"; want = 200; loc = ""; label = "i18n lowercase (no redirect)" }
    @{ p = "/favicon.ico";                       want = 200; loc = ""; label = "favicon exact path" }
    @{ p = "/FAVICON.ICO";                       want = 308; loc = "/favicon.ico"; label = "favicon uppercase" }
    @{ p = "/i18n/en.json";                      want = 200; loc = ""; label = "i18n JSON file (no redirect)" }
    @{ p = "/";                                  want = 200; loc = ""; label = "root" }
    @{ p = "/Blog/?utm=x";                       want = 308; loc = "utm=x"; label = "uppercase with query string" }
    @{ p = "/Pricing/#section";                  want = 308; loc = "/pricing/"; label = "uppercase with hash (hash not sent)" }
)

$pass = 0; $fail = 0
Write-Host ("{0,-50} {1,8}  {2,-40}  {3,-6} {4}" -f "URL", "Got", "Location", "Want", "OK")
Write-Host ("-" * 120)
foreach ($p in $probes) {
    $url = $base + $p.p
    $want = $p.want
    $wantLoc = $p.loc
    $r = Test-Probe $url
    $got = $r[0]; $gotLoc = $r[1]
    $statusOk = ($got -eq $want)
    $locOk = $true
    if ($wantLoc -and $wantLoc -ne "") {
        $locOk = $false
        if ($gotLoc -and $gotLoc.Contains($wantLoc)) { $locOk = $true }
    } else {
        # No location expected
        $locOk = ([string]::IsNullOrEmpty($gotLoc))
    }
    $ok = $statusOk -and $locOk
    if ($ok) { $pass++ } else { $fail++ }
    $mark = if ($ok) { "PASS" } else { "FAIL" }
    $locStr = if ([string]::IsNullOrEmpty($gotLoc)) { "<none>" } else { $gotLoc }
    Write-Host ("{0,-50} {1,8}  {2,-40}  {3,-6} {4}" -f $p.p, $got, $locStr, $want, $mark)
}
Write-Host ""
Write-Host "$pass passed, $fail failed"
exit $fail
