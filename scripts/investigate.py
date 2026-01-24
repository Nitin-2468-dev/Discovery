#!/usr/bin/env python3
"""CLI wrapper for a short investigation run.

Usage:
  python scripts/investigate.py --entity "ACME-PT6A" --types datasheet --out seeds.csv
"""

from __future__ import annotations

import argparse
import csv

from probe.analysis.investigator import Investigator
from probe.core.map import Map


def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--entity", help="Entity name", required=True)
    p.add_argument("--types", help="Comma-separated doc types", required=True)
    p.add_argument("--db", default="probe.db", help="DB path")
    p.add_argument("--out", default="seeds.csv", help="Output CSV for seeds")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    types = [t.strip() for t in args.types.split(",") if t.strip()]

    m = Map(args.db)
    inv = Investigator(m)
    result = inv.investigate(args.entity, types, max_seeds=20, dry_run=True)
    m.close()

    seeds = result.get("seeds", [])
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["seed"])
        for s in seeds:
            w.writerow([s])
    print(f"Wrote {len(seeds)} seeds to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
