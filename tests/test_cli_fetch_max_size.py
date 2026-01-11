from click.testing import CliRunner
import httpx
from cli import cli


def test_cli_fetch_respects_max_size(monkeypatch):
    big = b"a" * 5000

    def handler(request):
        return httpx.Response(
            200, headers={"content-type": "text/html; charset=utf-8"}, content=big
        )

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client", lambda *args, **kwargs: original_client(transport=transport)
    )

    runner = CliRunner()
    res = runner.invoke(cli, ["fetch", "https://large.example/", "--max-size", "1000"])
    assert res.exit_code == 0
    assert "max_size_exceeded" in res.output or "✗ max_size_exceeded" in res.output
