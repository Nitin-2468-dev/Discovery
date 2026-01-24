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
    plt = None  # type: ignore[assignment]

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


def _read_csv_rows(input_path: Path, normalize: str | None = None):
    """Yield CSV rows (dicts), optionally filtering by normalize value."""
    with input_path.open(newline="", encoding="utf-8") as fh:
        r = csv.DictReader(fh)
        for row in r:
            if normalize and row.get("normalize") != normalize:
                continue
            yield row


def _expand_row_to_points(row: dict, domain_filter: str | None = None):
    """Yield (weight_count, composite_score, domain) tuples from a CSV row.

    Supports both flattened rows with 'domain'+'composite_score' and rows with
    'domain_scores_json'.
    """
    if "domain" in row and "composite_score" in row and row.get("domain"):
        dom = row.get("domain")
        if domain_filter and dom != domain_filter:
            return
        try:
            wc = float(row.get("weight_count", 0.0) or 0.0)
            score = float(row.get("composite_score", 0.0) or 0.0)
        except Exception:
            return
        yield (wc, score, dom)
        return

    if row.get("domain_scores_json"):
        try:
            import json

            ds = json.loads(row["domain_scores_json"])
        except Exception:
            return
        for d in ds:
            dom = d.get("domain")
            score = d.get("composite_score")
            if not dom:
                continue
            if domain_filter and dom != domain_filter:
                continue
            try:
                wc = float(row.get("weight_count", 0.0) or 0.0)
                sc = float(score or 0.0)
            except Exception:
                continue
            yield (wc, sc, dom)


def _collect_scatter_points(
    input_path: Path, domain: str | None, normalize: str | None
):
    xs = []
    ys = []
    labels = []
    for row in _read_csv_rows(input_path, normalize=normalize):
        for wc, score, dom in _expand_row_to_points(row, domain):
            xs.append(wc)
            ys.append(score)
            labels.append(dom)
    return xs, ys, labels


def _find_domain_score_in_row(row: dict, heatmap_domain: str):
    """Return the composite_score for heatmap_domain from a row (or None)."""
    try:
        # check domain_scores_json first
        if row.get("domain_scores_json"):
            import json

            ds = json.loads(row["domain_scores_json"])
            for d in ds:
                if d.get("domain") == heatmap_domain:
                    return float(d.get("composite_score", 0.0) or 0.0)

        # fallback to flattened row
        if row.get("domain") == heatmap_domain:
            return float(row.get("composite_score", 0.0) or 0.0)
    except Exception:
        return None

    return None


def _aggregate_heatmap(
    input_path: Path,
    heatmap_domain: str,
    heatmap_x: str,
    heatmap_y: str,
    normalize: str | None,
):
    """Aggregate points into a grid keyed by (x_val, y_val) returning sorted x, y and the z-grid (list of lists)."""
    from collections import defaultdict

    agg = defaultdict(list)
    xs_unique = set()
    ys_unique = set()

    for row in _read_csv_rows(input_path, normalize=normalize):
        score = _find_domain_score_in_row(row, heatmap_domain)
        if score is None:
            continue
        try:
            x_val = float(row.get(heatmap_x, 0.0) or 0.0)
            y_val = float(row.get(heatmap_y, 0.0) or 0.0)
        except Exception:
            continue
        agg[(x_val, y_val)].append(score)
        xs_unique.add(x_val)
        ys_unique.add(y_val)

    if not agg:
        return [], [], []

    xs_sorted = sorted(xs_unique)
    ys_sorted = sorted(ys_unique)

    # build z as rows for y then x (matches imshow expectation with origin='lower')
    z = []
    for yv in ys_sorted:
        row = []
        for xv in xs_sorted:
            vals = agg.get((xv, yv), [])
            row.append(sum(vals) / len(vals) if vals else float("nan"))
        z.append(row)

    return xs_sorted, ys_sorted, z


def _plot_scatter(xs, ys, out_path: Path):
    plt.figure(figsize=(6, 4))
    plt.scatter(xs, ys)
    plt.xlabel("weight_count")
    plt.ylabel("composite_score")
    plt.title("Sweep: composite_score vs weight_count")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_path)


def _plot_heatmap(z, xs_sorted, ys_sorted, args, out_path: Path):
    import numpy as np

    arr = np.array(z)
    plt.figure(figsize=(8, 6))
    plt.imshow(
        arr,
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


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    input_path = Path(args.input)
    out_path = Path(args.output)

    if plt is None:
        print("matplotlib not available; install it to generate plots")
        return 1

    if args.mode == "scatter":
        xs, ys, labels = _collect_scatter_points(
            input_path, args.domain, args.normalize
        )
        if not xs:
            print("No data points to plot")
            return 1
        _plot_scatter(xs, ys, out_path)
        print(f"Saved plot to {out_path}")
        return 0

    if args.mode == "heatmap":
        if args.heatmap_domain is None:
            print("Heatmap mode requires --heatmap-domain")
            return 2
        xs_sorted, ys_sorted, z = _aggregate_heatmap(
            input_path,
            args.heatmap_domain,
            args.heatmap_x,
            args.heatmap_y,
            args.normalize,
        )
        if not z:
            print("No heatmap data found for domain", args.heatmap_domain)
            return 1
        _plot_heatmap(z, xs_sorted, ys_sorted, args, out_path)
        print(f"Saved heatmap to {out_path}")
        return 0

    # Should never reach here due to argparse choices, but make return explicit for typing
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
