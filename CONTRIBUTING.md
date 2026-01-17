# Contributing

Thanks for contributing! A few quick notes to make contributions go smoothly:

- CI: We run a CI matrix including linting, packaging checks, and tests. Please run `pre-commit` hooks locally and ensure `pytest -q` passes before opening a PR.
- Packaging annotations: For security, the automated packaging annotation that posts build log summaries to a PR is only posted when the PR originates from a branch in this repository (not a fork). If you open a PR from a fork and you need maintainers to see the packaging logs, you can either:
  - Attach the `build-log` artifact to the PR by asking maintainers to run the `Packager: annotate packaging` workflow for your run (see repository Actions), or
  - Paste the relevant snippet into the PR description.

Thanks for helping keep the project high-quality and secure.
