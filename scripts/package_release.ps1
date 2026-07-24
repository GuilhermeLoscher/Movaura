$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$dist = Join-Path $root "dist"
$packageName = "Movaura-0.9.0-source"
$stage = Join-Path $dist $packageName
$zip = Join-Path $dist "$packageName.zip"

$resolvedDist = [System.IO.Path]::GetFullPath($dist)
$resolvedStage = [System.IO.Path]::GetFullPath($stage)
if (-not $resolvedStage.StartsWith($resolvedDist + [System.IO.Path]::DirectorySeparatorChar)) {
    throw "Diretorio de pacote invalido: $resolvedStage"
}

if (Test-Path -LiteralPath $stage) {
    Remove-Item -LiteralPath $stage -Recurse -Force
}
if (Test-Path -LiteralPath $zip) {
    Remove-Item -LiteralPath $zip -Force
}

New-Item -ItemType Directory -Path $stage | Out-Null

$rootFiles = @(
    "app.py",
    "INICIAR_MOVAURA.cmd",
    "INSTALAR_DEPENDENCIAS.cmd",
    "LEIA-ME-PRIMEIRO.txt",
    "Movaura.cmd",
    "MovauraStartup.vbs",
    "README.md",
    "AUTHORS.md",
    "requirements.txt",
    "THIRD_PARTY_NOTICES.txt"
)
foreach ($file in $rootFiles) {
    Copy-Item -LiteralPath (Join-Path $root $file) -Destination $stage
}

foreach ($directory in @("core", "ui", "renderers", "plugins", "docs", "scripts", "installer")) {
    Copy-Item -LiteralPath (Join-Path $root $directory) -Destination $stage -Recurse
}
if (Test-Path -LiteralPath (Join-Path $root "licenses")) {
    Copy-Item -LiteralPath (Join-Path $root "licenses") -Destination $stage -Recurse
}

$tools = Join-Path $root "tools"
if (Test-Path -LiteralPath (Join-Path $tools "ffmpeg\bin\ffmpeg.exe")) {
    $stageFfmpeg = Join-Path $stage "tools\ffmpeg"
    New-Item -ItemType Directory -Path $stageFfmpeg -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $tools "ffmpeg\bin") -Destination $stageFfmpeg -Recurse
    foreach ($file in @("LICENSE.txt", "README.txt")) {
        $source = Join-Path $tools "ffmpeg\$file"
        if (Test-Path -LiteralPath $source) {
            Copy-Item -LiteralPath $source -Destination $stageFfmpeg
        }
    }
}

New-Item -ItemType Directory -Path (Join-Path $stage "data\profiles") -Force | Out-Null
foreach ($profile in @("default.json", "gif.json", "image.json", "opengl.json", "video.json")) {
    Copy-Item -LiteralPath (Join-Path $root "data\profiles\$profile") -Destination (Join-Path $stage "data\profiles")
}
$catalogManifest = Join-Path $root "data\catalog.json"
if (Test-Path -LiteralPath $catalogManifest) {
    Copy-Item -LiteralPath $catalogManifest -Destination (Join-Path $stage "data")
}

$nativeTargets = @(
    @{
        Source = "native_compositor_app\bin\movaura_native_compositor.exe"
        Target = "native_compositor_app\bin"
    },
    @{
        Source = "native_host\bin\movaura_native_host.dll"
        Target = "native_host\bin"
    },
    @{
        Source = "native_host_app\bin\movaura_host_probe.exe"
        Target = "native_host_app\bin"
    }
)
foreach ($native in $nativeTargets) {
    $target = Join-Path $stage $native.Target
    New-Item -ItemType Directory -Path $target -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $root $native.Source) -Destination $target
}

Get-ChildItem -LiteralPath $stage -Directory -Recurse -Force |
    Where-Object { $_.Name -eq "__pycache__" } |
    Remove-Item -Recurse -Force
Get-ChildItem -LiteralPath $stage -File -Recurse -Force |
    Where-Object { $_.Extension -in @(".pyc", ".pyo") } |
    Remove-Item -Force

Compress-Archive -LiteralPath $stage -DestinationPath $zip -CompressionLevel Optimal
Remove-Item -LiteralPath $stage -Recurse -Force
Get-Item -LiteralPath $zip | Select-Object FullName, Length, LastWriteTime
