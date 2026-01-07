from click.testing import CliRunner
import httpx
from cli import cli
import tempfile
from pathlib import Path


def test_seeds_run_no_ingest(monkeypatch, tmp_path):
    # prepare seeds file
    seeds = tmp_path / "s.txt"
    seeds.write_text("https://example.com/\nhttps://example.org/\n")

    def handler(request):
        return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, content=b"<html><head><title>One</title></head><body></body></html>")

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: original_client(transport=transport))

    runner = CliRunner()
    res = runner.invoke(cli, ["seeds", "run", str(seeds), "--limit", "2"])
    assert res.exit_code == 0
    assert "Loaded 2 seeds" in res.output
    assert "Successes: 2" in res.output


def test_seeds_run_with_ingest(monkeypatch, tmp_path):
    seeds = tmp_path / "s2.txt"
    seeds.write_text("https://example.org/\n")

    def handler(request):
        return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, content=b"<html><head><title>Ingest</title></head><body></body></html>")

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: original_client(transport=transport))

    db = str(tmp_path / "db.sqlite")
    runner = CliRunner()
    res = runner.invoke(cli, ["seeds", "run", str(seeds), "--ingest", "--db", db])
    assert res.exit_code == 0
    assert "Ingested" in res.output
    # verify DB had a page
    from probe.core.map import Map
    m = Map(db)
    stats = m.get_map_summary()
    assert stats["pages"] == 1
    m.close()
