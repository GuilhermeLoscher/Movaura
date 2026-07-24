param(
    [string]$PackageName = "GuilhermeLoscher.Movaura",
    [string]$Publisher = "CN=Guilherme Loscher",
    [string]$PublisherDisplayName = "Guilherme Loscher",
    [string]$Version = "0.9.0.0",
    [string]$StandalonePath = "",
    [string]$PythonExe = "",
    [switch]$StoreBuild,
    [switch]$AllowDefaultIdentity
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $StandalonePath) {
    $StandalonePath = Join-Path $root "dist\standalone\Movaura"
}
$standalone = [System.IO.Path]::GetFullPath($StandalonePath)
$layout = Join-Path $root "release\msix\MovauraPackage"
$outputDir = Join-Path $root "release\msix"
$output = Join-Path $outputDir "Movaura-$Version.msix"
$kitCandidates = @(
    "C:\Program Files (x86)\Windows Kits\10\App Certification Kit\makeappx.exe",
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\makeappx.exe",
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\makeappx.exe"
)
$makeappx = $kitCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

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
    throw "Python de build nao encontrado para gerar assets MSIX."
}

if (-not (Test-Path -LiteralPath $standalone)) {
    throw "Standalone nao encontrado: $standalone. Rode scripts\build_standalone.ps1 primeiro."
}
if (-not (Test-Path -LiteralPath (Join-Path $standalone "Movaura.exe"))) {
    throw "Standalone invalido: Movaura.exe ausente em $standalone."
}
if (-not $makeappx) {
    throw "makeappx.exe nao encontrado. Instale Windows SDK/App Certification Kit para gerar MSIX."
}
$python = Resolve-BuildPython $PythonExe
if ($StoreBuild -and -not $AllowDefaultIdentity) {
    if ($PackageName -eq "GuilhermeLoscher.Movaura" -or $Publisher -eq "CN=Guilherme Loscher") {
        throw "StoreBuild exige identidade real do Partner Center ou -AllowDefaultIdentity explicito para build tecnico local."
    }
}

if (Test-Path -LiteralPath $layout) {
    Remove-Item -LiteralPath $layout -Recurse -Force
}
New-Item -ItemType Directory -Path $layout -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $layout "Assets") -Force | Out-Null
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

Get-ChildItem -LiteralPath $standalone -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $layout -Recurse -Force
}
& $python (Join-Path $root "scripts\prepare_msix_assets.py") (Join-Path $root "assets\movaura-logo.png") (Join-Path $layout "Assets")
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao gerar assets MSIX."
}

$manifest = @"
<?xml version="1.0" encoding="utf-8"?>
<Package
  xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
  xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
  xmlns:desktop="http://schemas.microsoft.com/appx/manifest/desktop/windows10"
  xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
  IgnorableNamespaces="uap desktop rescap">
  <Identity Name="$PackageName" Publisher="$Publisher" Version="$Version" ProcessorArchitecture="x64" />
  <Properties>
    <DisplayName>Movaura</DisplayName>
    <PublisherDisplayName>$PublisherDisplayName</PublisherDisplayName>
    <Logo>Assets\StoreLogo.png</Logo>
  </Properties>
  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.19041.0" MaxVersionTested="10.0.26200.0" />
  </Dependencies>
  <Resources>
    <Resource Language="pt-br" />
    <Resource Language="en-us" />
  </Resources>
  <Applications>
    <Application Id="Movaura" Executable="Movaura.exe" EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements
        DisplayName="Movaura"
        Description="Live wallpapers otimizados para Windows."
        BackgroundColor="transparent"
        Square44x44Logo="Assets\Square44x44Logo.png"
        Square150x150Logo="Assets\Square150x150Logo.png" />
      <Extensions>
        <desktop:Extension Category="windows.fullTrustProcess" Executable="Movaura.exe" />
      </Extensions>
    </Application>
  </Applications>
  <Capabilities>
    <rescap:Capability Name="runFullTrust" />
  </Capabilities>
</Package>
"@

Set-Content -LiteralPath (Join-Path $layout "AppxManifest.xml") -Value $manifest -Encoding UTF8

if (Test-Path -LiteralPath $output) {
    Remove-Item -LiteralPath $output -Force
}
& $makeappx pack /d $layout /p $output /overwrite
if ($LASTEXITCODE -ne 0) {
    throw "makeappx encerrou com codigo $LASTEXITCODE"
}

& $python (Join-Path $root "scripts\validate_msix_layout.py") $layout --expected-package-name $PackageName --expected-publisher $Publisher --reports (Join-Path $root "release\reports")
if ($LASTEXITCODE -ne 0) {
    throw "Validacao do layout MSIX falhou."
}
& $python (Join-Path $root "scripts\check_no_pyqt_artifacts.py") --artifact $layout --report-base (Join-Path $root "release\reports\qt-binding-audit-msix")
if ($LASTEXITCODE -ne 0) {
    throw "Validacao PySide/PyQt do MSIX falhou."
}
& $python (Join-Path $root "scripts\generate_artifact_reports.py") $layout --name msix --reports (Join-Path $root "release\reports")
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao gerar inventario MSIX."
}
Get-FileHash -LiteralPath $output -Algorithm SHA256 |
    ForEach-Object { "$($_.Hash)  $($_.Path)" } |
    Set-Content -LiteralPath (Join-Path $root "release\reports\msix-package-sha256.txt") -Encoding UTF8

Get-Item -LiteralPath $output | Select-Object FullName, Length, LastWriteTime
Write-Host "Pacote MSIX gerado sem assinatura local. Assine com scripts\sign_msix.ps1 e os dados reservados no Partner Center."
