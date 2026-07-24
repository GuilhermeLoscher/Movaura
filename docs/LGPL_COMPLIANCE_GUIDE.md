# LGPL compliance guide for Movaura

Status: `TECHNICAL GUIDANCE - LEGAL REVIEW REQUIRED`

Movaura distributes Qt/PySide6 and FFmpeg components that may rely on LGPL-compatible obligations depending on the final selected binaries.

Technical practices prepared:

- keep Qt/PySide6 DLLs and modules as separate files in the packaged application;
- include notices in `licenses/`;
- include source URLs;
- document component versions;
- do not statically link FFmpeg in the app package;
- block FFmpeg builds with `--enable-gpl`, `--enable-nonfree`, `--enable-libx264` or `--enable-libx265`;
- preserve the ability to replace LGPL-covered DLLs where technically feasible.

Final release requirements still pending:

- include full license texts, not only summaries;
- verify exact Qt modules shipped in final MSIX;
- verify no GPL-only Qt module is included unintentionally;
- lock FFmpeg to an immutable source/build package;
- provide source-code offer or source links as required by the selected licenses;
- obtain professional legal review.

Use this statement in release evidence:

`Conformidade tecnica preparada; revisao juridica profissional recomendada.`
