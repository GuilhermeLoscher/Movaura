# CI artifact validation

Date: 2026-07-23

Branch: `migration/pyside6`

Commit: `89709fbb00125d9a511582a5252d16f17715b84a`

Status: `PENDING PR CI RUN`

## Required artifacts

The GitHub Actions workflow is expected to upload:

- `Movaura-standalone-windows`
- `Movaura-msix-unsigned`
- `Movaura-validation-reports`

The validation reports artifact is expected to include:

- `standalone-file-inventory.csv`
- `standalone-file-inventory.json`
- `standalone-sha256.txt`
- `standalone-sbom.json`
- `msix-validation.txt`
- `msix-validation.json`
- `msix-file-inventory.csv`
- `msix-file-inventory.json`
- `msix-sha256.txt`
- `msix-sbom.json`
- `msix-package-sha256.txt`
- `qt-binding-audit*.txt`
- `qt-binding-audit*.json`
- `encoding-audit.txt`
- `ffmpeg-audit.txt`
- `ffmpeg-audit.json`

## Validation checklist after CI is green

- [ ] Download `Movaura-standalone-windows`.
- [ ] Confirm `Movaura.exe` exists.
- [ ] Run standalone `--self-test`.
- [ ] Confirm no PyQt residue in the artifact report.
- [ ] Confirm licenses are present.
- [ ] Confirm FFmpeg audit passed.
- [ ] Confirm native binaries exist.
- [ ] Confirm no `.git`, `.env`, PFX, private key, service_role, cache or temporary files.
- [ ] Confirm no content from `C:\NovaWall\Movaura Beta`.
- [ ] Download `Movaura-msix-unsigned`.
- [ ] Confirm `AppxManifest.xml` exists inside the package.
- [ ] Confirm architecture is `x64`.
- [ ] Confirm `runFullTrust` is present.
- [ ] Confirm logos and assets are present.
- [ ] Confirm SHA-256 is calculated.
- [ ] Compare CI structure against local build structure without requiring identical hashes.

## Local reference

Local MSIX SHA-256:

```text
0E8E821E7533A4C1D40D8E29ECB3CA14063F0BE4775E95C5C9D5930A49CC8330
```

Local WACK XML:

```text
release/certification/wack-20260723-172615.xml
```

## Current result

NÃO EXECUTADO

Motivo: the GitHub connector did not have permission to create the pull request (`403 Resource not accessible by integration`), and no pull-request workflow run was available for commit `89709fbb00125d9a511582a5252d16f17715b84a`.

Impacto: the branch remains ready for CI review, but CI artifacts cannot be marked as validated.

Ação necessária: create/open the PR manually from `migration/pyside6` to `main`, wait for GitHub Actions to finish, download artifacts and complete this report.
