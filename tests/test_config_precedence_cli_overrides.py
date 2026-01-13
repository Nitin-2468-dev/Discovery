import json
from pathlib import Path

import httpx
from click.testing import CliRunner

from cli import cli


def test_config_concurrency_precedence(tmp_path, monkeypatch):
    # Create a config file with concurrency=3
    # Run this test inside tmp_path to avoid writing to the repository root and causing
    # race conditions with other parallel tests that may read probe.config.json from CWD.
    monkeypatch.chdir(tmp_path)

    cfgp = tmp_path / "probe.config.json"
    cfgp.write_text(json.dumps({"concurrency": 3}))

    seeds = tmp_path / "s.txt"
    seeds.write_text("https://a.example/\nhttps://b.example/\n")

    def handler(request):
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=b"<html></html>",
        )

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        httpx, "Client", lambda *args, **kwargs: httpx.Client(transport=transport)
    )

    runner = CliRunner()
    # Do not pass --concurrency, expect config value used
    res = runner.invoke(cli, ["seeds", "run", str(seeds), "--limit", "2"])
    assert res.exit_code == 0
    assert "Running with concurrency=3" in res.output

    # Now override with CLI
    res2 = runner.invoke(
        cli, ["seeds", "run", str(seeds), "--limit", "2", "--concurrency", "2"]
    )
    assert res2.exit_code == 0
    assert "Running with concurrency=2" in res2.output

    # cleanup
    Path("probe.config.json").unlink()
