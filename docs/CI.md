# CI and Test Matrix

This repository uses GitHub Actions to run unit and integration tests across supported Python versions and optional extras (OCR). This document summarizes the workflow and how to reproduce CI behavior locally.

## Workflow overview

- `.github/workflows/ci.yml` runs on `push`, `pull_request`, `schedule` (weekly), and `workflow_dispatch` (manual trigger).
- The main `test` job runs a matrix across Python versions (`3.10`, `3.11`) and an `ocr` boolean. When `ocr=true`, CI will install OCR extras so tests that require OCR packages can run.
- A `packaging` job now verifies editable installs (`pip install -e .`) and optional extras (`pip install -e .[ocr]`), and builds sdist/wheel artifacts to catch packaging issues early.

## How to run locally

- Run tests (default):

```bash
python -m pip install -U pip
pip install -r requirements.txt
pytest -q
```

- Run tests with OCR extras (install optional deps):

```bash
pip install -r requirements-ocr.txt
# or, when using editable install for package extras
pip install -e .[ocr]
pytest -q
```

- Reproduce packaging & editable install checks:

```bash
python -m pip install -U pip
pip install build
python -m build --sdist --wheel
pip install -e .
pip install -e .[ocr]
```

## Debugging failing CI runs

- Use the Actions UI to view logs and job steps; the `packaging` job contains build logs if editable install fails.
- To reproduce a particular matrix combination locally, use the same Python version and install the same extras.
- If you need a manual run for scheduled OCR checks, use the workflow `Run workflow` button in the Actions UI (requires `workflow_dispatch`).

## JUnit reports & caching

- CI now produces `junit.xml` reports for each matrix row (uploaded as workflow artifacts) so you can download test reports from the Actions UI and inspect failing tests in CI.
- The workflow uses `actions/cache` to cache pip downloads across runs (keyed on Python version + requirements file hashes) to speed up dependency installs.
- Packaging artifacts (sdist/wheel) are also uploaded as workflow artifacts from the `packaging` job to simplify debugging of wheel/sdist builds.
