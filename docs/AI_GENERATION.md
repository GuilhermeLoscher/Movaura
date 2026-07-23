# Movaura - Criar com IA

Este modulo implementa a arquitetura inicial de criacao de wallpapers por IA sem
usar APIs reais, chaves, rede ou custos. A primeira versao usa somente o provedor
`mock`, que gera imagens PNG localmente para validar UX, fila, erros, historico e
integracao com a biblioteca.

## Fluxo atual

1. O usuario abre a aba `Criar com IA`.
2. O usuario escreve o prompt, escolhe estilo, resolucao, qualidade e variacoes.
3. A UI melhora o prompt localmente quando a opcao esta ativa.
4. A fila inicia uma thread de geracao, com progresso e cancelamento.
5. O provedor mock gera imagens PNG locais.
6. O storage valida, ajusta para a resolucao final e grava em `data/ai_generation/results`.
7. O historico registra prompt, estilo, resolucao, qualidade, status e arquivos.
8. A imagem pode ser pre-visualizada, aplicada ou salva na biblioteca pessoal.

## Arquivos principais

- `core/ai_generation/models.py`: contratos, estados, erros e resultados.
- `core/ai_generation/prompting.py`: estilos, resolucoes e melhoria local do prompt.
- `core/ai_generation/providers.py`: interface de provedor e `MockImageGenerationProvider`.
- `core/ai_generation/queue.py`: execucao em background com progresso e cancelamento.
- `core/ai_generation/storage.py`: pos-processamento, arquivos finais e historico.
- `ui/ai_generation_page.py`: pagina `Criar com IA` integrada ao painel.
- `scripts/run_ai_generation_tests.py`: autoteste offline do fluxo de IA.

## Simulacao de erros

Na secao avancada da aba `Criar com IA`, o mock pode simular:

- autenticacao recusada;
- limite atingido;
- timeout;
- provedor indisponivel;
- resultado vazio;
- imagem invalida.

Esses cenarios existem para validar mensagens simples ao usuario antes de ligar
provedores reais.

## Caminho para provedores reais

Para adicionar um provedor real, implemente a interface de `ImageGenerationProvider`
em `core/ai_generation/providers.py` ou em um novo arquivo do mesmo pacote. O app
nao deve chamar rede diretamente pela UI. O provedor deve retornar `GenerationResult`
e converter falhas externas para `GenerationError`, usando mensagens simples para o
usuario.

Provedores reais devem usar configuracao segura, limites de custo, timeout,
cancelamento, politica de conteudo, logs sem dados sensiveis e nunca gravar chaves
em texto claro dentro do repositorio.

## Teste

```powershell
C:\NovaWall\.build-venv\Scripts\python.exe scripts\run_ai_generation_tests.py
```

Resultado esperado:

```text
ai_generation_tests=ok
```
