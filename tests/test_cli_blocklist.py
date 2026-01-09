from click.testing import CliRunner
import httpx
from cli import cli
from pathlib import Path


def test_blocklist_sequential(monkeypatch, tmp_path):
    seeds = tmp_path / "s.txt"
    seeds.write_text("https://blocked.example/\nhttps://allowed.example/\n")

    blocked = tmp_path / "blocked.txt"
    blocked.write_text("blocked.example\n")

    def handler(request):
        # if any fetch attempted for blocked.example it will still return a response, but we expect it not to be fetched
        return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, content=b"<html></html>")

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: original_client(transport=transport))

    runner = CliRunner()
    res = runner.invoke(cli, ["seeds", "run", str(seeds), "--limit", "2", "--blocked-domains", str(blocked)])
    assert res.exit_code == 0
    # check constraints.log contains our blocked_by_blocklist entry
    import re
    txt = Path('constraints.log').read_text(encoding='utf-8')
    assert 'blocked_by_blocklist' in txt


def test_blocklist_concurrent(monkeypatch, tmp_path):
    seeds = tmp_path / "s2.txt"
    seeds.write_text("https://blocked.example/\nhttps://blocked.example/page2\n")

    blocked = tmp_path / "blocked2.txt"
    blocked.write_text("blocked.example\n")

    def handler(request):
        return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, content=b"<html></html>")

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: original_client(transport=transport))

    runner = CliRunner()
    res = runner.invoke(cli, ["seeds", "run", str(seeds), "--limit", "2", "--concurrency", "2", "--blocked-domains", str(blocked)])
    assert res.exit_code == 0
    # check constraints.log contains our blocked_by_blocklist entry
    txt = Path('constraints.log').read_text(encoding='utf-8')
    assert 'blocked_by_blocklist' in txt