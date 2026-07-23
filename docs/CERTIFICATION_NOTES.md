# Notas de certificacao - Movaura

## Resumo tecnico
Movaura e um aplicativo Win32 empacotado para Windows Desktop. Ele renderiza wallpapers animados por um compositor nativo local e oferece interface grafica em portugues para escolher, pre-visualizar, otimizar e aplicar wallpapers.

## Comportamento esperado
- O app pode iniciar um processo auxiliar chamado `movaura_native_compositor.exe`.
- Esse processo e encerrado quando o usuario para o wallpaper ou fecha o aplicativo.
- O app pode criar cache local de miniaturas e videos otimizados em `%LOCALAPPDATA%\Movaura`.
- O app pode registrar inicializacao com o Windows somente quando o usuario ativa essa opcao.

## Segurança e privacidade
- Nao ha coleta automatica de dados pessoais.
- Diagnosticos sao gerados localmente e apenas mediante acao do usuario.
- O usuario pode parar o wallpaper e restaurar o wallpaper anterior pelo painel.

## Dependencia FFmpeg
FFmpeg e usado somente para otimizacao opcional de videos. Para builds comerciais fechados, o pacote deve incluir FFmpeg LGPL limpo, sem `--enable-gpl` e sem `--enable-nonfree`, com licencas em `licenses/ffmpeg`.

## Testes recomendados antes de enviar
1. Rodar `python app.py --self-test`.
2. Rodar `scripts/run_product_smoke_tests.py`.
3. Gerar o instalador final.
4. Gerar o MSIX com `scripts/build_msix_package.ps1`.
5. Rodar o Windows App Certification Kit com `scripts/run_wack.ps1`.
6. Testar aplicar, pausar, parar, restaurar, biblioteca, editor por camadas, otimizador e suporte.

## Resultado local mais recente
Em 12 de junho de 2026, o MSIX `release/msix/Movaura-0.9.0.0.msix` passou no Windows App Certification Kit com `OVERALL_RESULT="PASS"`.

O relatorio ainda pode listar mensagens opcionais sobre referencias a criacao de processo em bibliotecas de terceiros como PyQt, Python e FFmpeg. No teste local, essas mensagens nao impediram o resultado geral PASS.

## Limitacoes conhecidas a declarar se necessario
O comportamento de wallpaper animado depende do Windows Desktop Window Manager, GPU, drivers graficos e politicas do Windows Explorer. Em maquinas com drivers antigos, o usuario pode usar o perfil Leve para reduzir FPS e consumo.
