# Movaura 0.9.0

Desenvolvido por Guilherme Loscher (GL).

## Beta privado

O Movaura tem ativacao beta opcional via Supabase, com chaves unicas vinculadas
ao primeiro computador ativado. O passo a passo esta em
`docs/SUPABASE_BETA.md`, e as chaves podem ser geradas com:

```powershell
python scripts\generate_beta_keys.py --count 100
```

## Atualizacao comercial desta rodada

- Assistente inteligente de desempenho: monitora CPU/RAM, reduz FPS em degraus e pode aplicar perfil Leve automaticamente quando o consumo fica alto.
- Importacao inteligente: videos, GIFs e imagens recebem classificacao `Leve`, `Medio` ou `Pesado`, tags tecnicas e aviso de otimizacao quando necessario.
- Biblioteca com filtros por consumo (`Leves`, `Medios`, `Pesados`) e `4K`.
- FFmpeg trocado para build LGPL compartilhado, sem `--enable-gpl` e sem `--enable-nonfree` na configuracao reportada.
- Pasta `licenses/ffmpeg` incluida no projeto e no build para documentar origem, licenca e fonte do FFmpeg usado.
- Checagem `scripts/check_commercial_readiness.py` valida o FFmpeg real por `ffmpeg.exe -version`.
- Fluxo MSIX criado em `scripts/build_msix_package.ps1`.
- Fluxo Windows App Certification Kit criado em `scripts/run_wack.ps1`.
- O pacote MSIX local mais recente passou no WACK com `OVERALL_RESULT="PASS"`.

## Novidades da versão 0.9.0

- Painel inicial mais comercial, com resumo simples, recomendação de desempenho, catálogo, benchmark e autocorreção em um clique.
- Consultor de desempenho amigável para orientar usuários comuns sem expor detalhes técnicos.
- Editor de cenas com modelos rápidos: cena leve, áudio, partículas, chuva e vídeo limpo.
- Catálogo local inicial em `data/catalog.json`, pronto para migrar para um catálogo online.
- Atualizador com download verificado por SHA-256 quando houver manifesto configurado.
- Otimizador automático de vídeos pesados: cria uma cópia em cache para reduzir CPU/RAM sem alterar o arquivo original.
- FFmpeg incluído como ferramenta de otimização local quando o instalador é gerado com `tools/ffmpeg/bin/ffmpeg.exe`; licença e README ficam em `tools/ffmpeg`.
- Opção `Otimizar vídeos pesados automaticamente` na aba `Desempenho`.
- Correção de uma tentativa de seek agressivo que podia aumentar o custo de decodificação em MP4.
- Editor multicamadas reordenável com visibilidade, opacidade, escala, posição e mistura por camada.
- Presets pessoais de cena com carregar, salvar, duplicar e excluir.
- Novos efeitos nativos leves: partículas, chuva, neblina, brilho e vinheta.
- Biblioteca com tags, coleções, localização de arquivos ausentes e importação recursiva de pastas.
- Miniaturas assíncronas reais e metadados técnicos para vídeos importados.
- Pacotes `.movaura` exportados com capa automática quando uma miniatura estiver disponível.
- Relatórios automáticos para falhas inesperadas e logs rotativos.
- Benchmark integrado de 30 segundos com sugestão de perfil de desempenho.

## Novidades da versão 0.8.0

- Perfil adaptativo evoluído: usa média móvel de CPU, reduz consumo em degraus e restaura qualidade após estabilização.
- Diagnóstico ao vivo com CPU atual, média, pico, RAM atual e RAM média.
- Pausa automática quando o Windows está bloqueado, com retomada ao desbloquear.
- Editor de cenas com intensidade e velocidade independentes para os efeitos nativos.
- Pré-visualização da cena diretamente a partir do editor antes de aplicar.
- Pacotes `.movaura` preservam intensidade e velocidade dos efeitos.
- Biblioteca com filtro `Recentes` e ordenação por nome, uso recente ou favoritos.
- Diagnóstico exportado e autoteste registram os adaptadores gráficos ativos.
- Mensagens de inicialização mais simples, com indicação clara para exportar diagnóstico.

## Novidades da versão 0.7.1

- Painel inicial mais direto, com seletor visual de monitor, estado atual e botão para fechar a pré-visualização.
- Pré-visualização integrada com mensagens simples quando um wallpaper não puder ser aberto.
- Parallax real por camadas: imagem, GIF ou vídeo escolhido agora acompanha suavemente a posição do cursor.
- Correção do parallax para ambientes com monitores posicionados à esquerda ou acima da tela principal.
- Suporte completo a WebP na biblioteca, no editor e nos pacotes compartilháveis `.movaura`.
- Importação de cenas mais segura: pacotes inválidos são rejeitados e removidos sem deixar resíduos.
- Servidor de atualizações configurável diretamente na aba `Suporte`, com validação mais rígida de URL e SHA-256.
- Novo script `scripts/run_product_smoke_tests.py` para verificar painel, biblioteca, perfis, cenas, atualizações e resoluções antes de cada instalador.

