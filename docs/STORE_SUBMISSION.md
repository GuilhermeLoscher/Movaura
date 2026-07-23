# Movaura - Checklist de submissao Microsoft Store

## Status tecnico atual

- Standalone gerado em `dist/standalone/Movaura`.
- MSIX nao assinado gerado em `release/msix/Movaura-0.9.0.0.msix`.
- Validacao estrutural por `makeappx unpack`: aprovada.
- Windows App Certification Kit executado em 23 de julho de 2026 com `OVERALL_RESULT="PASS"`.
- O WACK pode listar um `FAIL` opcional em "Executaveis bloqueados" por referencias de criacao de processo em Python, Qt e FFmpeg; no relatorio local ele aparece com `OPTIONAL="TRUE"` e nao altera o resultado geral PASS.
- Assinatura digital ainda precisa usar os dados/certificado reais do Partner Center antes da instalacao/distribuicao final.

## Descricao curta sugerida

Movaura transforma videos, imagens, GIFs e cenas com efeitos em wallpapers vivos para Windows, com perfis de desempenho, biblioteca local, criacao assistida e controle simples para usuarios iniciantes.

## Descricao longa sugerida

Movaura e um aplicativo de live wallpaper para Windows focado em fluidez, baixo consumo e facilidade de uso. Escolha um wallpaper da biblioteca, importe seus proprios videos, imagens ou GIFs, crie cenas com camadas e efeitos, ajuste o perfil de desempenho e aplique na area de trabalho com poucos cliques.

O app inclui monitoramento de desempenho, perfis Leve/Recomendado/Maxima qualidade, otimizacao de videos com FFmpeg LGPL quando disponivel, suporte a multiplos monitores, pacotes de cena `.movaura`, controle de inicializacao e recuperacao automatica do compositor.

## Aviso funcional para certificacao

O Movaura usa compositor nativo e APIs de desktop do Windows para apresentar wallpapers animados. Em algumas configuracoes do Windows 11, o app usa uma janela/composicao segura e isolada quando o host de area de trabalho do Explorer nao permite renderizacao direta abaixo dos icones. O usuario pode pausar, parar ou restaurar o wallpaper pelo painel principal.

O pacote MSIX declara somente a capability restrita `runFullTrust`, necessaria para executar o app Win32 empacotado e seus auxiliares nativos. Essa capability deve ser justificada nas notas do Partner Center como requisito tecnico para o compositor de wallpaper local.

## Politica de privacidade base

O Movaura processa wallpapers, configuracoes e arquivos importados localmente no computador do usuario. O app nao envia wallpapers pessoais para servidores por padrao. Funcionalidades futuras de catalogo online, ativacao beta ou provedores reais de IA podem se comunicar com servicos externos e devem exibir aviso especifico, URL do provedor e politica de privacidade atualizada.

## FFmpeg

Para distribuicao comercial, usar somente build FFmpeg compativel com LGPL, sem `--enable-gpl` e sem `--enable-nonfree`. Manter no pacote:

- `tools/ffmpeg/LICENSE.txt`
- `tools/ffmpeg/README.txt`
- `licenses/ffmpeg/NOTICE.txt`
- `licenses/ffmpeg/README.txt`
- `licenses/ffmpeg/SOURCE.txt`

## Antes de enviar

1. Assinar `release/msix/Movaura-0.9.0.0.msix` com `scripts/sign_msix.ps1` e certificado real.
2. Instalar o MSIX assinado em uma maquina limpa.
3. Rodar Windows App Certification Kit como administrador e confirmar `OVERALL_RESULT="PASS"` no pacote assinado final.
4. Registrar nas notas de certificacao qualquer resultado opcional do WACK, especialmente "Executaveis bloqueados" opcional causado por runtime Python/Qt/FFmpeg.
5. Testar aplicar, pausar, parar, importar video/imagem/GIF e abrir biblioteca.
6. Capturar screenshots finais da aba Inicio, Biblioteca, Criar com IA, Desempenho e wallpaper aplicado.
7. Conferir identidade `PackageName`, `Publisher`, `PublisherDisplayName` e versao com os dados reservados no Partner Center.
