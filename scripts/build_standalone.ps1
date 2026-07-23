param(
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$dist = Join-Path $root "dist\standalone"
$work = Join-Path $root "build\pyinstaller"
$reports = Join-Path $root "release\reports"
$report = Join-Path $reports "standalone-validation.txt"

function Resolve-BuildPython {
    param([string]$Requested)
    $candidates = @()
    if ($Requested) { $candidates += $Requested }
    if ($env:MOVAURA_BUILD_PYTHON) { $candidates += $env:MOVAURA_BUILD_PYTHON }
    $candidates += Join-Path $root ".build-venv\Scripts\python.exe"
    $candidates += Join-Path (Split-Path $root -Parent) ".build-venv\Scripts\python.exe"
    $candidates += "python"
    foreach ($candidate in $candidates) {
        try {
            $resolved = (Get-Command $candidate -ErrorAction Stop).Source
            if ($resolved) { return $resolved }
        } catch {
            if (Test-Path -LiteralPath $candidate) { return $candidate }
        }
    }
    throw "Python de build nao encontrado. Informe -PythonExe ou configure MOVAURA_BUILD_PYTHON."
}

function Invoke-ExeChecked {
    param([string]$Label, [string]$ExePath, [string[]]$Arguments)
    Write-Host "[Movaura build] $Label"
    $process = Start-Process -FilePath $ExePath -ArgumentList $Arguments -Wait -PassThru -NoNewWindow
    if ($process.ExitCode -ne 0) {
        throw "$Label falhou com codigo $($process.ExitCode)"
    }
}
function Invoke-Checked {
    param([string]$Label, [scriptblock]$Command)
    Write-Host "[Movaura build] $Label"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label falhou com codigo $LASTEXITCODE"
    }
}

$python = Resolve-BuildPython $PythonExe
New-Item -ItemType Directory -Path $reports -Force | Out-Null
"Movaura standalone validation - $(Get-Date -Format o)" | Set-Content -LiteralPath $report -Encoding UTF8
"Python: $python" | Add-Content -LiteralPath $report -Encoding UTF8

Invoke-Checked "compileall" { & $python -m compileall -q app.py core renderers ui plugins scripts }
Invoke-Checked "product smoke tests" {
    $env:QT_QPA_PLATFORM = "offscreen"
    $env:PYTHONDONTWRITEBYTECODE = "1"
    & $python scripts\run_product_smoke_tests.py
}
Invoke-Checked "self-test dev" { & $python app.py --self-test }

foreach ($path in @($dist, $work)) {
    $resolved = [System.IO.Path]::GetFullPath($path)
    if (-not $resolved.StartsWith($root + [System.IO.Path]::DirectorySeparatorChar)) {
        throw "Diretorio de build invalido: $resolved"
    }
    if (Test-Path -LiteralPath $resolved) {
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}

$nativeCompositor = Join-Path $root "native_compositor_app\bin\movaura_native_compositor.exe"
$nativeHost = Join-Path $root "native_host\bin\movaura_native_host.dll"
$nativeProbe = Join-Path $root "native_host_app\bin\movaura_host_probe.exe"
$plugins = Join-Path $root "plugins"
$wallpapers = Join-Path $root "wallpapers"
$assets = Join-Path $root "assets"
$tools = Join-Path $root "tools"
$catalogManifest = Join-Path $root "data\catalog.json"
$licenses = Join-Path $root "licenses"

foreach ($path in @($nativeCompositor, $nativeHost, $nativeProbe, $plugins, $wallpapers, $assets, $catalogManifest)) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Recurso obrigatorio ausente: $path"
    }
}

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
    "--add-data", "$assets;assets",
    "--add-data", "$catalogManifest;data"
)
if (Test-Path -LiteralPath $licenses) {
    $pyinstallerArgs += @("--add-data", "$licenses;licenses")
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
    "FFmpeg: LGPL check passed" | Add-Content -LiteralPath $report -Encoding UTF8
} else {
    "FFmpeg: not bundled" | Add-Content -LiteralPath $report -Encoding UTF8
}
$pyinstallerArgs += (Join-Path $root "app.py")

Invoke-Checked "PyInstaller" { & $python @pyinstallerArgs }

$applicationRoot = Join-Path $dist "Movaura"
$application = Join-Path $applicationRoot "Movaura.exe"
if (-not (Test-Path -LiteralPath $application)) {
    throw "Executavel autocontido nao foi criado: $application"
}

Copy-Item -LiteralPath $wallpapers -Destination $applicationRoot -Recurse -Force
Invoke-ExeChecked "self-test standalone" $application @("--self-test")

$copyWithSpacesRoot = Join-Path $root "build\Path With Spaces\Movaura"
if (Test-Path -LiteralPath $copyWithSpacesRoot) {
    Remove-Item -LiteralPath $copyWithSpacesRoot -Recurse -Force
}
New-Item -ItemType Directory -Path (Split-Path $copyWithSpacesRoot -Parent) -Force | Out-Null
Copy-Item -LiteralPath $applicationRoot -Destination $copyWithSpacesRoot -Recurse -Force
Invoke-ExeChecked "self-test standalone path with spaces" (Join-Path $copyWithSpacesRoot "Movaura.exe") @("--self-test")
for ($attempt = 1; $attempt -le 5; $attempt++) {
    try {
        Remove-Item -LiteralPath $copyWithSpacesRoot -Recurse -Force -ErrorAction Stop
        break
    } catch {
        if ($attempt -eq 5) {
            Write-Warning "Nao foi possivel limpar a copia temporaria de teste: $copyWithSpacesRoot"
        } else {
            Start-Sleep -Milliseconds (250 * $attempt)
        }
    }
}
$item = Get-Item -LiteralPath $application
"Standalone: $($item.FullName)" | Add-Content -LiteralPath $report -Encoding UTF8
"Size: $($item.Length)" | Add-Content -LiteralPath $report -Encoding UTF8
"Validation: ok" | Add-Content -LiteralPath $report -Encoding UTF8
$item | Select-Object FullName, Length, LastWriteTime
Write-Host "Relatorio: $report"
