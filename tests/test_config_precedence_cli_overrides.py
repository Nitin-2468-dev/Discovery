from click.testing import CliRunner
from pathlib import Path
from cli import cli
import httpx
import json


def test_config_concurrency_precedence(tmp_path, monkeypatch):
    # Create a config file with concurrency=3
    cfgp = tmp_path / "probe.config.json"
    cfgp.write_text(json.dumps({"concurrency": 3}))
    # copy into working dir
    Path("probe.config.json").write_text(cfgp.read_text(), encoding="utf-8")

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
