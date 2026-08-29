$ErrorActionPreference = 'Stop'

$frontendRoot = $PSScriptRoot
$projectRoot = Split-Path $frontendRoot -Parent
$distRoot = Join-Path $frontendRoot 'dist'
$outputFile = Join-Path $projectRoot 'ReGrow-AI-作业3-双击打开.html'

Push-Location $frontendRoot
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { throw '前端构建失败' }
} finally {
    Pop-Location
}

$html = Get-Content -LiteralPath (Join-Path $distRoot 'index.html') -Raw -Encoding UTF8
$scriptMatch = [regex]::Match($html, '<script type="module" crossorigin src="([^"]+)"></script>')
$styleMatch = [regex]::Match($html, '<link rel="stylesheet" crossorigin href="([^"]+)">')
if (-not $scriptMatch.Success -or -not $styleMatch.Success) { throw '没有找到构建后的 JS 或 CSS' }

$scriptPath = Join-Path $distRoot $scriptMatch.Groups[1].Value.TrimStart('/')
$stylePath = Join-Path $distRoot $styleMatch.Groups[1].Value.TrimStart('/')
$javascript = Get-Content -LiteralPath $scriptPath -Raw -Encoding UTF8
$stylesheet = Get-Content -LiteralPath $stylePath -Raw -Encoding UTF8

$logoPath = Join-Path $frontendRoot 'public\regrow-mark.png'
$logoBase64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($logoPath))
$logoDataUrl = "data:image/png;base64,$logoBase64"
$javascript = $javascript.Replace('"/regrow-mark.png"', '"' + $logoDataUrl + '"')
$javascript = $javascript.Replace('</script', '<\/script')

$singleFile = $html.Replace($scriptMatch.Value, "<script type=`"module`">$javascript</script>")
$singleFile = $singleFile.Replace($styleMatch.Value, "<style>$stylesheet</style>")
$singleFile = [regex]::Replace($singleFile, '<link rel="icon"[^>]*>', "<link rel=`"icon`" href=`"$logoDataUrl`">")
$singleFile = $singleFile.Replace('<body>', '<body><noscript>请启用浏览器 JavaScript 后重新打开。</noscript>')

[IO.File]::WriteAllText($outputFile, $singleFile, [Text.UTF8Encoding]::new($false))
Write-Host "离线单文件已生成：$outputFile"
