$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true

$imgDir = 'C:\Users\qiaoshan\.openclaw\workspace\weddingai\images'
$ffmpeg = 'C:\ffmpeg\bin\ffmpeg.exe'
$src = Join-Path $imgDir 'case-slow-motion-sangeet-ref.png'

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

# target sizes
$sizes = @(360, 720, 1280)
$name = 'gallery-slow-motion-sangeet'

# master jpg (full, just to overwrite if needed)
Write-Host "=== master jpg / webp / avif ===" -ForegroundColor Cyan
Invoke-FFmpeg -CmdArgs @('-y','-i',$src,'-q:v','2',(Join-Path $imgDir "$name.jpg"))
Invoke-FFmpeg -CmdArgs @('-y','-i',$src,'-c:v','libwebp','-lossless','0','-q:v','82','-compression_level','6',(Join-Path $imgDir "$name.webp"))
Invoke-FFmpeg -CmdArgs @('-y','-i',$src,'-c:v','libaom-av1','-still-picture','1','-crf','30','-cpu-used','4',(Join-Path $imgDir "$name.avif"))

foreach ($w in $sizes) {
    $h = [int]($w * 9 / 16)  # 16:9 aspect
    $tmp = Join-Path $imgDir "_sangeet_${w}.png"
    Write-Host "=== ${w}x${h} ===" -ForegroundColor Cyan
    Invoke-FFmpeg -CmdArgs @('-y','-i',$src,'-vf',"scale=${w}:${h}:force_original_aspect_ratio=decrease,pad=${w}:${h}:(ow-iw)/2:(oh-ih)/2:color=black",$tmp)
    Invoke-FFmpeg -CmdArgs @('-y','-i',$tmp,'-q:v','3',(Join-Path $imgDir "$name-${w}.jpg"))
    Invoke-FFmpeg -CmdArgs @('-y','-i',$tmp,'-c:v','libwebp','-lossless','0','-q:v','80','-compression_level','6',(Join-Path $imgDir "$name-${w}.webp"))
    Invoke-FFmpeg -CmdArgs @('-y','-i',$tmp,'-c:v','libaom-av1','-still-picture','1','-crf','30','-cpu-used','4',(Join-Path $imgDir "$name-${w}.avif"))
    Remove-Item $tmp -ErrorAction SilentlyContinue
}

Remove-Item "$env:TEMP\ffmpeg-stdout.txt","$env:TEMP\ffmpeg-stderr.txt" -ErrorAction SilentlyContinue
Write-Host "All done." -ForegroundColor Green
