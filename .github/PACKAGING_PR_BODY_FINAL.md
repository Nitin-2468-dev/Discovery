This draft PR contains three focused changes to make packaging failures easier to detect and triage:

- **CI:** Add packaging-smoke job that attempts a wheel build up to 3 times and uploads packaging-smoke-build-log-<python-version> artifact on failure.
- **CI:** Improve wheel-install step to retry installing dist/*.whl up to 2 times and dump uild_logs/build.out when persistent failures occur.
- **Tests:** Add a retry to _build_wheel in 	ests/test_packaging_validation.py and write combined stdout/stderr to uild_logs/build.out on failure so CI artifacts include failure logs.
- **Docs:** Update docs/CI.md with instructions to re-run the packaging smoke job and where to find build logs.

Motivation: CI showed intermittent wheel build failures (missing METADATA / backend transient errors). These small, non-invasive changes make flakiness visible and give maintainers artifacts and a fast smoke job to reproduce issues.

Local verification: packaging tests passed repeatedly locally; full test suite passed (165 passed, 3 skipped).

This PR is a draft for initial review and feedback; happy to split into smaller PRs if preferred.

<!-- This is an auto-generated description by cubic. -->
---
## Summary by cubic
Makes packaging CI more resilient and easier to debug by adding a smoke job with wheel-build retries and capturing build logs as artifacts. Also adds retries for wheel install and test wheel builds, with logs included for faster triage.

- **New Features**
  - Added packaging-smoke CI job that retries wheel build up to 3 times and uploads packaging-smoke-build-log-<python-version>.
  - Captured and uploaded build logs in the main packaging job as build-log-<python-version>-<ocr>.

- **Bug Fixes**
  - Wheel install step now retries up to 2 times and dumps the first 500 lines of build_logs/build.out on persistent failure.
  - Tests: _build_wheel retries once and writes combined stdout/stderr to build_logs/build.out; docs updated with steps to re-run the smoke job and find logs.

<sup>Written for commit 154dbba146e61ccb75062602a5379d61b33cb597. Summary will update on new commits.</sup>

<!-- End of auto-generated description by cubic. -->


\n\n## Checklist\n- [ ] Run CI and confirm packaging-smoke artifacts are present for at least one matrix row\n- [ ] Verify wheel-install retry logs are produced on persistent failure\n- [ ] Confirm packaging tests pass consistently across 2-3 repeated runs\- [ ] Merge after peer review and CI green
\n\n## Checklist\n- [ ] Run CI and confirm \\packaging-smoke\\ artifacts are present for at least one matrix row\n- [ ] Verify \\wheel-install\\ retry logs are produced on persistent failure\n- [ ] Confirm packaging tests pass consistently across 2-3 repeated runs\n- [ ] Merge after peer review and CI green
