## Change

Describe the problem and resulting behavior. Link the issue; use `Closes #N` if completed.

## Validation

List tests run and results, plus any remaining manual or hardware checks.

## Contributor checklist

Check each item when satisfied or not applicable; explain exceptions above.

- [ ] Runtime, test and build dependencies are declared in the appropriate requirements files.
- [ ] Distributable resources are tracked under `assets/`, `data/`, or `hal2030/`, with appropriate redistribution rights.
- [ ] No private data, credentials, runtime output or downloaded models are committed.
- [ ] Relevant behavior/regressions are tested; screenshot checks are not treated as full functional validation.
- [ ] Packaging and setup are checked for native libraries, dynamic imports and external models.
- [ ] Observed, simulated and estimated data remain clearly labeled.
- [ ] Before merge: required Linux tests, Windows tests and Windows executable checks pass on an up-to-date branch.

See [CONTRIBUTING.md](https://github.com/ItayBlank/space-health-monitor/blob/main/CONTRIBUTING.md) for setup and the CI contract.
