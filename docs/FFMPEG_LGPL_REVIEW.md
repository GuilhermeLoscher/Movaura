# Revisao FFmpeg LGPL - Movaura

## Build escolhido
Fonte: BtbN/FFmpeg-Builds, artefato `ffmpeg-master-latest-win64-lgpl-shared.zip`.

Motivo: build Windows x64 compartilhado identificado como LGPL, sem x264/x265 e sem opcoes GPL/nonfree na configuracao reportada por `ffmpeg -version`.

## Validacao feita
O comando `ffmpeg.exe -version` deve mostrar:
- ausencia de `--enable-gpl`;
- ausencia de `--enable-nonfree`;
- `--disable-libx264`;
- `--disable-libx265`;
- `--enable-shared`;
- `--disable-static`.

## Observacao juridica
Isto nao substitui revisao juridica profissional. Antes da venda final, mantenha a versao exata, licencas, fonte/link e configuracao dentro de `licenses/ffmpeg`.
