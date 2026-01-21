## PR Review Checklist

Before merging a PR (especially feature and tooling changes), please verify:

- [ ] CI is green (Lint, Tests, Packaging, Demo run if present)
- [ ] `pre-commit run --all-files` passes locally (Black/isort/ruff)
- [ ] Test suite runs locally (`pytest -q`) and new tests cover the change
- [ ] For changes that touch crawling/orchestration, run the demo locally:
  - `python scripts/demo_e2e.py --output-dir ./demo-out`
  - Inspect `demo-out/demo_results.json` and `demo-out/demo_summary.html`
- [ ] If the PR impacts packaging or release behavior, confirm packaging-smoke artifacts and wheel-install logs in CI
- [ ] Add a short note to the PR description describing how the reviewer can validate the change (commands/flags/scripts)

Optional for maintainers:
- Run the `Demo: e2e demo` workflow from the Actions tab (manual) and inspect uploaded artifacts for the run.

Artifact access tips:
- UI: Actions → select demo run → Artifacts → download `probe-demo-artifacts` and open `demo_summary.html`.
- CLI: use GitHub CLI to download artifacts for a run:
  ```bash
  gh run list --workflow demo.yml
  gh run download <run-id> -n probe-demo-artifacts -D ./demo-artifacts
  open ./demo-artifacts/demo_summary.html  # macOS/Linux
  start ./demo-artifacts/demo_summary.html # Windows
  ```
