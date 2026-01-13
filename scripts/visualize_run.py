"""visualize_run.py

Generate visualizations for a specific experimental run directory (results/<run>).
If an `analysis.json` file exists, the script will visualize the top N suggested entities
from the analysis and write individual HTML files.

Usage:
    python scripts/visualize_run.py --run results/testing-5 --top 3 --outdir results/testing-5/visualizations
"""
import json
import argparse
from pathlib import Path

from probe.core.map import Map
from probe.visualization.graph_viz import GraphVisualizer


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True, help="Path to the run directory (e.g. results/testing-5)")
    p.add_argument("--top", type=int, default=3, help="Top N suggested entities to visualize")
    p.add_argument("--outdir", default=None, help="Output directory for generated visualizations")
    args = p.parse_args()

    run_dir = Path(args.run)
    if not run_dir.exists():
        raise SystemExit(f"Run directory not found: {run_dir}")

    analysis_file = run_dir / "analysis.json"
    outdir = Path(args.outdir or (run_dir / "visualizations"))
    outdir.mkdir(parents=True, exist_ok=True)

    # If analysis.json exists, pick the top N suggested entities
    entities = None
    if analysis_file.exists():
        with open(analysis_file, 'r', encoding='utf-8') as fh:
            analysis = json.load(fh)
        # assume structure: analysis['suggested_entities'] = [{'name': ..., ...}, ...]
        suggested = analysis.get('suggested_entities') or analysis.get('suggestions') or []
        entities = [s['name'] for s in suggested][: args.top]

    # If there is a run DB, prefer it; else expect user to point at a DB
    db_path = run_dir / 'probe.db'
    if db_path.exists():
        map_db = Map(str(db_path))
    else:
        raise SystemExit("No probe.db found in run directory; provide a directory with a DB")

    viz = GraphVisualizer(map_db)

    if entities:
        for e in entities:
            viz.build_graph(entity_name=e, depth=2)
            out = outdir / f"{e}-graph.html"
            viz.plot_interactive(str(out))
            print("Wrote", out)
    else:
        # full graph
        viz.build_graph()
        out = outdir / "full-graph.html"
        viz.plot_interactive(str(out))
        print("Wrote", out)

    map_db.close()


if __name__ == '__main__':
    main()
