import httpx
from click.testing import CliRunner
from cli import cli
from pathlib import Path


def test_robots_blocks_seed(monkeypatch, tmp_path):
    # create seeds file
    seeds = tmp_path / "s.txt"
    seeds.write_text("https://example.com/page\n")

    # ensure cache is clear
    from probe.crawl.robots import clear_cache
    clear_cache()

    # robots.txt disallows /
    def handler(request):
        if request.url.path == '/robots.txt':
            return httpx.Response(200, content=b"User-agent: *\nDisallow: /\n")
        return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, content=b"<html></html>")

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: original_client(transport=transport))

    runner = CliRunner()
    summary_dir = tmp_path / "reports"
    res = runner.invoke(cli, ["seeds", "run", str(seeds), "--limit", "1", "--summary-dir", str(summary_dir)])

    assert res.exit_code == 0
    files = list(summary_dir.glob("*.csv"))
    assert len(files) == 1

    with open(files[0], newline='') as f:
        rows = list(__import__('csv').DictReader(f))
        # blocked seeds should be marked unsuccessful
        assert rows[0]['success'] == 'False'

    log = Path('constraints.log').read_text()
    assert 'blocked_by_robots' in log


def test_ignore_robots_allows_fetch(monkeypatch, tmp_path):
    seeds = tmp_path / "s2.txt"
    seeds.write_text("https://example.com/page\n")
    # ensure cache is clear
    from probe.crawl.robots import clear_cache
    clear_cache()
    def handler(request):
        if request.url.path == '/robots.txt':
            return httpx.Response(200, content=b"User-agent: *\nDisallow: /\n")
        return httpx.Response(200, headers={"content-type": "text/html; charset=utf-8"}, content=b"<html><title>OK</title></html>")

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: original_client(transport=transport))

    runner = CliRunner()
    summary_dir = tmp_path / "reports"
    res = runner.invoke(cli, ["seeds", "run", str(seeds), "--limit", "1", "--summary-dir", str(summary_dir), "--ignore-robots"])

    assert res.exit_code == 0
    files = list(summary_dir.glob("*.csv"))
    assert len(files) == 1
    with open(files[0], newline='') as f:
        rows = list(__import__('csv').DictReader(f))
        assert rows[0]['success'] == 'True'
