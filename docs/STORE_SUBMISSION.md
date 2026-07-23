# Movaura - materiais para Microsoft Store

## Nome
Movaura

## Categoria sugerida
Personalization / Personalizacao.

## Descricao curta
Live wallpapers leves para Windows, com videos, imagens, efeitos, audio visualizer e perfis de desempenho.

## Descricao longa
Movaura transforma a area de trabalho do Windows em um wallpaper vivo, com foco em fluidez e baixo consumo. O app permite escolher wallpapers de video, imagem, GIF e cenas com efeitos, aplicar por monitor, otimizar midias pesadas e pausar automaticamente em jogos ou aplicativos em tela cheia.

Recursos principais:
- Wallpapers de video, imagem, GIF e cenas por camadas.
- Perfis Leve, Recomendado e Maxima qualidade.
- Otimizacao inteligente de videos para reduzir CPU e RAM.
- Suporte a multiplos monitores.
- Pausa automatica em tela cheia, bateria ou alto consumo.
- Biblioteca local com busca, favoritos, tags e miniaturas.
- Pacotes .movaura para compartilhar cenas.
- Diagnostico de suporte sem coleta externa automatica.

## Aviso claro sobre funcionamento
Movaura usa um compositor grafico local para desenhar wallpapers animados na area de trabalho. Em algumas configuracoes do Windows Explorer, o app usa uma superficie de composicao propria para preservar estabilidade e desempenho. O usuario pode pausar, parar ou restaurar o wallpaper anterior a qualquer momento.

## Dependencias e componentes de terceiros
O app inclui FFmpeg apenas para otimizacao opcional de videos. A versao comercial deve usar um build LGPL limpo, sem `--enable-gpl` e sem `--enable-nonfree`, com licencas incluidas em `licenses/ffmpeg`.

## Screenshots necessarias
1. Tela inicial com botoes Escolher, Pre-visualizar, Aplicar e Otimizar.
2. Biblioteca com miniaturas, tags e favoritos.
3. Editor por camadas.
4. Aba Desempenho mostrando perfil e consumo.
5. Wallpaper aplicado na area de trabalho.
6. Suporte/diagnostico com mensagem simples.

## Notas para certificacao
Ver `docs/CERTIFICATION_NOTES.md`.
