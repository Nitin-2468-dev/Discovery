# Makefile: helpful helpers

.PHONY: sweep-weights
sweep-weights:
	python scripts/weight_sweep.py --seeds seeds/seeds_testing.txt --types manual --out results/weight_sweep.csv
