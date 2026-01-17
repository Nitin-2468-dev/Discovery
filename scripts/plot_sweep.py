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
except ImportError:
    plt = None

import csv


def parse_args(argv: List[str] | None = None):
    p = argparse.ArgumentParser()
    p.add_argument("input", help="Flattened CSV (from flatten_sweep.py)")
    p.add_argument("output", help="Output PNG file")
    p.add_argument("--domain", default=None, help="Filter to a single domain")
    return p.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    input_path = Path(args.input)
    out_path = Path(args.output)

    if plt is None:
        print("matplotlib not available; install it to generate plots")
        return 1

    xs = []
    ys = []
    labels = []

    with input_path.open(newline="", encoding="utf-8") as fh:
        r = csv.DictReader(fh)
        for row in r:
            if args.domain and row["domain"] != args.domain:
                continue
            try:
                wc = float(row["weight_count"])
                score = float(row["composite_score"])
            except Exception:
                continue
            xs.append(wc)
            ys.append(score)
            labels.append(row["domain"])

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


if __name__ == "__main__":
    raise SystemExit(main())
