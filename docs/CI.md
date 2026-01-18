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

### Re-running packaging smoke job & retrieving build logs

- To re-run the packaging smoke job for a PR/branch: open the Actions UI, select the CI workflow run for the branch or PR, then either click **Re-run jobs -> Re-run failed jobs** (fastest for intermittent failures) or use the **Run workflow** button on the CI workflow page to dispatch a fresh run on the branch.
- Build logs are uploaded as workflow artifacts. Look for artifacts named `packaging-smoke-build-log-<python-version>` (packaging smoke job) or `build-log-<python-version>-<ocr>` (packaging/wheel-install steps). Download the artifact and inspect the `build.out` file inside for the full stdout/stderr.
- If a PR originates from a fork, workflow runs may lack permission to post comments; in that case maintainers can download artifacts and paste relevant snippets into the PR comment. Tip: when filing issues or commenting on PRs include the first 200 lines of the `build.out` and the workflow run URL to help triage quickly.

- To reproduce a particular matrix combination locally, use the same Python version and install the same extras.
- If you need a manual run for scheduled OCR checks, use the workflow `Run workflow` button in the Actions UI (requires `workflow_dispatch`).

## JUnit reports & caching

- CI now produces `junit.xml` reports for each matrix row (uploaded as workflow artifacts) so you can download test reports from the Actions UI and inspect failing tests in CI.
- The workflow uses `actions/cache` to cache pip downloads across runs (keyed on Python version + requirements file hashes) to speed up dependency installs.
- Packaging artifacts (sdist/wheel) are also uploaded as workflow artifacts from the `packaging` job to simplify debugging of wheel/sdist builds.

## Autofix formatting workflow

We run an Autofix workflow on pull requests that executes `pre-commit` (Black, isort, ruff) to keep runner formatting consistent with local developer tooling. Notes:

- The workflow is defined in `.github/workflows/autofix.yml` and triggers on `pull_request` events. It installs the same pinned formatter versions as CI and runs `pre-commit run --all-files`.
- The workflow attempts to push any formatting fixes back to the PR branch using the `GITHUB_TOKEN`. The `contents` permission is required (`permissions: contents: write`) for pushes to succeed on repository-owned branches.
- Push failures (HTTP 403) are tolerated (the workflow now continues even when the runner cannot push, which is common for forked PRs that have read-only tokens). When the push succeeds, the commit will appear on the branch and CI will re-run with the formatted files.
- If you encounter a post-checkout submodule error like "No url found for submodule path 'tmp_ci_check' in .gitmodules" in Actions logs, this indicates a lingering submodule gitlink in the repository index. To resolve locally:

```bash
# Remove the gitlink from the index (do not remove local files if you want to preserve them)
git rm --cached tmp_ci_check || true
# Ensure it is ignored
echo "tmp_ci_check" >> .gitignore
# Commit the removal
git add .gitignore
git commit -m "ci: remove tmp_ci_check submodule gitlink and ignore it"
# Push the branch
git push
```

- Developer guidance: run `pre-commit run --all-files` and `mypy --config-file mypy.ini` locally before opening PRs to reduce back-and-forth autofix commits.



### Optional real-network integration tests (scheduled & manual)
We run a single real-network integration test on a weekly schedule and via manual dispatch. The workflow is .github/workflows/research-integration.yml. This job sets RUN_REAL_NET_TESTS=1 and runs the test 	ests/test_crawler_integration.py::test_end_to_end_crawl_index_and_search_real.
