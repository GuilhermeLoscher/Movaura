$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$targets = @(
    "dist",
    "build",
    "__pycache__",
    "release\ffmpeg-gpl-backup",
    "release\ffmpeg-lgpl-shared",
    "release\pyinstaller-work",
    "release\standalone-fixed",
    "release\ffmpeg-lgpl-shared.zip",
    "release\msix\MovauraPackage",
    "data\updates",
    "data\optimized_videos",
    "data\logs",
    "tools\ffmpeg\doc",
    "tools\ffmpeg\include",
    "tools\ffmpeg\lib",
    "tools\ffmpeg\presets",
    "perf-desktop-stderr.txt",
    "perf-desktop-stderr2.txt",
    "perf-desktop-stderr3.txt",
    "perf-hw-stderr.txt",
    "perf-preview-stderr.txt",
    "perf-seek8-stderr.txt"
)

foreach ($relative in $targets) {
    $path = Join-Path $root $relative
    if (-not (Test-Path -LiteralPath $path)) {
        continue
    }
    $full = [System.IO.Path]::GetFullPath($path)
    if (-not $full.StartsWith($root)) {
        throw "Recusando remover fora do workspace: $full"
    }
    Remove-Item -LiteralPath $full -Recurse -Force
    Write-Host "removido: $relative"
}
