import time
from click.testing import CliRunner
import httpx
from cli import cli


def test_seeds_concurrency_respects_per_domain_delay(monkeypatch, tmp_path):
    seeds = tmp_path / "s.txt"
    seeds.write_text("https://example.com/a\nhttps://example.com/b\n")

    timestamps = []

    def handler(request):
        timestamps.append(time.monotonic())
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
    res = runner.invoke(
        cli,
        [
            "seeds",
            "run",
            str(seeds),
            "--limit",
            "2",
            "--concurrency",
            "2",
            "--per-domain-delay",
            "0.2",
        ],
    )
    assert res.exit_code == 0
    assert len(timestamps) == 2
    # the timestamps for the same domain should be separated by approximately the delay
    delay = 0.2
    required = delay * 0.6
    assert abs(timestamps[1] - timestamps[0]) >= required

    # cleanup not needed when flags used
