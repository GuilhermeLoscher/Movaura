# Auditoria final Microsoft Store - Movaura

Data: 23 de julho de 2026.
Base auditada: release candidate 0.9.0 / MSIX 0.9.0.0.

## Resultado

- AppxManifest.xml valido para app Win32 empacotado no Windows Desktop.
- Identidade atual: `GuilhermeLoscher.Movaura`.
- Publisher atual: `CN=Guilherme Loscher`.
- Versao MSIX atual: `0.9.0.0`.
- Capability solicitada: somente `runFullTrust`.
- WACK local: `OVERALL_RESULT="PASS"`.
- Contagem WACK local: 23 PASS, 1 FAIL opcional (`Executaveis bloqueados`, `OPTIONAL="TRUE"`).
- Relatorio local gerado em `release/certification/wack-20260723-144550.xml` e ignorado pelo Git por ser artefato de certificacao.

## Correcoes aplicadas nesta auditoria

- O build standalone agora empacota plugins a partir de uma area temporaria limpa, sem `__pycache__`, `.pyc` ou `.pyo`.
- O verificador de atualizacoes passou a aceitar manifestos remotos apenas via HTTPS. Manifestos `file://` continuam permitidos para autotestes locais.
- Downloads de atualizacao passaram a exigir HTTPS antes de qualquer acesso de rede.
- Relatorios WACK locais passaram a ficar ignorados pelo Git.
- Notas de submissao e certificacao foram atualizadas com o estado real do WACK e com a justificativa de `runFullTrust`.

## Itens externos ao codigo

- Assinatura digital final deve usar certificado/identidade reais do Partner Center.
- O pacote final assinado deve passar novamente no WACK antes do envio.
- Screenshots, descricao comercial, classificacao etaria, URL de suporte e URL publica da politica de privacidade devem ser preenchidos no Partner Center.
- Revisao juridica final de FFmpeg/licencas continua recomendada antes da venda.
