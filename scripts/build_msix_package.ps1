param(
    [string]$PackageName = "GuilhermeLoscher.Movaura",
    [string]$Publisher = "CN=Guilherme Loscher",
    [string]$PublisherDisplayName = "Guilherme Loscher",
    [string]$Version = "0.9.0.0"
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$standalone = Join-Path $root "release\standalone-commercial\Movaura"
$layout = Join-Path $root "release\msix\MovauraPackage"
$outputDir = Join-Path $root "release\msix"
$output = Join-Path $outputDir "Movaura-$Version.msix"
$kit = "C:\Program Files (x86)\Windows Kits\10\App Certification Kit"
$makeappx = Join-Path $kit "makeappx.exe"
$python = Join-Path (Split-Path $root -Parent) ".build-venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $standalone)) {
    throw "Standalone nao encontrado. Rode scripts\build_fixed_release.ps1 primeiro."
}
if (-not (Test-Path -LiteralPath $makeappx)) {
    throw "makeappx.exe nao encontrado. Instale o Windows SDK/App Certification Kit."
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
if (-not (Test-Path -LiteralPath $python)) {
    $python = Join-Path $root ".build-venv\Scripts\python.exe"
}
if (-not (Test-Path -LiteralPath $python)) {
    throw "Python de build nao encontrado para gerar assets MSIX."
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

Get-Item -LiteralPath $output | Select-Object FullName, Length, LastWriteTime
Write-Host "Pacote MSIX gerado sem assinatura local. Para Partner Center, ajuste Identity/Publisher com os dados reservados na conta da Microsoft Store."
