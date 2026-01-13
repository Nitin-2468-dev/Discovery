#!/usr/bin/env python3
"""Interactive Plotly heatmap generator for weight sweep CSVs.

Produces an HTML file with an interactive heatmap for a selected domain.
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import defaultdict


def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("csv", help="Sweep CSV")
    p.add_argument("--domain", required=True, help="Domain to visualize")
    p.add_argument("--x", default="weight_count", help="X axis field")
    p.add_argument("--y", default="weight_yield", help="Y axis field")
    p.add_argument("--out", default="sweep_heatmap.html", help="Output HTML file")
    return p.parse_args(argv)


def main(argv=None):  # noqa: C901 - CLI plotting helper; scheduled for refactor
    args = parse_args(argv)
    rows = []
    with open(args.csv, newline='', encoding='utf-8') as fh:
        r = csv.DictReader(fh)
        for row in r:
            ds = []
            if row.get('domain_scores_json'):
                try:
                    ds = json.loads(row['domain_scores_json'])
                except Exception:
                    pass
            # Find domain score
            sc = None
            for d in ds:
                if d.get('domain') == args.domain:
                    sc = d.get('composite_score')
                    break
            if sc is None and row.get('top_domain') == args.domain:
                sc = float(row.get('top_score') or 0.0)
            if sc is None:
                continue
            try:
                x = float(row.get(args.x, 0.0) or 0.0)
                y = float(row.get(args.y, 0.0) or 0.0)
                rows.append((x, y, float(sc)))
            except Exception:
                continue

    if not rows:
        print('No data for domain')
        return 1

    # Build grid
    xs = sorted({r[0] for r in rows})
    ys = sorted({r[1] for r in rows})
    grid = defaultdict(list)
    for x, y, sc in rows:
        grid[(x, y)].append(sc)

    z = []
    for yv in ys:
        row = []
        for xv in xs:
            vals = grid.get((xv, yv), [])
            row.append(sum(vals) / len(vals) if vals else None)
        z.append(row)

    try:
        import plotly.graph_objects as go
    except Exception:
        print('plotly not available; install plotly to produce interactive HTML')
        return 2

    fig = go.Figure(data=go.Heatmap(z=z, x=xs, y=ys, colorscale='Viridis'))
    fig.update_layout(title=f'Heatmap: {args.domain}', xaxis_title=args.x, yaxis_title=args.y)
    fig.write_html(args.out, include_plotlyjs='cdn')
    print('Wrote', args.out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
