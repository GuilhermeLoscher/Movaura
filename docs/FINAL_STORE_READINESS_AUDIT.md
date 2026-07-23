# Final Store readiness audit

Status: `READY FOR CI REVIEW`

Movaura is not marked as ready for Microsoft Store submission yet.

## Ready

- Branch: `migration/pyside6`
- PySide6 migration completed.
- Automated local tests passed in current audit pass.
- Build scripts now produce inventories, hashes and simple SBOM files.
- MSIX build has Partner Center identity safeguards.
- runFullTrust justification exists.
- Privacy policy updated for beta activation/licensing.

## Not ready

- Partner Center real identity has not been applied.
- Final Store-signed MSIX has not been generated.
- WACK has not yet been rerun after the final changes in this audit.
- Manual tests have not been completed.
- FFmpeg source/build lock is partial.
- License package still needs full legal review.

## Final status

`READY FOR CI REVIEW`
