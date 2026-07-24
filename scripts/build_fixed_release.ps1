$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path (Split-Path $root -Parent) ".build-venv\Scripts\python.exe"
$dist = Join-Path $root "release\standalone-commercial"
$work = Join-Path ([System.IO.Path]::GetTempPath()) ("movaura-pyinstaller-work-" + (Get-Date -Format "yyyyMMdd-HHmmss"))

foreach ($path in @($dist, $work)) {
    if (Test-Path -LiteralPath $path) {
        Remove-Item -LiteralPath $path -Recurse -Force
    }
}
New-Item -ItemType Directory -Path (Split-Path $dist -Parent) -Force | Out-Null

$nativeCompositor = Join-Path $root "native_compositor_app\bin\movaura_native_compositor.exe"
$nativeHost = Join-Path $root "native_host\bin\movaura_native_host.dll"
$nativeProbe = Join-Path $root "native_host_app\bin\movaura_host_probe.exe"
$plugins = Join-Path $root "plugins"
$wallpapers = Join-Path $root "wallpapers"
$assets = Join-Path $root "assets"
$tools = Join-Path $root "tools"
$catalogManifest = Join-Path $root "data\catalog.json"
$licenses = Join-Path $root "licenses"

$pyinstallerArgs = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--windowed",
    "--onedir",
    "--name", "Movaura",
    "--icon", (Join-Path $assets "movaura.ico"),
    "--manifest", (Join-Path $assets "movaura.exe.manifest"),
    "--distpath", $dist,
    "--workpath", $work,
    "--specpath", $work,
    "--add-binary", "$nativeCompositor;native_compositor_app\bin",
    "--add-binary", "$nativeHost;native_host\bin",
    "--add-binary", "$nativeProbe;native_host_app\bin",
    "--add-data", "$plugins;plugins",
    "--add-data", "$assets;assets"
)
if (Test-Path -LiteralPath $licenses) {
    $pyinstallerArgs += @("--add-data", "$licenses;licenses")
}
$thirdPartyNotice = Join-Path $root "THIRD_PARTY_NOTICES.txt"
if (Test-Path -LiteralPath $thirdPartyNotice) {
    $pyinstallerArgs += @("--add-data", "$thirdPartyNotice;.")
}
if (Test-Path -LiteralPath $catalogManifest) {
    $pyinstallerArgs += @("--add-data", "$catalogManifest;data")
}
if (Test-Path -LiteralPath (Join-Path $tools "ffmpeg\bin\ffmpeg.exe")) {
    $ffmpegRoot = Join-Path $tools "ffmpeg"
    $ffmpegExe = Join-Path $ffmpegRoot "bin\ffmpeg.exe"
    $ffmpegVersion = (& $ffmpegExe -version 2>&1) -join "`n"
    $ffmpegConfig = ($ffmpegVersion -split "`n" | Where-Object { $_ -like "configuration:*" } | Select-Object -First 1).ToLowerInvariant()
    if ($ffmpegConfig -match "--enable-gpl" -or $ffmpegConfig -match "--enable-nonfree" -or $ffmpegConfig -notmatch "--disable-libx264" -or $ffmpegConfig -notmatch "--disable-libx265") {
        throw "FFmpeg comercial bloqueado: o build em tools\ffmpeg parece GPL/nonfree."
    }
    $pyinstallerArgs += @("--add-data", "$(Join-Path $ffmpegRoot 'bin');tools\ffmpeg\bin")
    foreach ($licenseFile in @("LICENSE.txt", "README.txt")) {
        $licensePath = Join-Path $ffmpegRoot $licenseFile
        if (Test-Path -LiteralPath $licensePath) {
            $pyinstallerArgs += @("--add-data", "$licensePath;tools\ffmpeg")
        }
    }
}
$pyinstallerArgs += (Join-Path $root "app.py")

& $python @pyinstallerArgs
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller encerrou com codigo $LASTEXITCODE"
}

Copy-Item -LiteralPath $wallpapers -Destination (Join-Path $dist "Movaura") -Recurse

Get-Item -LiteralPath (Join-Path $dist "Movaura\Movaura.exe") | Select-Object FullName, Length, LastWriteTime
