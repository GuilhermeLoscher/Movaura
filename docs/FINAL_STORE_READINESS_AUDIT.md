# Final Store readiness audit

Status: `READY FOR CI REVIEW`

Movaura is not marked as ready for Microsoft Store submission yet.

## Ready

- Branch: `migration/pyside6`
- PySide6 migration completed.
- Automated local tests passed in current audit pass.
- Build scripts now produce inventories, hashes and simple SBOM files.
- Fresh standalone rebuild passed.
- Fresh MSIX rebuild passed.
- Fresh WACK on the regenerated MSIX passed overall.
- MSIX build has Partner Center identity safeguards.
- runFullTrust justification exists.
- Privacy policy updated for beta activation/licensing.

## Not ready

- Partner Center real identity has not been applied.
- Final Store-signed MSIX has not been generated.
- Manual tests have not been completed.
- FFmpeg source/build lock is partial.
- License package still needs full legal review.

## Final status

`READY FOR CI REVIEW`

This means the local technical package passed, but the branch still needs GitHub Actions CI evidence for the final commit before it can return to `READY FOR PARTNER CENTER IDENTITY`.
