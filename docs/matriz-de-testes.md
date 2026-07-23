# Matriz de testes do Movaura

Use esta lista antes de publicar uma versão comercial em novas máquinas.

## Cobertura automatizada local

- HD: 1366x768.
- Full HD: 1920x1080.
- QHD: 2560x1440.
- 4K: 3840x2160.
- Ultrawide: 3440x1440.
- Dois monitores com coordenadas negativas.
- Imagem, GIF, vídeo e visualizador de áudio.
- Inicialização do painel standalone sem Python.

## Validação manual recomendada

Execute o instalador em pelo menos uma máquina de cada grupo:

- Windows 11 com vídeo integrado Intel.
- Windows 11 com GPU AMD.
- Windows 11 com GPU NVIDIA.
- Notebook usando bateria e tomada.
- Dois monitores com resoluções diferentes.
- Escala de tela do Windows em 100%, 125% e 150%.

Em cada máquina, confirme:

1. Instalação e desinstalação.
2. Inicialização automática opcional.
3. Aplicar, pausar, continuar e parar.
4. Pré-visualização de imagem, GIF e vídeo.
5. Reprodução contínua de vídeo durante cinco minutos.
6. Pausa automática ao abrir um aplicativo em tela cheia.
7. Consumo exibido na aba inicial.
8. Importação e exportação de uma cena `.movaura`.

## Vídeo

O compositor solicita transformações de hardware do Media Foundation quando
disponíveis. O Windows pode usar decodificação por hardware ou retornar ao
processamento compatível com a máquina.
