# Movaura CI validation report

Date: 2026-07-23

## Scope

This document describes the CI validation flow prepared on branch `migration/pyside6`.

## Workflow

- File: `.github/workflows/windows-build.yml`
- Triggers:
  - `pull_request` to `main`
  - `workflow_dispatch`
  - `push` to `main`
  - `push` to `migration/pyside6` while this migration/audit branch is active

## Dependency pinning

- Runtime dependencies: `requirements.txt`
- Build dependencies: `requirements-build.txt`

Build dependencies are pinned with exact versions. Hash-pinned install is not yet enabled.

## Jobs and commands

- Checkout source.
- Set up Python 3.12.
- Install build dependencies from `requirements-build.txt`.
- Compile Python sources.
- Run AI generation tests.
- Run product smoke tests.
- Run product self-test.
- Run Qt binding residue checker with JSON/TXT report output.
- Build standalone.
- Run standalone self-test.
- Check standalone artifact for Qt binding residue.
- Build unsigned MSIX.
- Generate package checksums.
- Upload standalone artifact.
- Upload unsigned MSIX artifact.
- Upload validation reports.

## Artifacts

Expected CI artifacts:

- `Movaura-standalone-windows`
- `Movaura-msix-unsigned`
- `Movaura-validation-reports`

Expected reports:

- `release/reports/qt-binding-audit.json`
- `release/reports/qt-binding-audit.txt`
- `release/reports/standalone-file-inventory.csv`
- `release/reports/standalone-file-inventory.json`
- `release/reports/standalone-sha256.txt`
- `release/reports/standalone-sbom.json`
- `release/reports/msix-validation.txt`
- `release/reports/msix-validation.json`
- `release/reports/msix-file-inventory.csv`
- `release/reports/msix-file-inventory.json`
- `release/reports/msix-sha256.txt`
- `release/reports/msix-sbom.json`
- `release/reports/msix-package-sha256.txt`

## Current status

Local workflow edits are prepared. Local standalone/MSIX/WACK validation passed after the final audit changes.

GitHub-hosted CI result is not yet known until the branch is pushed and the workflow runs.

Status before GitHub Actions verification: `READY FOR CI REVIEW`, not Store-ready.

The local package is ready for the Partner Center identity step only after GitHub Actions is green and CI artifacts are reviewed.
