param(
    [string]$PackagePath = "",
    [string]$ReportPath = ""
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$kit = "C:\Program Files (x86)\Windows Kits\10\App Certification Kit"
$appcert = Join-Path $kit "appcert.exe"

if (-not (Test-Path -LiteralPath $appcert)) {
    throw "Windows App Certification Kit nao encontrado. Instale o Windows SDK com App Certification Kit."
}

if ([string]::IsNullOrWhiteSpace($PackagePath)) {
    $candidate = Get-ChildItem -Path (Join-Path $root "release\msix") -Filter "*.msix" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($null -eq $candidate) {
        throw "Nenhum MSIX encontrado. Rode scripts\build_msix_package.ps1 primeiro."
    }
    $PackagePath = $candidate.FullName
}

if ([string]::IsNullOrWhiteSpace($ReportPath)) {
    $reports = Join-Path $root "release\certification"
    New-Item -ItemType Directory -Path $reports -Force | Out-Null
    $ReportPath = Join-Path $reports ("wack-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".xml")
}

Write-Host "Rodando Windows App Certification Kit em: $PackagePath"
$arguments = @(
    "/c",
    "`"$appcert`" test -appxpackagepath `"$PackagePath`" -reportoutputpath `"$ReportPath`""
)
& cmd.exe @arguments
if (-not (Test-Path -LiteralPath $ReportPath)) {
    throw "WACK nao gerou relatorio. Tente abrir appcertui.exe pelo Windows App Certification Kit."
}

$reportText = Get-Content -LiteralPath $ReportPath -Raw
if ($reportText -match 'OVERALL_RESULT="([^"]+)"') {
    $overall = $Matches[1]
    Write-Host "WACK overall result: $overall"
    if ($overall -eq "FAIL") {
        throw "WACK reprovou o pacote. Veja o relatorio: $ReportPath"
    }
}

Get-Item -LiteralPath $ReportPath | Select-Object FullName, Length, LastWriteTime
