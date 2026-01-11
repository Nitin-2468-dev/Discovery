import csv
from pathlib import Path
from click.testing import CliRunner
from cli import cli
import httpx


def test_seed_run_writes_csv_and_logs(monkeypatch, tmp_path):
    # prepare seeds file with one success and one failure
    seeds = tmp_path / "s.txt"
    seeds.write_text("https://example.com/success\nhttps://example.com/fail\n")

    def handler(request):
        path = request.url.path
        if path.endswith("/success"):
            return httpx.Response(
                200,
                headers={"content-type": "text/html; charset=utf-8"},
                content=b"<html><head><title>OK</title></head><body></body></html>",
            )
        if path.endswith("/fail"):
            return httpx.Response(
                500,
                headers={"content-type": "text/html; charset=utf-8"},
                content=b"Server Error",
            )
        # default
        return httpx.Response(
            404,
            headers={"content-type": "text/html; charset=utf-8"},
            content=b"Not Found",
        )

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client", lambda *args, **kwargs: original_client(transport=transport)
    )

    runner = CliRunner()
    summary_dir = tmp_path / "reports"
    res = runner.invoke(
        cli,
        ["seeds", "run", str(seeds), "--limit", "2", "--summary-dir", str(summary_dir)],
    )

    assert res.exit_code == 0

    # check CSV exists
    files = list(summary_dir.glob("*.csv"))
    assert len(files) == 1

    # Read CSV and assert two rows + header
    with open(files[0], newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        print("CSV ROWS:", rows)
        assert len(rows) == 2
        assert any(r["success"] == "True" for r in rows)
        assert any(r["success"] == "False" for r in rows)

    # check constraints.log got an entry for the failed URL
    log = Path("constraints.log").read_text()
    print("LOG TAIL:", log.strip().splitlines()[-10:])
    assert "FETCHER_FAILURE" in log
    assert "https://example.com/fail" in log
