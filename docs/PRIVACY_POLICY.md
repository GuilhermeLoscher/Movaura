# Politica de privacidade - Movaura

Ultima atualizacao: 12 de junho de 2026.

Movaura e um aplicativo de wallpapers animados para Windows desenvolvido por Guilherme Loscher (GL).

## Coleta de dados
O Movaura nao envia automaticamente wallpapers pessoais, historico de uso ou diagnosticos para servidores externos.

Builds com ativacao beta/licenciamento podem enviar ao servidor de ativacao configurado:
- chave beta informada;
- e-mail informado;
- nome informado, quando preenchido;
- identificador tecnico do computador em formato hash;
- data de ativacao.

Esses dados sao usados para validar a chave de acesso e impedir uso duplicado indevido durante testes beta.

## Dados salvos localmente
O aplicativo pode salvar no computador do usuario:
- configuracoes do app;
- favoritos e biblioteca local;
- perfis de desempenho;
- cache de miniaturas;
- copias otimizadas de videos importados;
- relatorios de diagnostico gerados manualmente pelo usuario.

Esses dados ficam armazenados localmente, normalmente em `%LOCALAPPDATA%\Movaura`, e podem ser apagados pelo usuario ao desinstalar ou limpar os dados do aplicativo.

## Diagnosticos
Quando o usuario gera um relatorio de suporte, o arquivo pode conter informacoes tecnicas como versao do Windows, GPU detectada, monitores, caminho do compositor e mensagens de erro. O relatorio so e compartilhado se o proprio usuario enviar o arquivo.

## Internet
O Movaura pode acessar a internet apenas para recursos opcionais ou configurados, como ativacao beta, verificacao de atualizacao ou catalogo online. Wallpapers importados pelo usuario permanecem locais por padrao.

## Terceiros
O Movaura usa FFmpeg para otimizacao opcional de videos. As licencas e avisos ficam na pasta `licenses/ffmpeg`.

Builds beta podem usar Supabase como servidor de ativacao, conforme configuracao do distribuidor.

## Retencao e exclusao
Dados locais ficam no computador do usuario, normalmente em `%LOCALAPPDATA%\Movaura`.

Dados enviados para ativacao beta devem ser removidos ou expirados pelo operador do beta conforme a politica definida para o teste.

## Contato
Suporte: informe o canal oficial definido na pagina da Microsoft Store ou no site do produto.
