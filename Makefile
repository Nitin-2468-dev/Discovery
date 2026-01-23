# Makefile: helpful helpers

.PHONY: sweep-weights format ci-checks
sweep-weights:
	python scripts/weight_sweep.py --seeds seeds/seeds_testing.txt --types manual --out results/weight_sweep.csv

format:
	# Format the repository using Black and isort
	black .
	isort .

ci-checks:
	# Run the same checks the CI runs (formatters in check mode + linters + mypy)
	black --check . || (echo "Black found formatting issues; run 'make format' locally." && exit 1)
	isort --check-only . || (echo "isort found import-order issues; run 'make format' locally." && exit 1)
	pre-commit run --all-files --show-diff-on-failure || (echo "pre-commit detected issues; run 'pre-commit run --all-files' locally." && exit 1)
	ruff check . || (echo "ruff found issues; run 'ruff check .' locally to inspect." && exit 1)
	mypy . || (echo "mypy found issues; run 'mypy .' locally to inspect." && exit 1)
