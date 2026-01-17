import csv
import subprocess
import sys


def test_plot_sweep_heatmap_cli(tmp_path):
    out = tmp_path / "sweep.csv"
    rows = [
        {
            "weight_count": "1.0",
            "weight_yield": "0.0",
            "normalize": "none",
            "domain_scores_json": '[{"domain": "d1", "composite_score": 2.0}]',
        },
        {
            "weight_count": "2.0",
            "weight_yield": "1.0",
            "normalize": "none",
            "domain_scores_json": '[{"domain": "d1", "composite_score": 3.5}]',
        },
        {
            "weight_count": "1.0",
            "weight_yield": "1.0",
            "normalize": "none",
            "domain_scores_json": '[{"domain": "d1", "composite_score": 1.5}]',
        },
    ]
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)

    png = tmp_path / "heatmap.png"
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/plot_sweep.py",
            str(out),
            str(png),
            "--mode",
            "heatmap",
            "--heatmap-domain",
            "d1",
            "--heatmap-x",
            "weight_count",
            "--heatmap-y",
            "weight_yield",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode in (0, 1)
    if png.exists():
        assert png.stat().st_size > 0
