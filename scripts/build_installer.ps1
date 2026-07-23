$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$iss = Join-Path $root "installer\MovauraFixedRelease.iss"
$standalone = Join-Path $root "release\standalone-commercial\Movaura\Movaura.exe"
$installer = Join-Path $root "release\installer\Movaura-Setup-0.9.0.exe"
$candidates = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)
$iscc = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if (-not $iscc) {
    throw "ISCC.exe nao encontrado. Instale o Inno Setup 6 e execute novamente."
}
if (-not (Test-Path -LiteralPath $standalone)) {
    throw "Aplicativo comercial ausente. Execute scripts\build_fixed_release.ps1 primeiro."
}

& $iscc $iss
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup encerrou com codigo $LASTEXITCODE"
}
if (-not (Test-Path -LiteralPath $installer)) {
    throw "Instalador nao foi criado: $installer"
}

Get-Item -LiteralPath $installer | Select-Object FullName, Length, LastWriteTime
Get-FileHash -LiteralPath $installer -Algorithm SHA256 | Select-Object Algorithm, Hash, Path
