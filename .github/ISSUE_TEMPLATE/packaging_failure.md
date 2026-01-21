---
name: Packaging failure report
about: Use this template when packaging/wheel build fails in CI; include the build log artifact and workflow run URL if available.
labels: packaging, ci
assignees: ''
---

**Describe the problem**
A clear and concise description of what failed during packaging (wheel/sdist build or wheel install).

**Reproduction (CI or local)**
- Workflow run URL: <link to the failed Actions run>
- Artifact name (if present): `packaging-smoke-build-log-<python-version>` or `build-log-<python-version>-<ocr>`

**Attach the build log**
Please attach the `build.out` file from the workflow artifact or paste the first 200 lines of it here.

**Additional context**
Add any other context about the environment, Python version, or steps you tried to reproduce locally.

**Suggested triage steps**
1. Download the `build.out` artifact from the Actions UI and inspect the first error message.
2. Re-run the packaging smoke job on the branch (Actions -> CI -> Run workflow -> select branch).
3. If the failure is intermittent, note how many times you re-ran and attach additional `build.out` outputs if available.
