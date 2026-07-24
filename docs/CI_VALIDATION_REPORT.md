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

GitHub Actions passed on pull request `#1` after the final CI fixes.

Validated commit:

```text
70f6ec901e5b19ca9414f37da5dce64595d1c384
```

Workflow results:

- `Movaura AI Generation` run `30044657837`: `success`
- `Movaura Windows Build` run `30044657907`: `success`

The Windows build completed all required steps:

- Compile Python sources.
- Check text encoding.
- Run AI generation tests.
- Run product smoke tests.
- Run product self-test.
- Check Qt binding source residue.
- Build standalone.
- Run standalone self-test.
- Check standalone artifact Qt binding residue.
- Build unsigned MSIX.
- Generate package checksums.
- Upload standalone, MSIX and validation report artifacts.

Published CI artifacts:

- `Movaura-standalone-windows`
- `Movaura-msix-unsigned`
- `Movaura-validation-reports`

Status after GitHub Actions verification: `CI PASSED`.

The package remains ready for the Partner Center identity/signing/publication step. Store submission still requires the reserved Microsoft Store identity, final signing, Partner Center metadata and final WACK execution against the signed package.
