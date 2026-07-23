param(
    [Parameter(Mandatory = $true)]
    [string]$PackagePath,
    [string]$CertificateThumbprint = "",
    [string]$PfxPath = "",
    [string]$TimestampUrl = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $PackagePath)) {
    throw "Pacote MSIX nao encontrado: $PackagePath"
}
if (-not $CertificateThumbprint -and -not $PfxPath) {
    throw "Informe -CertificateThumbprint ou -PfxPath. Nao coloque senhas no script."
}
if ($PfxPath -and -not (Test-Path -LiteralPath $PfxPath)) {
    throw "Certificado PFX nao encontrado: $PfxPath"
}

$candidates = @(
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe",
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"
)
$signtool = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $signtool) {
    $command = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if ($command) { $signtool = $command.Source }
}
if (-not $signtool) {
    throw "signtool.exe nao encontrado. Instale Windows SDK."
}

$args = @("sign", "/fd", "SHA256", "/tr", $TimestampUrl, "/td", "SHA256")
if ($CertificateThumbprint) {
    $args += @("/sha1", $CertificateThumbprint)
} else {
    $args += @("/f", $PfxPath)
}
$args += $PackagePath

& $signtool @args
if ($LASTEXITCODE -ne 0) {
    throw "signtool encerrou com codigo $LASTEXITCODE"
}

& $signtool verify /pa /v $PackagePath
if ($LASTEXITCODE -ne 0) {
    throw "verificacao da assinatura falhou com codigo $LASTEXITCODE"
}

Write-Host "MSIX assinado e verificado: $PackagePath"
