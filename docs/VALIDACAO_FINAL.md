# Validacao final do Movaura 0.9.0

Este documento resume o fluxo atual de validacao. O caminho comercial oficial
usa a pasta `release`, nao a pasta antiga `dist`.

## Build recomendado

1. `scripts\build_fixed_release.ps1`
2. `scripts\build_installer.ps1`
3. `scripts\build_msix_package.ps1`
4. `scripts\run_wack.ps1`
5. `scripts\check_commercial_readiness.py`

## Artefatos esperados

- `release\standalone-commercial\Movaura\Movaura.exe`
- `release\installer\Movaura-Setup-0.9.0.exe`
- `release\msix\Movaura-0.9.0.0.msix`
- `release\certification\*.xml`

## Testes mínimos

```powershell
<python-da-build>\python.exe -m compileall -q app.py core renderers ui plugins scripts
<python-da-build>\python.exe scripts\run_product_smoke_tests.py
<python-da-build>\python.exe app.py --self-test
<python-da-build>\python.exe scripts\check_commercial_readiness.py
```

## Observacoes

- O FFmpeg comercial fica em `tools\ffmpeg\bin\ffmpeg.exe` e deve continuar
  LGPL, sem GPL/nonfree na configuracao reportada.
- O Windows App Certification Kit deve retornar `OVERALL_RESULT="PASS"` antes
  do envio ao Partner Center.
- Para publicar na Microsoft Store, substitua a identidade provisoria do MSIX
  pelos dados reservados no Partner Center.
