#!/usr/bin/env python3
"""Run a short crawl for a set of seeds and produce GapDetector analysis + weight sweep CSV.

Usage:

python scripts/run_seed_trial.py --seeds seeds/seeds_testing.txt --count 5 --types manual --out results/testing-5
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import List

from probe.core.map import Edge, Entity, Map
from probe.crawl.ingest import ingest_fetch_result


def parse_args(argv: List[str] | None = None):
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", required=True, help="seeds file path")
    p.add_argument("--count", type=int, default=1)
    p.add_argument("--types", default="manual", help="comma separated types")
    p.add_argument("--out", required=True, help="output prefix (dir will be created)")
    p.add_argument("--db", default=None, help="db path (optional)")
    return p.parse_args(argv)


def load_seeds(path: str, count: int) -> List[str]:
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            out.append(s)
            if len(out) >= count:
                break
    return out


def fetch_and_ingest(seeds: List[str], db_path: str, entity_name: str):
    # Import lazily to avoid network side effects during import time
    fetcher = __import__("probe.crawl.fetcher", fromlist=["fetch"])  # module
    m = Map(db_path)

    entity = Entity(id=None, name=entity_name, type="seed-run", confidence_score=0.5)
    eid = m.add_entity(entity)

    results = []
    for url in seeds:
        try:
            res = fetcher.fetch(url, timeout=10, max_retries=2, max_size=2000000)
        except Exception as exc:
            results.append({"url": url, "error": str(exc)})
            continue

        if res.get("error"):
            results.append({"url": url, "error": res.get("error")})
            continue

        out = ingest_fetch_result(m, res)
        # link created document to entity if any
        if out.get("document_id"):
            doc_id = out.get("document_id")
            edge = Edge(
                id=None,
                from_type="entity",
                from_id=eid,
                to_type="document",
                to_id=doc_id,
                relation="has_document",
            )
            m.add_edge(edge)
        results.append({"url": url, "summary": out})

        # polite sleep
        time.sleep(1.0)

    m.close()
    return results


def run_analysis(db_path: str, entity_name: str, types: List[str], out_prefix: str):
    from probe.analysis.gaps import GapDetector

    m = Map(db_path)
    gd = GapDetector(m)
    analysis = gd.analyze_entity_gaps(entity_name, types, include_scores=True)
    m.close()

    out_dir = Path(out_prefix)
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "analysis.json", "w", encoding="utf-8") as fh:
        json.dump(analysis, fh, indent=2)

    # run a focused weight sweep (small grid)
    counts = [0.5, 1.0, 2.0]
    yields = [0.0, 1.0]
    trusts = [0.0, 0.5]
    recents = [0.0, 0.5]

    # Import weight_sweep as a script module (avoid package import issues)
    import importlib.util

    ws_path = Path(__file__).parent / "weight_sweep.py"
    spec = importlib.util.spec_from_file_location("weight_sweep", str(ws_path))
    ws = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ws)  # type: ignore

    csv_out = str(out_dir / "sweep.csv")
    ws.run_sweep(
        [entity_name], types, db_path, csv_out, counts, yields, trusts, recents
    )

    return analysis, csv_out


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    seeds = load_seeds(args.seeds, args.count)
    if not seeds:
        print("No seeds found for given count")
        return 1

    out_prefix = args.out
    db_path = args.db or (out_prefix + ".db")

    print(f"Running seeds: {seeds} -> DB: {db_path}")
    # ensure db parent directory exists
    db_parent = Path(db_path).parent
    if db_parent and not db_parent.exists():
        db_parent.mkdir(parents=True, exist_ok=True)

    entity_name = f"seed-run-{Path(args.seeds).stem}-{args.count}"

    fetch_results = fetch_and_ingest(seeds, db_path, entity_name)
    with open(out_prefix + "-fetch.json", "w", encoding="utf-8") as fh:
        json.dump(fetch_results, fh, indent=2)

    analysis, csv_out = run_analysis(
        db_path,
        entity_name,
        [t.strip() for t in args.types.split(",") if t.strip()],
        out_prefix,
    )

    print(f"Analysis written to {out_prefix}/analysis.json and sweep to {csv_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