## Novidades da versão 0.7.0

- Painel inicial completo com resumo do wallpaper, tela escolhida e consumo do compositor.
- Fluxo guiado com biblioteca, criação rápida, pré-visualização, aplicar, pausar e parar.
- Biblioteca visual com busca, filtros, favoritos, importação por arrastar e capas melhores para vídeos.
- Editor de cenas por camadas com fundo, efeito, áudio e ajustes de fluidez.
- Importação e exportação de cenas compartilháveis no formato `.movaura`.
- Perfis de desempenho simplificados: `Recomendado`, `Leve` e `Máxima qualidade`.
- Opção de inicialização automática durante a instalação.
- Matriz de testes documentada para validação comercial em diferentes GPUs e escalas do Windows.

## Novidades da versão 0.6.2

- Nova aba `Início` com os caminhos mais comuns para usuários iniciantes.
- Novo assistente `Criar wallpaper com efeitos` para montar cenas com mídia, movimento suave ou visualizador de áudio.
- Novo perfil de desempenho `Adaptativo`, que reduz o FPS da sessão quando o compositor começa a pesar.
- Validação automatizada de geometria em resoluções HD, Full HD, QHD, 4K, ultrawide e múltiplos monitores.

## Desempenho de vídeo

O compositor solicita aceleração por hardware do Media Foundation quando ela
está disponível. Consulte `docs/matriz-de-testes.md` antes de publicar uma
versão comercial em novas combinações de Windows e GPU.

## Novidades da versão 0.6.1

- O visualizador de áudio agora funciona como efeito sobreposto ao wallpaper escolhido.
- Imagens, GIFs e vídeos podem ser usados como fundo do visualizador.
- O editor mostra explicitamente o campo `Wallpaper de fundo`.

## Novidades da versão 0.6.0

- Diagnóstico ao vivo de processos, CPU e memória na aba `Desempenho`.
- Wallpapers independentes por monitor com seleção visual na aba `Wallpaper`.
- O modo global continua usando somente um compositor compartilhado.
- Biblioteca visual aceita importação por arrastar e soltar.
- Editor básico inclui `Parallax suave` e `Visualizador de áudio`.
- O visualizador usa o pico real da saída de áudio do Windows via WASAPI.
- Estrutura do catálogo online documentada com downloads verificados por SHA-256.

## Novidades da versão 0.5.1

- `Repetir em cada monitor` agora usa um único compositor nativo compartilhado.
- O vídeo é decodificado somente uma vez e desenhado por inteiro em cada tela.
- `Panorâmico entre monitores` continua disponível e também usa somente um compositor.

## Novidades da versão 0.5.0

- Nova opção `Vários monitores` na aba `Wallpaper`.
- `Repetir em cada monitor` exibe o wallpaper completo em cada tela.
- `Panorâmico entre monitores` estende o wallpaper pelas telas e usa um único compositor.

## Novidades da versão 0.4.9

- Compatibilidade restaurada para codecs que recusam redimensionamento durante a inicialização.
- O limite de resolução passa a ser solicitado somente para vídeos acima de `1920x1080`.
- Quando o driver rejeita a otimização, o compositor retorna automaticamente ao tamanho original.

## Novidades da versão 0.4.8

- Atualizações encerram o painel e os compositores antigos antes de substituir arquivos.
- O primeiro lançamento remove compositores órfãos deixados por versões anteriores.
- A atualização para o compositor compartilhado passa a funcionar mesmo com o Movaura antigo aberto.

## Novidades da versão 0.4.7

- O modo `Todos` usa uma única superfície virtual para múltiplos monitores.
- Um mesmo vídeo não é mais decodificado separadamente em cada tela.
- Vídeos acima de `1920x1080` são reduzidos durante a decodificação para evitar desperdício de CPU e RAM.
- A recuperação automática acompanha corretamente o novo compositor compartilhado.

## Novidades da versão 0.4.6

- Fila de vídeo nativa reduzida de oito para três frames por monitor.
- Buffers RGB reaproveitados para diminuir alocações e consumo de memória.
- Decodificação roda com prioridade reduzida para manter a área de trabalho responsiva.

## Novidades da versão 0.4.5

