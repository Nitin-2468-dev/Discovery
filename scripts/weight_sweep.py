#!/usr/bin/env python3
"""Weight sweep tool for GapDetector.

Produces a CSV of top suggested domains for each weight combination and entity.

Usage examples:

# Sweep defaults with entities listed in `seeds/seeds_testing.txt` and types 'manual'
python scripts/weight_sweep.py --seeds seeds/seeds_testing.txt --types manual --out results.csv

# Single-weight run (useful in CI)
python scripts/weight_sweep.py --entity "ACME-PT6A" --types manual --weight-count 1.0 --weight-yield 1.0 --weight-trust 0.5 --weight-recent 0.5 --out single.csv
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import os
import sys
from typing import List

from probe.analysis.gaps import GapDetector
from probe.core.map import Map


def parse_args(argv: List[str] | None = None):
    p = argparse.ArgumentParser(description="Weight sweep tool for GapDetector")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--seeds", help="File with one entity name per line")
    g.add_argument("--entity", help="Single entity name to test")

    p.add_argument(
        "--types", required=True, help="Comma-separated desired document types"
    )
    p.add_argument(
        "--db", default="probe.db", help="Path to DB file (default: probe.db)"
    )
    p.add_argument("--out", default="weight_sweep.csv", help="Output CSV file")

    p.add_argument(
        "--weight-count",
        help="Comma-separated weight values for count (default: 0.5,1.0,2.0,4.0)",
    )
    p.add_argument(
        "--weight-yield",
        help="Comma-separated weight values for yield (default: 0.0,1.0)",
    )
    p.add_argument(
        "--weight-trust",
        help="Comma-separated weight values for trust (default: 0.0,0.5,1.0)",
    )
    p.add_argument(
        "--weight-recent",
        help="Comma-separated weight values for recent (default: 0.0,0.5,1.0)",
    )

    return p.parse_args(argv)


def parse_list_arg(value: str | None, default: List[float]) -> List[float]:
    if not value:
        return default
    return [float(x.strip()) for x in value.split(",") if x.strip()]


def read_entities_from_file(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip()]


def run_sweep(
    entities: List[str],
    types: List[str],
    db_path: str,
    out_csv: str,
    counts,
    yields,
    trusts,
    recents,
):
    # ensure output directory exists
    out_dir = os.path.dirname(out_csv)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(out_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=[
                "entity",
                "types",
                "weight_count",
                "weight_yield",
                "weight_trust",
                "weight_recent",
                "top_domain",
                "top_score",
                "suggested_domains",
                "domain_scores_json",
            ],
        )
        writer.writeheader()

        total = 0
        for entity in entities:
            for wc, wy, wt, wr in itertools.product(counts, yields, trusts, recents):
                m = Map(db_path)
                detector = GapDetector(
                    m, weights={"count": wc, "yield": wy, "trust": wt, "recent": wr}
                )
                analysis = detector.analyze_entity_gaps(
                    entity, types, include_scores=True
                )
                m.close()

                ds = analysis.get("domain_scores") or []
                top_domain = ds[0]["domain"] if ds else ""
                top_score = ds[0]["composite_score"] if ds else 0.0
                suggested = ";".join([d["domain"] for d in ds])

                row = {
                    "entity": entity,
                    "types": ",".join(types),
                    "weight_count": wc,
                    "weight_yield": wy,
                    "weight_trust": wt,
                    "weight_recent": wr,
                    "top_domain": top_domain,
                    "top_score": top_score,
                    "suggested_domains": suggested,
                    "domain_scores_json": json.dumps(ds, ensure_ascii=False),
                }
                writer.writerow(row)
                total += 1

    print(f"Wrote {total} rows to {out_csv}")
    return 0


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    types = [t.strip() for t in args.types.split(",") if t.strip()]

    entities = []
    if args.seeds:
        entities = read_entities_from_file(args.seeds)
    else:
        entities = [args.entity]

    counts = parse_list_arg(args.weight_count, [0.5, 1.0, 2.0, 4.0])
    yields = parse_list_arg(args.weight_yield, [0.0, 1.0])
    trusts = parse_list_arg(args.weight_trust, [0.0, 0.5, 1.0])
    recents = parse_list_arg(args.weight_recent, [0.0, 0.5, 1.0])

    return run_sweep(
        entities, types, args.db, args.out, counts, yields, trusts, recents
    )


if __name__ == "__main__":
    raise SystemExit(main())
