#!/usr/bin/env python3
"""Run full end-to-end pipeline for a given run directory and record per-step timings.

Steps:
  - fetch & ingest (runs scripts/run_seed_trial.py)
  - flatten sweep
  - plot sweep (top domain)
  - visualize run (scripts/visualize_run.py)

Writes timings to <run_dir>/timings.csv and prints summary.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z"


def time_it(step_name: str, fn, *args, **kwargs):
    start = time.perf_counter()
    start_iso = now_iso()

    result = fn(*args, **kwargs)

    end = time.perf_counter()
    end_iso = now_iso()
    duration = end - start

    rec = {
        'step': step_name,
        'start': start_iso,
        'end': end_iso,
        'duration_seconds': f"{duration:.3f}",
    }
    print(f"{step_name}: {rec['duration_seconds']}s")
    return result, rec


def run_seed_trial(seeds: str, count: int, types: str, out: str, db: str | None = None):
    # Call the script entrypoint (imported) to ensure we run in-process and capture timing
    import importlib.util

    path = Path(__file__).parent / 'run_seed_trial.py'
    spec = importlib.util.spec_from_file_location('run_seed_trial', str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore

    argv = ['--seeds', seeds, '--count', str(count), '--types', types, '--out', out]
    if db:
        argv += ['--db', db]
    return mod.main(argv)


def flatten_sweep(in_csv: str, out_csv: str):
    import importlib.util
    path = Path(__file__).parent / 'flatten_sweep.py'
    spec = importlib.util.spec_from_file_location('flatten_sweep', str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod.main([str(in_csv), str(out_csv)])


def plot_sweep(flat_csv: str, out_png: str, domain: str | None = None):
    import importlib.util
    path = Path(__file__).parent / 'plot_sweep.py'
    spec = importlib.util.spec_from_file_location('plot_sweep', str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    argv = [str(flat_csv), str(out_png)]
    if domain:
        argv += ['--domain', domain]
    return mod.main(argv)


def visualize_run(run_dir: str, top: int = 3, outdir: str | None = None):
    import importlib.util
    import sys
    path = Path(__file__).parent / 'visualize_run.py'
    spec = importlib.util.spec_from_file_location('visualize_run', str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    outd = outdir or (Path(run_dir) / 'visualizations')
    # The script's main() expects sys.argv; emulate CLI invocation
    argv = sys.argv
    try:
        sys.argv = ['scripts/visualize_run.py', '--run', str(run_dir), '--top', str(top), '--outdir', str(outd)]
        return mod.main()
    finally:
        sys.argv = argv


def pick_top_domain(flat_csv: str) -> str | None:
    # Pick domain with highest composite_score
    import csv

    best = None
    best_score = -1.0
    with open(flat_csv, newline='', encoding='utf-8') as fh:
        r = csv.DictReader(fh)
        for row in r:
            try:
                score = float(row.get('composite_score') or 0)
            except (ValueError, TypeError):
                continue
            if score > best_score:
                best_score = score
                best = row.get('domain')
    return best


def main(argv: List[str] | None = None):
    p = argparse.ArgumentParser()
    p.add_argument('--run', required=True, help='Output run dir (e.g. results/testing-5)')
    p.add_argument('--seeds', default='seeds/seeds_testing.txt')
    p.add_argument('--count', type=int, default=5)
    p.add_argument('--types', default='manual')
    p.add_argument('--db', default=None)
    args = p.parse_args(argv)

    run_dir = Path(args.run)
    run_dir.mkdir(parents=True, exist_ok=True)

    timings = []

    # Step 1: fetch & ingest & analysis & sweep
    out_prefix = str(run_dir)
    db_path = args.db or str(run_dir / 'probe.db')
    print('Step: fetch & ingest & analysis')
    _, rec = time_it('fetch_ingest_analysis', run_seed_trial, args.seeds, args.count, args.types, out_prefix, db_path)
    timings.append(rec)

    # Step 2: flatten sweep
    sweep_csv = str(run_dir / 'sweep.csv')
    flat_csv = str(run_dir / 'sweep_flat.csv')
    print('Step: flatten sweep')
    _, rec = time_it('flatten_sweep', flatten_sweep, sweep_csv, flat_csv)
    timings.append(rec)

    # Step 3: pick top domain and plot
    print('Step: pick top domain')
    top_domain = pick_top_domain(flat_csv)
    print('Top domain:', top_domain)
    plot_png = str(run_dir / f'plot_{top_domain or "top"}.png')
    print('Step: plot sweep')
    _, rec = time_it('plot_sweep', plot_sweep, flat_csv, plot_png, top_domain)
    timings.append(rec)

    # Step 4: generate visualizations
    print('Step: visualize run')
    viz_outdir = run_dir / 'visualizations'
    _, rec = time_it('visualize_run', visualize_run, str(run_dir), 3, str(viz_outdir))
    timings.append(rec)

    # Write timings CSV
    timings_csv = run_dir / 'timings.csv'
    with open(timings_csv, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=['step', 'start', 'end', 'duration_seconds'])
        w.writeheader()
        for t in timings:
            w.writerow(t)

    print('Wrote timings to', timings_csv)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
