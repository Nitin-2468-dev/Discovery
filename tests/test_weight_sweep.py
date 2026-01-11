import csv
import subprocess
import sys
from pathlib import Path


def test_weight_sweep_cli(tmp_path):
    out = tmp_path / "out.csv"
    seeds = tmp_path / "seeds.txt"
    seeds.write_text("TEST-ENT\n")

    proc = subprocess.run(
        [sys.executable, "scripts/weight_sweep.py", "--seeds", str(seeds), "--types", "manual", "--out", str(out), "--weight-count", "1.0", "--weight-yield", "1.0", "--weight-trust", "0.5", "--weight-recent", "0.5", "--db", str(tmp_path / 'sweep.db')],
        check=False,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0
    assert out.exists()

    with open(out, newline='', encoding='utf-8') as fh:
        r = csv.DictReader(fh)
        rows = list(r)
    assert len(rows) >= 1
    # basic sanity check columns
    assert "entity" in rows[0]
    assert "top_domain" in rows[0]
