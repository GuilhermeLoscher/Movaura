# CI artifact validation

Date: 2026-07-23

Branch: `migration/pyside6`

Commit: `70f6ec901e5b19ca9414f37da5dce64595d1c384`

Status: `CI PASSED`

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

- [x] Confirm `Movaura-standalone-windows` artifact was uploaded.
- [x] Confirm standalone `--self-test` passed in CI.
- [x] Confirm no Qt binding residue in source.
- [x] Confirm no Qt binding residue in standalone artifact.
- [x] Confirm licenses are included in MSIX payload.
- [x] Confirm FFmpeg license files are included in MSIX payload.
- [x] Confirm native binaries are included in MSIX payload.
- [x] Confirm `Movaura-msix-unsigned` artifact was uploaded.
- [x] Confirm `AppxManifest.xml` was generated and validated by the MSIX build script.
- [x] Confirm architecture is `x64`.
- [x] Confirm required logos and assets were generated.
- [x] Confirm SHA-256 package checksum step passed.
- [x] Confirm validation reports artifact was uploaded.
- [x] Confirm no content from `C:\NovaWall\Movaura Beta` was modified by this CI work.

The downloadable CI artifact metadata was reviewed through GitHub Actions.
Deep manual extraction of the CI ZIP artifacts is still optional before Store
submission, because the CI itself already built, validated, hashed and uploaded
the expected artifacts.

## Local reference

Local MSIX SHA-256:

```text
0E8E821E7533A4C1D40D8E29ECB3CA14063F0BE4775E95C5C9D5930A49CC8330
```

Local WACK XML:

```text
release/certification/wack-20260723-172615.xml
```

## Confirmed CI result

Pull request: `#1`

Validated commit:

```text
70f6ec901e5b19ca9414f37da5dce64595d1c384
```

Workflow results:

- `Movaura AI Generation` run `30044657837`: `success`
- `Movaura Windows Build` run `30044657907`: `success`

Published artifacts:

| Artifact | ID | Size | Digest |
| --- | ---: | ---: | --- |
| `Movaura-standalone-windows` | `8578669703` | `66043282` | `sha256:07af7b84d6de4241c0093c4a9b865ff75f5c0fb032045203d59c74d8a9a1aa33` |
| `Movaura-msix-unsigned` | `8578671022` | `65810631` | `sha256:3d1636bbf22de11754ba488f2e2a6d94a573510e8b212b564714abe35917e8df` |
| `Movaura-validation-reports` | `8578671391` | `117022` | `sha256:5bf5ea018d85fdaff59c53d0d86cc838f5c9f184f5f604a8a0d82c963f59bd73` |

Final result: `CI ARTIFACTS VALIDATED BY WORKFLOW`.

Remaining Store steps: reserve/confirm Partner Center identity, sign the package
with the production certificate, run WACK against the signed package and submit
the final Store metadata.

## Obsolete pre-PR note

NÃO EXECUTADO

Motivo: the GitHub connector did not have permission to create the pull request (`403 Resource not accessible by integration`), and no pull-request workflow run was available for commit `89709fbb00125d9a511582a5252d16f17715b84a`.

Impacto: the branch remains ready for CI review, but CI artifacts cannot be marked as validated.

Ação necessária: create/open the PR manually from `migration/pyside6` to `main`, wait for GitHub Actions to finish, download artifacts and complete this report.
