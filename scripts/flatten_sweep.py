#!/usr/bin/env python3
"""Flatten sweep CSV (one row per domain per weight combo) for easier plotting."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import List


def parse_args(argv: List[str] | None = None):
    p = argparse.ArgumentParser()
    p.add_argument("input", help="Input sweep CSV")
    p.add_argument("output", help="Output flattened CSV")
    return p.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    input_path = Path(args.input)
    output_path = Path(args.output)

    with (
        input_path.open(newline="", encoding="utf-8") as fh_in,
        output_path.open("w", newline="", encoding="utf-8") as fh_out,
    ):
        reader = csv.DictReader(fh_in)
        fieldnames = [
            "entity",
            "types",
            "weight_count",
            "weight_yield",
            "weight_trust",
            "weight_recent",
            "domain",
            "composite_score",
            "count",
            "yield_score",
            "trust_score",
            "recent_score",
        ]
        writer = csv.DictWriter(fh_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            ds_json = row.get("domain_scores_json")
            if not ds_json:
                continue
            try:
                ds = json.loads(ds_json)
            except Exception:
                continue
            for d in ds:
                out = {
                    "entity": row.get("entity"),
                    "types": row.get("types"),
                    "weight_count": row.get("weight_count"),
                    "weight_yield": row.get("weight_yield"),
                    "weight_trust": row.get("weight_trust"),
                    "weight_recent": row.get("weight_recent"),
                    "domain": d.get("domain"),
                    "composite_score": d.get("composite_score"),
                    "count": d.get("count"),
                    "yield_score": d.get("yield_score"),
                    "trust_score": d.get("trust_score"),
                    "recent_score": d.get("recent_score"),
                }
                writer.writerow(out)

    print(f"Wrote flattened CSV to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
