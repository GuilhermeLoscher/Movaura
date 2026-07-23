# Arquitetura do Movaura

## Separação principal

Movaura separa renderização de apresentação:

- renderizadores produzem cor, imagem, GIF, vídeo ou efeitos;
- backends de apresentação decidem onde mostrar esse conteúdo com segurança;
- o diagnóstico do Explorer informa capacidades sem transformar
  silenciosamente o wallpaper em uma janela sobreposta.

## Backends

### `system-wallpaper`

Usa APIs do Windows para aplicar uma cor gerada ou imagem estática. Explorer
continua responsável por ícones, cliques e barra de tarefas.

### `native-composition`

Executa `native_compositor_app`, escrito em C++, como processo filho da engine
Python. O compositor usa D3D11, DirectComposition, Direct2D, WIC e Media
Foundation. Ele suporta cor, imagem, GIF e vídeo com uma superfície
independente por monitor.

No modo `desktop-live`, o compositor reconhece o desktop elevado do Windows 11.
Ele cria sua própria janela filha `WS_EX_LAYERED` sob `Progman`, posiciona essa
janela imediatamente abaixo da `SHELLDLL_DefView` e mantém o `WorkerW` no fundo.
As janelas dos ícones não são movidas.

### `window-host`

Mantém as integrações clássicas de `WorkerW` e `Progman` para diagnóstico.
Essas APIs do Explorer não são documentadas e só podem ser promovidas quando
a topologia encontrada for visualmente segura.

## Regra de segurança

- o modo automático nunca usa overlay como fallback;
- janelas de ícones do Explorer não são movidas em produção;
- testes invasivos ficam restritos aos probes laboratoriais;
- superfícies laboratoriais não são persistidas como padrão;
- `desktop-live` só é iniciado quando a topologia elevada esperada existe.

## Topologia observada

Nesta máquina, o Explorer fornece um `WorkerW` aninhado sob `Progman` e uma
`SHELLDLL_DefView` transparente acima dele. A superfície nativa própria é
inserida entre essas camadas e foi validada visualmente atrás dos ícones.

## Evolução

A engine Python conserva configurações, perfis, bandeja, políticas de energia,
logs e plugins. Partes críticas podem migrar gradualmente para C++/Qt sem
alterar esses contratos. A próxima validação deve cobrir múltiplos monitores
conectados simultaneamente e recuperação após reinicializações do Explorer.
