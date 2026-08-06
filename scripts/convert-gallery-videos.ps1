if ($env:WEDDINGAI_ROOT) { $root = $env:WEDDINGAI_ROOT }
else { $root = Split-Path -Parent $PSScriptRoot }
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true

$imgDir = Join-Path $root 'images'
$ffmpeg = 'C:\ffmpeg\bin\ffmpeg.exe'

function Invoke-FFmpeg {
    param([string[]]$CmdArgs)
    $p = Start-Process -FilePath $ffmpeg -ArgumentList $CmdArgs -NoNewWindow -Wait -PassThru `
        -RedirectStandardOutput "$env:TEMP\ffmpeg-stdout.txt" `
        -RedirectStandardError "$env:TEMP\ffmpeg-stderr.txt"
    if ($p.ExitCode -ne 0) {
        $err = Get-Content "$env:TEMP\ffmpeg-stderr.txt" -Raw -ErrorAction SilentlyContinue
        throw "ffmpeg exit $($p.ExitCode): $err"
    }
}

# Process only the names that need it (skip ones already done)
$all = @('dance', 'sangeet', 'tea')

foreach ($n in $all) {
    $mp4 = Join-Path $imgDir "case-slow-motion-$n.mp4"
    $webm = Join-Path $imgDir "case-slow-motion-$n.webm"
    $posterWebp = Join-Path $imgDir "case-slow-motion-$n-poster.webp"
    $poster1280Avif = Join-Path $imgDir "case-slow-motion-$n-poster-1280.avif"
    $poster640Avif = Join-Path $imgDir "case-slow-motion-$n-poster-640.avif"

    if (-not (Test-Path $mp4)) { Write-Warning "Missing ${mp4}"; continue }

    # Validate mp4 by checking the last 4KB contains the "moov" atom string.
    $bytes = [System.IO.File]::ReadAllBytes($mp4)
    $tailLen = [Math]::Min(4096, $bytes.Length)
    $tail = New-Object byte[] $tailLen
    [Array]::Copy($bytes, $bytes.Length - $tailLen, $tail, 0, $tailLen)
    $asString = [System.Text.Encoding]::ASCII.GetString($tail)
    if ($asString -notmatch 'moov') {
        Write-Warning "  ${n}: mp4 has no trailing moov box (corrupt), skipping"
        continue
    }

    if (Test-Path $webm) { Write-Host "  ${n}: webm exists, skip" } else {
        Write-Host "=== ${n}: webm ===" -ForegroundColor Cyan
        Invoke-FFmpeg -CmdArgs @('-y','-i',$mp4,'-c:v','libvpx-vp9','-b:v','600k','-deadline','good','-cpu-used','2','-row-mt','1','-pix_fmt','yuv420p','-an',$webm)
    }

    if (Test-Path $posterWebp) { Write-Host "  ${n}: poster exists, skip" } else {
        Write-Host "=== ${n}: poster 1280x720 ===" -ForegroundColor Cyan
        $posterPng = Join-Path $imgDir "_poster_$n.png"
        Invoke-FFmpeg -CmdArgs @('-y','-ss','1','-i',$mp4,'-frames:v','1','-vf','scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black',$posterPng)
        Invoke-FFmpeg -CmdArgs @('-y','-i',$posterPng,'-c:v','libwebp','-lossless','0','-q:v','80','-compression_level','6',$posterWebp)
        Copy-Item $posterWebp (Join-Path $imgDir "case-slow-motion-$n-poster-1280.webp") -Force
        Invoke-FFmpeg -CmdArgs @('-y','-i',$posterPng,'-c:v','libaom-av1','-still-picture','1','-crf','28','-cpu-used','4',$poster1280Avif)
        $posterPng640 = Join-Path $imgDir "_poster_${n}_640.png"
        Invoke-FFmpeg -CmdArgs @('-y','-i',$posterPng,'-vf','scale=640:360',$posterPng640)
        Invoke-FFmpeg -CmdArgs @('-y','-i',$posterPng640,'-c:v','libwebp','-lossless','0','-q:v','78','-compression_level','6',(Join-Path $imgDir "case-slow-motion-$n-poster-640.webp"))
        Invoke-FFmpeg -CmdArgs @('-y','-i',$posterPng640,'-c:v','libaom-av1','-still-picture','1','-crf','30','-cpu-used','4',$poster640Avif)
        Remove-Item $posterPng, $posterPng640 -ErrorAction SilentlyContinue
    }
    Write-Host "  ${n}: done" -ForegroundColor Green
}

Remove-Item "$env:TEMP\ffmpeg-stdout.txt","$env:TEMP\ffmpeg-stderr.txt" -ErrorAction SilentlyContinue
Write-Host ""
Write-Host "All done." -ForegroundColor Green
