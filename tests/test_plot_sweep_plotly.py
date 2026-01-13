import subprocess, sys
from pathlib import Path
import csv

def test_plotly_heatmap_cli(tmp_path):
    csvp = tmp_path / 'sweep.csv'
    rows = [
        {"weight_count": "1.0", "weight_yield": "0.0", "top_domain": "a.example.com", "top_score": "2.0", "domain_scores_json": "[{\"domain\": \"a.example.com\", \"composite_score\": 2.0}]"},
        {"weight_count": "2.0", "weight_yield": "1.0", "top_domain": "a.example.com", "top_score": "3.0", "domain_scores_json": "[{\"domain\": \"a.example.com\", \"composite_score\": 3.0}]"},
    ]
    with open(csvp, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)

    out = tmp_path / 'heat.html'
    proc = subprocess.run([sys.executable, 'scripts/plot_sweep_plotly.py', str(csvp), '--domain', 'a.example.com', '--out', str(out)], capture_output=True, text=True)
    # If plotly is present, file should be created; otherwise script returns non-zero
    assert proc.returncode in (0, 2)
    if out.exists():
        assert out.stat().st_size > 0
