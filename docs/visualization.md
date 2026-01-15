# Visualization

Use the `visualize` CLI command to generate an interactive knowledge graph (HTML).

Usage:

- Visualize the entire graph and save to `graph.html`:

```
probe visualize --db probe.db --output graph.html
```

- Visualize an entity neighborhood (depth=2):

```
probe visualize --entity "PT6A-52" --depth 2 --output pt6a52.html
```

Notes:

- The visualization relies on NetworkX and Plotly; if these packages are not installed the CLI will still run if a compatible visualizer is available (it produces a minimal HTML listing nodes/edges).
- For a richer interactive visualization (force-directed layout with hover labels), install the plotting libs and re-run the command:

```
pip install networkx plotly
probe visualize --entity "PT6A-52" --db probe.db --output graph-rich.html
```

- You can export static images (requires `kaleido`):

```
pip install kaleido
probe visualize --entity "PT6A-52" --db probe.db --output graph-rich.html --export-png graph.png --export-svg graph.svg
```

- To open the generated HTML automatically in your browser, use `--open`:

```
probe visualize --entity "PT6A-52" --db probe.db --output graph-rich.html --open
```

- To visualize an actual experimental run directory (uses `analysis.json` suggestions if present):

```
python scripts/visualize_run.py --run results/testing-5 --top 3 --outdir results/testing-5/visualizations
```

- The output file is a self-contained HTML that can be opened in a browser.

## Risk-Aware Graphs

When Policy is active the visualizer will (future implementation):

- Color-code high-risk nodes (sensitive sources, restricted categories)
- In `public_guarded` mode, suppress or summarize sensitive edges/nodes
- In `educational_open` mode, include hidden edges with prominent warnings

Visualizations will be annotated with metadata from the Policy Engine so reviewers can quickly identify risk areas.
