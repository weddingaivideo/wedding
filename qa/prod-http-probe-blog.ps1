#!/usr/bin/env powershell
# Blog date diversification probe (Part 2 of 24-probe matrix)
# Pairs with prod-http-probe.ps1 (16 case-normalization probes).
# This script: 8 probes for the new blog ItemList / card / i18n behavior
# added 2026-08-11.

$ErrorActionPreference = 'Stop'
$base = if ($args.Count -gt 0) { $args[0] } else { "https://weddingai.video" }
Write-Host "Probing: $base"
Write-Host ""

function Test-Probe($url) {
    try {
        $r = Invoke-WebRequest -Uri $url -Method GET -MaximumRedirection 0 -UseBasicParsing `
            -Headers @{"User-Agent" = "Mavis-Prod-Probe/1.0"} -ErrorAction Stop
        return @($r.StatusCode, $r.Headers['Location'], $r.Content)
    } catch {
        $code = $null; $loc = $null
        $resp = $_.Exception.Response
        if ($resp) { $code = [int]$resp.StatusCode }
        try { if ($resp -and $resp.Headers) { $loc = $resp.Headers['Location'] } } catch {}
        $body = ""
        try { if ($resp) { $body = (New-Object System.IO.StreamReader($resp.GetResponseStream())).ReadToEnd() } } catch {}
        return @($code, $loc, $body)
    }
}

$probes = @(
    # 17: /blog/ serves 200 + has ItemList JSON-LD
    @{ p = "/blog/"; kind = "200_has_itemlist"; label = "EN blog index 200 + ItemList" }
    # 18: one of the 50 batch-stamped posts (already diversified in source)
    @{ p = "/blog/wedding-highlight-video/"; kind = "200_has_date"; expected_date = "2026-06-25"; label = "EN single post (diversified date 2026-06-25)" }
    # 19: zh lang version of same post (hash gives 2026-07-02)
    @{ p = "/zh/blog/wedding-highlight-video/"; kind = "200_has_date"; expected_date = "2026-07-02"; label = "ZH single post (diversified date 2026-07-02)" }
    # 20: EN blog index card text should NOT contain raw "Aug 1, 2026"
    @{ p = "/blog/"; kind = "card_no_aug1"; label = "EN blog index card text no Aug 1, 2026" }
    # 21: i18n zh blog index 200
    @{ p = "/zh/blog/"; kind = "200_has_itemlist"; label = "ZH blog index 200 + ItemList" }
    # 22: i18n ar blog post 200
    @{ p = "/ar/blog/wedding-highlight-video/"; kind = "200_has_date"; label = "AR single post 200" }
    # 23: legacy /en/blog/01-* redirect still works (per _redirects file)
    @{ p = "/en/blog/01-restore-old-wedding-videos/"; kind = "301_location"; expected_loc = "/en/blog/restore-vhs-wedding-footage/"; label = "EN legacy blog 01 redirect" }
    # 24: /styles.min.css (asset) 200
    @{ p = "/styles.min.css"; kind = "200"; label = "asset 200" }
)

$pass = 0; $fail = 0
Write-Host ("{0,-6} {1,-50} {2,-6} {3,-40}  {4}" -f "#", "URL", "Got", "Detail", "OK")
Write-Host ("-" * 130)
$i = 16
foreach ($p in $probes) {
    $i++
    $url = $base + $p.p
    $r = Test-Probe $url
    $got = $r[0]; $gotLoc = $r[1]; $body = $r[2]
    $ok = $false
    $detail = ""

    switch ($p.kind) {
        "200" {
            $ok = ($got -eq 200)
            $detail = "want 200"
        }
        "200_has_itemlist" {
            $ok = ($got -eq 200 -and $body.Contains('"@type":"ItemList"'))
            $detail = "want 200 + ItemList"
        }
        "200_has_date" {
            $ok = ($got -eq 200 -and $body.Contains($p.expected_date))
            $detail = "want 200 + contains '$($p.expected_date)'"
        }
        "card_no_aug1" {
            # The visible card text is in <article class="case-card"> blocks.
            # After middleware rewrite, none should still say "Aug 1, 2026".
            $has_aug1 = $body.Contains('Aug 1, 2026')
            $ok = ($got -eq 200 -and -not $has_aug1)
            $detail = if ($has_aug1) { "FAIL: still has 'Aug 1, 2026'" } else { "no 'Aug 1, 2026'" }
        }
        "301_location" {
            $ok = ($got -eq 301 -and $gotLoc -and $gotLoc.Contains($p.expected_loc))
            $detail = "want 301 -> $($p.expected_loc)"
        }
    }

    if ($ok) { $pass++ } else { $fail++ }
    $mark = if ($ok) { "PASS" } else { "FAIL" }
    Write-Host ("{0,-6} {1,-50} {2,-6} {3,-40}  {4}" -f $i, $p.p, $got, $detail, $mark)
}
Write-Host ""
Write-Host "$pass passed, $fail failed"
exit $fail
