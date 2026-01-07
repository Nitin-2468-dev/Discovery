from click.testing import CliRunner
import httpx
from cli import cli
from pathlib import Path
import csv


def test_seeds_retry_updates_retry_count(monkeypatch, tmp_path):
    seeds = tmp_path / "s.txt"
    seeds.write_text("https://example.com/first\n")

    calls = {"n": 0}

    def handler(request):
        # avoid consuming 429 during robots.txt fetch
        if request.url.path == '/robots.txt':
            return httpx.Response(200, content=b"")
        calls["n"] += 1
        if calls["n"] == 1:
            # First call returns 429 for the page
            return httpx.Response(429, headers={"retry-after": "0"}, content=b"Too Many")
        return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, content=b"<html></html>")

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: original_client(transport=transport))

    summary_dir = tmp_path / "reports"
    runner = CliRunner()
    res = runner.invoke(cli, ["seeds", "run", str(seeds), "--limit", "1", "--summary-dir", str(summary_dir)])

    assert res.exit_code == 0
    files = list(summary_dir.glob("*.csv"))
    assert len(files) == 1

    with open(files[0], newline='') as f:
        rows = list(csv.DictReader(f))
        assert int(rows[0]['retry_count']) >= 1
        assert rows[0]['success'] == 'True'
