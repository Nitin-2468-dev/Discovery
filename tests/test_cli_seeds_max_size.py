from click.testing import CliRunner
import httpx
from cli import cli
from pathlib import Path
import csv


def test_seeds_run_max_size_records_failure(monkeypatch, tmp_path):
    seeds = tmp_path / "s.txt"
    seeds.write_text("https://example.com/large\n")

    big = b"a" * 5000

    def handler(request):
        return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, content=big)

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: original_client(transport=transport))

    summary_dir = tmp_path / "reports"
    runner = CliRunner()
    res = runner.invoke(cli, ["seeds", "run", str(seeds), "--limit", "1", "--summary-dir", str(summary_dir), "--max-size", "1000"]) 
    assert res.exit_code == 0

    files = list(summary_dir.glob("*.csv"))
    assert len(files) == 1

    with open(files[0], newline='') as f:
        rows = list(csv.DictReader(f))
        assert rows[0]['success'] == 'False'
        assert 'max_size_exceeded' in rows[0]['error_message']

    # constraints.log should have an entry
    log = Path('constraints.log').read_text()
    assert 'FETCHER_FAILURE' in log
    assert 'https://example.com/large' in log
