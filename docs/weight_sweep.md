# Weight Sweep: running and plotting

This document describes how to run the weight sweep tool and how to visualize results.

Running a sweep

- Use `scripts/weight_sweep.py` to run a grid search over weights and normalization modes.

Example (small sweep):

```bash
python scripts/weight_sweep.py --entity "ACME-PT6A" --types datasheet --db probe.db --out results/sweep.csv --weight-count 0.5,1.0,2.0 --weight-yield 0.0,1.0 --weight-trust 0.0,0.5 --weight-recent 0.0 --normalize none,per_page,log
```

Plotting the results

- Use `scripts/plot_sweep.py` to create simple plots from a sweep CSV.

Example:

```bash
python scripts/plot_sweep.py results/sweep.csv results/plots/summary.png
```

- The plotting utility accepts both flattened CSVs (with `domain` and `composite_score` columns) and the weight-sweep CSV (has `domain_scores_json` column). For weight-sweep CSVs the script will expand domain scores and plot composite_score vs weight_count.

Interpreting outputs

- `weight_sweep.py` CSV rows include the top suggested domain and a JSON field `domain_scores_json` with per-domain component scores for that weight configuration.
- `plot_sweep.py` produces a scatter plot of `composite_score` vs `weight_count` (or similar) which helps you understand sensitivity of the top suggestions to weight changes.

Tips

- Use the `--normalize` option of `scripts/weight_sweep.py` to explore `none`, `per_page`, `log`, and `per_page_log` modes.
- Start with a small grid to get intuition, then expand sampling where results are sensitive.

Examples & Dashboard

- A small example CSV and summary are included in `results/examples/sweep_example.csv` and `results/examples/sweep_example_summary.txt`.
- An example interactive heatmap for `a.example.com` is in `results/examples/heatmap_example.html` (open in browser to explore the interactive heatmap built with Plotly).
- For a more feature-rich interactive dashboard, use `scripts/plot_sweep_plotly.py` to generate an HTML heatmap for any domain from your sweep CSV.
