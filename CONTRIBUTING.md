# Contributing

Claim the relevant issue before starting, work on a feature branch, and open a
pull request against `main`. Keep each PR focused and include `Closes #N` when it
completes an issue. All collaborators with write access can merge through a PR;
review approvals are optional, but the required CI checks must pass.

## Contributor checklist

- Declare runtime dependencies in `requirements.txt` or a requirements file it
  includes. Put test-only dependencies in `requirements-dev.txt` and build-only
  dependencies in `requirements-build.txt`.
- Commit distributable resources under `assets/`, `data/`, or the application
  package (`hal2030/`). CI packages tracked resources from these locations. Check
  their license and redistribution terms before adding them.
- Keep runtime output, credentials, private data, virtual environments and
  downloaded models out of Git. Document explicit setup for external resources.
- Add behavioral tests for new features and regression tests for fixes where
  appropriate. Navigation screenshots check startup and rendering; they do not
  test dialog flows, microphone quality, hardware behavior or medical validity.
- Check packaging when introducing native libraries, dynamic third-party imports,
  external models or new resource locations. Update PyInstaller hooks/spec files
  when needed, and document any additional setup.
- Run relevant local tests and inspect the PR's executable build. Report what was
  tested and any remaining manual checks in the PR description.
- Before merging, wait for all required CI jobs: `test (ubuntu-latest)`,
  `test (windows-latest)`, and `windows-executable`. Update the branch from `main`
  and rerun CI if GitHub marks it out of date. Do not bypass failing checks.

## Local validation

From the repository root, using Python 3.13:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

On Windows, validate packaging when the change affects distribution:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean packaging/HAL2030.spec
.\.venv\Scripts\python.exe tools/download_voice_model.py --destination dist/voice-model
.\.venv\Scripts\python.exe tools/smoke_executable.py dist/HAL2030.exe --output-dir build/smoke --verify-voice-model
```

The app exposes its current navigation pages to the smoke runner. New dialogs and
interactions still need feature-specific tests. Keep observed, simulated and
estimated values clearly labeled, and use UTC timestamps and stable crew IDs.

## CI maintenance

The workflow runs for every PR, pushes to `main`, and manual dispatch. A new PR
commit cancels its outdated run. The executable artifact identifies the PR/run
and tested commit. See the [CI maintenance contract](README.md#ci-maintenance-contract).

The required check names above are also configured in GitHub branch protection.
Renaming a job or changing matrix labels requires updating that configuration;
otherwise PRs will wait for a check name that is no longer produced. GitHub Actions
is the required source of these checks. Do not add path filters that prevent the
required workflow from running on some PRs.
