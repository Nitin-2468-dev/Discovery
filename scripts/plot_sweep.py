#!/usr/bin/env python3
"""Simple plotting helper for flattened sweep CSV.
Generates a scatter plot of composite_score vs weight_count for top domains.
Requires matplotlib (optional)."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

import csv


def parse_args(argv: List[str] | None = None):
    p = argparse.ArgumentParser()
    p.add_argument(
        "input", help="Flattened CSV (from flatten_sweep.py) or weight sweep CSV"
    )
    p.add_argument("output", help="Output PNG file")
    p.add_argument("--domain", default=None, help="Filter to a single domain")
    p.add_argument(
        "--normalize",
        default=None,
        help="Filter rows by normalization mode (if present in CSV)",
    )
    p.add_argument(
        "--mode",
        choices=["scatter", "heatmap"],
        default="scatter",
        help="Plot mode: scatter (default) or heatmap",
    )
    p.add_argument(
        "--heatmap-x",
        default="weight_count",
        help="Heatmap X-axis field (default: weight_count)",
    )
    p.add_argument(
        "--heatmap-y",
        default="weight_yield",
        help="Heatmap Y-axis field (default: weight_yield)",
    )
    p.add_argument(
        "--heatmap-domain",
        default=None,
        help="Domain to aggregate for heatmap (required for heatmap)",
    )
    return p.parse_args(argv)


def main(
    argv: List[str] | None = None,
) -> int:  # noqa: C901 - CLI plotting helper; scheduled for refactor
    args = parse_args(argv)
    input_path = Path(args.input)
    out_path = Path(args.output)

    if plt is None:
        print("matplotlib not available; install it to generate plots")
        return 1

    xs = []
    ys = []
    labels = []

    import json

    with input_path.open(newline="", encoding="utf-8") as fh:
        r = csv.DictReader(fh)
        for row in r:
            # optional normalize filter
            if args.normalize and row.get("normalize") != args.normalize:
                continue

            # Two supported CSV formats:
            # 1) Flattened rows with 'domain' and 'composite_score' (from flatten_sweep.py)
            # 2) Weight sweep rows with a JSON 'domain_scores_json' column (we'll expand each domain)
            if "domain" in row and "composite_score" in row and row.get("domain"):
                if args.domain and row.get("domain") != args.domain:
                    continue
                try:
                    wc = float(row.get("weight_count", 0.0) or 0.0)
                    score = float(row.get("composite_score", 0.0) or 0.0)
                except Exception:
                    continue
                xs.append(wc)
                ys.append(score)
                labels.append(row.get("domain"))
            elif row.get("domain_scores_json"):
                try:
                    ds = json.loads(row["domain_scores_json"])
                except Exception:
                    continue
                for d in ds:
                    dom = d.get("domain")
                    score = d.get("composite_score")
                    if not dom:
                        continue
                    if args.domain and dom != args.domain:
                        continue
                    try:
                        wc = float(row.get("weight_count", 0.0) or 0.0)
                        sc = float(score or 0.0)
                    except Exception:
                        continue
                    xs.append(wc)
                    ys.append(sc)
                    labels.append(dom)
            else:
                continue

    if args.mode == "scatter":
        if not xs:
            print("No data points to plot")
            return 1

        plt.figure(figsize=(6, 4))
        plt.scatter(xs, ys)
        plt.xlabel("weight_count")
        plt.ylabel("composite_score")
        plt.title("Sweep: composite_score vs weight_count")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(out_path)
        print(f"Saved plot to {out_path}")
        return 0

    # Heatmap mode: aggregate scores for a given domain across two weight dimensions
    if args.mode == "heatmap":
        if args.heatmap_domain is None:
            print("Heatmap mode requires --heatmap-domain")
            return 2

        # build grid dictionary keyed by (x_val, y_val) -> average score
        xs_unique = set()
        ys_unique = set()
        # Points will be aggregated by re-reading the CSV below

        # Re-read CSV to aggregate using specified fields
        from collections import defaultdict

        agg = defaultdict(list)
        with input_path.open(newline="", encoding="utf-8") as fh:
            r = csv.DictReader(fh)
            for row in r:
                if args.normalize and row.get("normalize") != args.normalize:
                    continue
                try:
                    ds = []
                    if row.get("domain_scores_json"):
                        import json

                        ds = json.loads(row["domain_scores_json"])
                    # find matching domain score
                    score = None
                    for d in ds:
                        if d.get("domain") == args.heatmap_domain:
                            score = float(d.get("composite_score", 0.0) or 0.0)
                            break
                    if score is None and row.get("domain") == args.heatmap_domain:
                        score = float(row.get("composite_score", 0.0) or 0.0)
                    if score is None:
                        continue
                    x_val = float(row.get(args.heatmap_x, 0.0) or 0.0)
                    y_val = float(row.get(args.heatmap_y, 0.0) or 0.0)
                except Exception:
                    continue
                agg[(x_val, y_val)].append(score)
                xs_unique.add(x_val)
                ys_unique.add(y_val)

        if not agg:
            print("No heatmap data found for domain", args.heatmap_domain)
            return 1

        xs_sorted = sorted(xs_unique)
        ys_sorted = sorted(ys_unique)
        import numpy as np

        z = np.zeros((len(ys_sorted), len(xs_sorted)))
        for i, yv in enumerate(ys_sorted):
            for j, xv in enumerate(xs_sorted):
                vals = agg.get((xv, yv), [])
                z[i, j] = sum(vals) / len(vals) if vals else np.nan

        plt.figure(figsize=(8, 6))
        plt.imshow(
            z,
            aspect="auto",
            origin="lower",
            interpolation="nearest",
            extent=(min(xs_sorted), max(xs_sorted), min(ys_sorted), max(ys_sorted)),
        )
        plt.colorbar(label="composite_score")
        plt.xlabel(args.heatmap_x)
        plt.ylabel(args.heatmap_y)
        plt.title(f"Heatmap: {args.heatmap_domain} (normalize={args.normalize})")
        plt.tight_layout()
        plt.savefig(out_path)
        print(f"Saved heatmap to {out_path}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
