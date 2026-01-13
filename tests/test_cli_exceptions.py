import logging
from click.testing import CliRunner
from cli import cli


def test_fetch_cmd_handles_fetch_exceptions(monkeypatch, caplog, tmp_path):
    # monkeypatch fetch to raise
    def bad_fetch(url, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr('probe.crawl.fetcher.fetch', bad_fetch)

    runner = CliRunner()
    caplog.set_level(logging.ERROR)
    res = runner.invoke(cli, ['fetch', 'https://example.com', '--db', str(tmp_path / 'probe.db')])

    assert res.exit_code != 0
    assert 'Fetch failed' in res.output
    # ensure exception was logged
    assert any('Fetch failed' in rec.getMessage() or 'Error fetching' in rec.getMessage() for rec in caplog.records)
