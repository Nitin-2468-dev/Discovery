import time
from datetime import datetime

import httpx
from click.testing import CliRunner

import probe.crawl.state as state
from cli import cli


def test_seeds_persistent_politeness_respects_stored_last_crawled(
    monkeypatch, tmp_path
):
    # switch cwd so state file is created in tmp path
    monkeypatch.chdir(tmp_path)

    seeds = tmp_path / "s.txt"
    seeds.write_text("https://example.com/a\n")

    # set last crawled to now (so worker should sleep for approximately per_domain_delay)
    state.clear_state()
    # instead of relying on file-based state, monkeypatch get_last_crawled to return now
    monkeypatch.setattr(state, "get_last_crawled", lambda d: datetime.now())

    # measure duration to ensure the run waits due to persistent politeness
    start = time.monotonic()

    # mock HTTP client to avoid real network
    def handler(request):
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=b"<html></html>",
        )

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client", lambda *args, **kwargs: original_client(transport=transport)
    )

    runner = CliRunner()
    per_domain_delay = 2.0
    res = runner.invoke(
        cli,
        [
            "seeds",
            "run",
            str(seeds),
            "--limit",
            "1",
            "--concurrency",
            "1",
            "--per-domain-delay",
            str(per_domain_delay),
            "--persistent-politeness",
        ],
    )
    assert res.exit_code == 0

    end = time.monotonic()
    duration = end - start
    # expect the run to take at least ~per_domain_delay (allow some leeway)
    assert duration >= per_domain_delay * 0.6

    # cleanup
    state.clear_state()
