This draft PR contains three focused changes to make packaging failures easier to detect and triage:

- **CI:** Add packaging-smoke job that attempts a wheel build up to 3 times and uploads packaging-smoke-build-log-<python-version> artifact on failure.
- **CI:** Improve wheel-install step to retry installing dist/*.whl up to 2 times and dump uild_logs/build.out when persistent failures occur.
- **Tests:** Add a retry to _build_wheel in 	ests/test_packaging_validation.py and write combined stdout/stderr to uild_logs/build.out on failure so CI artifacts include failure logs.
- **Docs:** Update docs/CI.md with instructions to re-run the packaging smoke job and where to find build logs.

Motivation: CI showed intermittent wheel build failures (missing METADATA / backend transient errors). These small, non-invasive changes make flakiness visible and give maintainers artifacts and a fast smoke job to reproduce issues.

Local verification: packaging tests passed repeatedly locally; full test suite passed (165 passed, 3 skipped).

This PR is a draft for initial review and feedback; happy to split into smaller PRs if preferred.
