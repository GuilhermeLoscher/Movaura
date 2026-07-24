# Movaura - relatorio de migracao PySide6

Data: 2026-07-23

Branch: `migration/pyside6`

Base antes da migracao: `81f91e2491abe4f5d26ad75f11bd496caf7c3f59`

## Escopo

- Migrar o binding Qt do Movaura de PyQt6 para PySide6.
- Preservar comportamento, arquitetura, modulo de IA mock, licenciamento, Supabase e fluxo de build.
- Nao alterar `C:\NovaWall\Movaura Beta`.
- Nao integrar API real de IA.
- Nao adicionar telemetria, coleta de dados ou segredos.

## Commits da migracao

- `3b7196e` - Inventory Qt usage for PySide6 migration
- `a023076` - Migrate Qt bindings to PySide6
- `67f8b4f` - Add PySide6 residue checks
- `bcf5efa` - Document PySide6 third-party licensing

## Inventario original

O inventario original foi registrado antes da migracao em:

- `docs/PYSIDE6_MIGRATION_INVENTORY.md`

Resumo:

- 236 ocorrencias relacionadas a Qt/PyQt6 inventariadas.
- 29 arquivos Python/configuracao com uso de Qt/PyQt6.
- Areas de maior risco identificadas: fila de IA, pagina de IA, cache de miniaturas, video renderer, tray e painel principal.

## Alteracoes tecnicas

- `requirements.txt` trocado de PyQt6 para `PySide6==6.10.0`.
- Imports de `PyQt6` migrados para `PySide6`.
- `pyqtSignal` migrado para `Signal`.
- Nao havia `pyqtSlot` ou `pyqtProperty` em codigo de producao.
- Scripts de smoke test atualizados para PySide6.
- Build standalone e GitHub Actions ganharam verificacao contra residuos de PyQt/SIP.

## Checagens contra residuos PyQt

Script criado:

- `scripts/check_no_pyqt_artifacts.py`

Tokens bloqueados:

- `PyQt6`
- `PyQt6-Qt6`
- `PyQt6-sip`
- `pyqtSignal`
- `pyqtSlot`
- `pyqtProperty`

Resultado:

- Codigo fonte: `pyqt_artifact_check=ok`
- Pacote MSIX expandido: `pyqt_artifact_check=ok`

Excecoes permitidas:

- `docs/PYSIDE6_MIGRATION_INVENTORY.md`, por ser snapshot historico anterior a migracao.
- `scripts/check_no_pyqt_artifacts.py`, por conter os tokens bloqueados que ele mesmo verifica.

## Dependencias locais

Ambiente local `.build-venv`:

- PySide6 6.10.0 instalado.
- shiboken6 6.10.0 instalado.
- PyQt6, PyQt6-Qt6 e PyQt6-sip removidos.

## Validacoes executadas

- `python -m compileall -q app.py core renderers ui plugins scripts`: aprovado.
- `scripts/run_product_smoke_tests.py`: aprovado.
- `scripts/run_ai_generation_tests.py`: aprovado.
- `python app.py --self-test`: aprovado.
- Build standalone com PyInstaller: aprovado.
- Self-test no standalone: aprovado.
- Self-test em caminho com espacos: aprovado.
- Build MSIX: aprovado.
- Higiene do layout MSIX: aprovado.
- Windows App Certification Kit: `OVERALL_RESULT="PASS"`.

## Artefatos gerados

Standalone:

- `dist/standalone/Movaura/Movaura.exe`
- Tamanho: 2.271.816 bytes
- SHA256: `774C125FC47235940A9F7888E8D6B3736D5BD83B6922FC5465F276BEFA0E44BA`

MSIX:

- `release/msix/Movaura-0.9.0.0.msix`
- Tamanho: 225.394.737 bytes
- SHA256: `97E004A689ECFB1186ABBAE272E79A8A8E7AD25BB69235097EB3F6701427C0BD`

WACK:

- Relatorio: `release/certification/wack-20260723-153122.xml`
- PASS: 23
- FAIL: 1
- FAIL opcional: 1
- Resultado geral: `PASS`

## Observacao do WACK

O unico FAIL e opcional:

- Teste: `Executaveis bloqueados`
- `OPTIONAL="TRUE"`
- Exemplos reportados: referencias em arquivos do Qt/PySide como `opengl32sw.dll`, `qdirect2d.dll` e arquivos de traducao Qt.

Como o resultado geral do WACK e `PASS`, isso nao bloqueia automaticamente o pacote. Deve ser mantido como observacao para submissao na Microsoft Store.

## Manifesto MSIX validado

Resumo do manifesto gerado:

- Identity: `GuilhermeLoscher.Movaura`
- Publisher: `CN=Guilherme Loscher`
- Version: `0.9.0.0`
- Architecture: `x64`
- DisplayName: `Movaura`
- Capability: `runFullTrust`
- TargetDeviceFamily: `Windows.Desktop`
- MinVersion: `10.0.19041.0`
- MaxVersionTested: `10.0.26200.0`

## Licencas e avisos

Arquivos adicionados:

- `docs/THIRD_PARTY_NOTICES.md`
- `licenses/pyside6/*`
- `licenses/qt/*`
- `licenses/shiboken6/*`
- `licenses/python/*`
- `licenses/pywin32/*`

Observacao: esta documentacao e apoio tecnico de conformidade, nao substitui revisao juridica.

## Segredos e dados sensiveis

Busca local nao encontrou chaves reais embutidas, certificados privados ou `service_role`.

Ocorrencias encontradas sao placeholders/documentacao:

- `SUA_ANON_KEY`
- mensagem de erro sobre anon key/RLS

## Movaura Beta

Confirmacao:

- Nenhum arquivo em `C:\NovaWall\Movaura Beta` foi modificado.
- Nenhum arquivo da pasta `Movaura Beta` entrou no MSIX.
- Nenhum symlink ou junction entre projetos foi criado.

## Riscos remanescentes

- O WACK possui 1 FAIL opcional relacionado a bibliotecas Qt/PySide.
- Testes reais ainda devem ser feitos em maquinas diferentes, DPI diferente, GPU diferente e Windows 10/11 antes de publicar amplamente.
- A migracao altera o binding Qt base; apesar dos testes automatizados e WACK aprovarem, recomenda-se smoke test manual do painel, tray, biblioteca, IA mock, aplicacao/parada de wallpaper e build instalado antes do merge.

## Recomendacao

A branch `migration/pyside6` esta pronta para revisao e teste manual final. Recomenda-se fazer merge somente depois de confirmar visualmente os fluxos principais no aplicativo instalado.
