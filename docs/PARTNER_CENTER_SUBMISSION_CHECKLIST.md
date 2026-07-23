# Partner Center submission checklist

Status: `READY FOR PARTNER CENTER IDENTITY`

Do not submit until every required item is completed with real evidence.

## Identity

- [ ] Reserve/finalize PackageName in Partner Center.
- [ ] Configure real Publisher from Partner Center.
- [ ] Configure PublisherDisplayName.
- [ ] Generate Store build with real identity.
- [ ] Do not commit private PFX/certificate material.

## Package

- [ ] Generate standalone from clean environment.
- [ ] Generate MSIX with Store identity.
- [ ] Sign through accepted Store/Partner Center process.
- [ ] Validate MSIX layout.
- [ ] Confirm no `.pyc`, cache, `.env`, private key or Movaura Beta artifact.

## Certification

- [ ] Run WACK on the final signed MSIX.
- [ ] Confirm no required FAIL.
- [ ] Document optional FAIL entries if any.
- [ ] Keep WACK XML in release evidence.

## Legal/licensing

- [ ] Review FFmpeg LGPL package.
- [ ] Confirm no GPL-only Qt module is unintentionally distributed.
- [ ] Include third-party notices and license texts.
- [ ] Complete professional legal review.

## Privacy

- [ ] Publish privacy policy URL.
- [ ] Mention beta activation/licensing if enabled.
- [ ] Mention optional network features.
- [ ] Provide support contact.

## Manual tests

- [ ] Install on clean machine.
- [ ] Run without admin privileges.
- [ ] Test one monitor and two monitors.
- [ ] Test DPI 100/125/150 percent.
- [ ] Test apply/stop/restore.
- [ ] Test import file/folder.
- [ ] Test uninstall/reinstall.
- [ ] Confirm no orphan compositor process.