- Decodificação MP4/WebM movida para uma fila assíncrona dedicada.
- O compositor redesenha somente quando um novo frame está disponível.
- Atualizar um wallpaper animado não desmonta mais toda a engine.
- Inicialização normal evita repetir o diagnóstico completo do Explorer.

## Novidades da versão 0.4.4

- Vídeos MP4/WebM agora retornam ao início sem rajadas de decodificação.
- A superfície da área de trabalho só aparece após o primeiro frame estar pronto.
- Playlists ativas não reiniciam mais o compositor logo após a inicialização.
- Temporizador nativo ajustado para animações mais fluidas.

## Novidades da versão 0.4.3

- A playlist ativa agora aparece na aba `Wallpaper`.
- Salvar uma playlist sincroniza seu primeiro item válido com a aba `Wallpaper`.
- O avanço automático da playlist atualiza o formulário em tempo real.
- Identidade de autoria GL adicionada ao software, instalador e código principal.

## Novidades da versão 0.4.2

- A geometria de cada monitor agora vem diretamente do Win32 em pixels físicos.
- Monitores secundários com escala de DPI diferente passam a receber uma superfície fullscreen correta.
- O compositor nativo declara suporte a DPI por monitor antes de criar janelas.

## Novidades da versão 0.4.1

- Vídeos, GIFs e imagens animadas agora usam preenchimento `cover`: ocupam toda a tela preservando a proporção e recortando somente o excedente.
- A janela nativa da área de trabalho animada nasce sem moldura para preencher corretamente o monitor.

## Novidades da versão 0.4.0

- Biblioteca visual com miniaturas, busca, filtros e favoritos.
- Importação de imagens, GIFs, MP4 e WebM para uma biblioteca pessoal.
- Perfis de desempenho: Economia, Equilibrado e Qualidade.
- Consulta manual de atualização por manifesto verificável.
- Diagnóstico ampliado com estatísticas da biblioteca.
- Playlists com avanço automático e duração configurável por item.
- Regras para pausar animações conforme o aplicativo em primeiro plano.
- Atalhos globais: `Ctrl+Alt+P` pausa, `Ctrl+Alt+N` avança e `Ctrl+Alt+R` reinicia.
- Integração opcional com o protetor de tela do Windows.
- Editor básico de cenas leves com cor sólida ou pulso animado.
- Catálogo online conectável por manifesto JSON e telemetria opcional desativada por padrão.

Movaura é uma base profissional para wallpapers no Windows 11, construída
com Python, PySide6, Win32 e um compositor nativo em C++.

## Estado da versão

A versão `0.9.0` está consolidada com três caminhos seguros:

- `Papel de parede`: aplica cor ou imagem como wallpaper real do Windows.
- `Área de trabalho animada`: executa vídeo, GIF e efeitos atrás dos ícones.
- `Pré-visualização animada`: executa vídeo, GIF e efeitos no compositor nativo.

Em versões recentes do Windows 11, o Explorer pode usar a topologia de desktop
elevado: `Progman` sem redirecionamento de bitmap, `SHELLDLL_DefView` em camada
transparente e um `WorkerW` filho no fundo. O compositor nativo detecta essa
estrutura e insere uma janela própria entre a camada de ícones e o fundo sem
mover janelas pertencentes ao Explorer.

## Como usar

Para uso normal:

1. Execute `Movaura-Setup-0.9.0.exe`.
2. Conclua o assistente de instalação.
3. Abra `Movaura` pelo menu Iniciar ou pelo atalho opcional da área de trabalho.

O instalador inclui Python, PySide6 e os componentes nativos necessários. Não é
necessário instalar Python separadamente. No painel:

1. Escolha o modo.
2. Escolha o renderizador.
3. Se necessário, selecione o arquivo com `Procurar`.
4. Clique em `Iniciar`.

O botão `Parar` interrompe a apresentação ativa. O botão `Sair` encerra o
Movaura completamente.

## Automação e criação

- Use `Gerenciar playlists` para adicionar arquivos e definir quantos segundos cada item permanece ativo.
- Use `Regras por aplicativo` para selecionar jogos ou programas que devem pausar a animação.
- Use `Editor básico de cenas` para criar uma cena leve com cor sólida ou pulso animado.
- Use `Ativar como protetor de tela` após instalar o aplicativo.
- Use `Catálogo online` quando houver um manifesto publicado no servidor do produto.

O catálogo utiliza o formato documentado em `docs/catalog-manifest.example.json`.
Nenhum dado de telemetria é gravado ou enviado enquanto a opção correspondente
permanecer desativada.

## Biblioteca incluída

