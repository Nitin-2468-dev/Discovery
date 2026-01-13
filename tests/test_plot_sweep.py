import json
from pathlib import Path

import types

from scripts import plot_sweep


def write_csv(path: Path, rows):
    import csv

    with path.open("w", newline="", encoding="utf-8") as fh:
        if not rows:
            return
        # Use the union of all keys across rows so differing row schemas are supported
        fieldnames = sorted({k for r in rows for k in r.keys()})
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def test_expand_row_to_points_flattened():
    row = {"domain": "example.com", "composite_score": "1.5", "weight_count": "2"}
    pts = list(plot_sweep._expand_row_to_points(row, None))
    assert pts == [(2.0, 1.5, "example.com")]


def test_expand_row_to_points_json():
    row = {"domain_scores_json": json.dumps([{"domain": "a.com", "composite_score": 0.5}]), "weight_count": "3"}
    pts = list(plot_sweep._expand_row_to_points(row, None))
    assert pts == [(3.0, 0.5, "a.com")]


def test_collect_scatter_points_and_main_scatter(tmp_path, monkeypatch):
    csv_path = tmp_path / "sweep.csv"
    out = tmp_path / "out.png"
    rows = [
        {"domain": "example.com", "composite_score": "1.0", "weight_count": "1"},
        {"domain_scores_json": json.dumps([{"domain": "example.com", "composite_score": 2.0}]), "weight_count": "2"},
    ]
    write_csv(csv_path, rows)

    # fake matplotlib to capture savefig
    fake_plt = types.SimpleNamespace()
    calls = {}

    def figure(**kwargs):
        calls['figure'] = kwargs

    def scatter(xs, ys):
        calls['scatter'] = (list(xs), list(ys))

    def savefig(path):
        calls['saved'] = str(path)

    fake_plt.figure = figure
    fake_plt.scatter = scatter
    fake_plt.xlabel = lambda *a, **k: None
    fake_plt.ylabel = lambda *a, **k: None
    fake_plt.title = lambda *a, **k: None
    fake_plt.grid = lambda *a, **k: None
    fake_plt.tight_layout = lambda *a, **k: None
    fake_plt.savefig = savefig

    monkeypatch.setattr(plot_sweep, "plt", fake_plt)

    rc = plot_sweep.main([str(csv_path), str(out)])
    assert rc == 0
    assert calls.get('saved') == str(out)
    assert 'scatter' in calls


def test_aggregate_heatmap(tmp_path):
    csv_path = tmp_path / "sweep.csv"
    rows = [
        {"domain": "example.com", "composite_score": "1.0", "weight_count": "1", "weight_yield": "0.1"},
        {"domain": "example.com", "composite_score": "3.0", "weight_count": "2", "weight_yield": "0.2"},
    ]
    write_csv(csv_path, rows)

    xs, ys, z = plot_sweep._aggregate_heatmap(csv_path, "example.com", "weight_count", "weight_yield", None)
    assert xs == [1.0, 2.0]
    assert ys == [0.1, 0.2]
    assert len(z) == 2
    # check first row first col value == 1.0
    assert z[0][0] == 1.0
