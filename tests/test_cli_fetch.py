from click.testing import CliRunner
import httpx
from cli import cli


def test_cli_fetch_no_ingest(monkeypatch):
    html = """<html><head><title>Fetch Me</title></head><body><p>X</p><a href="/a">A</a></body></html>"""

    def handler(request):
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=html.encode("utf-8"),
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: client)

    runner = CliRunner()
    res = runner.invoke(cli, ["fetch", "https://example.com/"])
    assert res.exit_code == 0
    assert "Fetching: https://example.com/" in res.output
    assert "Title: Fetch Me" in res.output


def test_cli_fetch_with_ingest(monkeypatch, tmp_path):
    html = "<html><head><title>Ingest</title></head><body><p>X</p></body></html>"

    def handler(request):
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=html.encode("utf-8"),
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: client)

    db = str(tmp_path / "probe.db")
    runner = CliRunner()
    res = runner.invoke(cli, ["fetch", "https://example.org/", "--ingest", "--db", db])
    assert res.exit_code == 0
    assert "Ingested:" in res.output
    # ensure the DB now has a page
    from probe.core.map import Map

    m = Map(db)
    stats = m.get_map_summary()
    assert stats["pages"] == 1
    m.close()