O instalador inclui uma biblioteca original com 20 imagens, 20 GIFs animados e
20 vídeos MP4. Use `Abrir biblioteca` no painel para acessar os arquivos e
selecione qualquer mídia pelo botão `Procurar`.

Quando uma apresentação animada estiver ativa, fechar o painel pelo `X`
mantém o Movaura na bandeja do sistema. Use `Abrir painel` no menu da bandeja
ou clique duas vezes no ícone para restaurar a janela.

## Recursos concluídos

- Painel PySide6 em português.
- Papel de parede estático seguro com cor ou imagem.
- Restauração do wallpaper anterior e da posição da imagem.
- Renderização nativa de vídeo MP4/WebM, GIF, imagem, cor e efeito pulsante.
- Área de trabalho animada real atrás dos ícones no Windows 11 compatível.
- Superfície animada independente para cada monitor selecionado.
- Pré-visualização nativa por monitor.
- Perfis persistentes e perfis pessoais.
- Inicialização opcional com o Windows sem privilégios administrativos.
- Restauração automática da área de trabalho animada ao iniciar com o Windows.
- Bandeja com abrir painel, pausar, continuar, reiniciar e sair.
- Pausa automática durante aplicativos em tela cheia.
- Redução automática para até 15 FPS quando o notebook usa bateria.
- Restauração do FPS configurado ao reconectar a tomada.
- Recuperação automática limitada se o compositor nativo encerrar sozinho.
- Detecção de falhas parciais em múltiplos monitores.
- Bloqueio de instâncias duplicadas.
- Logs persistentes com rotação.
- Exportação de diagnóstico em um clique.
- Gravação atômica de configurações, perfis e estado de restauração.
- Sistema modular de plugins.

## Diagnóstico

Em uma instalação normal, os logs ficam em:

```text
%LOCALAPPDATA%\Movaura\logs\movaura.log
```

Use `Abrir logs` no painel para abrir a pasta. Use `Exportar diagnóstico` para
gerar um relatório completo em:

```text
%LOCALAPPDATA%\Movaura\support
```

O relatório reúne configurações, diagnóstico do Explorer, estado do host
nativo e o trecho final do log.

## Instalação para desenvolvimento

```powershell
cd <pasta-do-projeto>\Movaura
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py --control-panel
```

Os arquivos `.cmd` são mantidos apenas para desenvolvimento a partir do
código-fonte.

## Estrutura principal

```text
app.py
core/
  engine.py
  settings.py
  profile_manager.py
  system_wallpaper.py
  desktop_probe.py
  desktop_host.py
  native_compositor.py
  fullscreen_detector.py
  power_status.py
  app_logging.py
  support_report.py
  presentation_validator.py
ui/
  control_panel.py
renderers/
plugins/
native_compositor_app/
native_host/
native_host_app/
```

## Testes rápidos

Abrir o painel:

```powershell
python app.py --control-panel
```

Aplicar cor estática segura:

```powershell
python app.py --renderer color --color "#0078ff" --mode system-wallpaper
```

Restaurar wallpaper anterior:

```powershell
python app.py --restore-system-wallpaper
```

Abrir pré-visualização nativa de vídeo:

```powershell
python app.py --mode native-composition --renderer video --file "C:\Wallpapers\loop.mp4"
```

Aplicar vídeo animado atrás dos ícones pelo painel:

```text
Modo: Área de trabalho animada
Renderizador: vídeo
Arquivo de mídia: C:\Wallpapers\loop.mp4
```

Diagnóstico da DLL nativa:

```powershell
python app.py --native-diagnose
```

## Modos laboratoriais

Os modos abaixo servem apenas para investigação técnica:

```powershell
python app.py --renderer color --mode workerw --diagnose
python app.py --renderer color --mode native-workerw --diagnose
python app.py --renderer color --mode native-progman-stack --screen 0 --diagnose
python app.py --renderer color --mode defview-transparent-icons --screen 0 --diagnose
python app.py --renderer color --mode desktop-overlay --screen 0 --diagnose
python app.py --reset-experimental-host
```

Não use modos overlay ou experimentais no uso cotidiano. Eles permanecem
isolados para proteger ícones, barra de tarefas e janelas normais.

O modo oficial `Área de trabalho animada` usa `desktop-live` internamente.
Ele não move a lista de ícones do Explorer. Os modos laboratoriais antigos
continuam isolados e não devem ser usados no fluxo normal.

## Próxima fronteira técnica

O próximo marco é ampliar a validação da área de trabalho animada com múltiplos
monitores conectados simultaneamente. O compositor nativo já está separado da
camada de apresentação para permitir essa evolução e uma migração gradual para
C++/Qt.

Veja também [docs/architecture.md](docs/architecture.md).
