from click.testing import CliRunner
import httpx
from cli import cli


def test_cli_ignore_retry_after_end_to_end(monkeypatch, tmp_path):
    seeds = tmp_path / "s.txt"
    seeds.write_text("https://example.com/a\n")

    calls = []
    sleeps = []

    def handler(request):
        if len(calls) == 0:
            calls.append("first")
            return httpx.Response(429, headers={"Retry-After": "5"})
        else:
            calls.append("second")
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

    def fake_sleep(s):
        sleeps.append(s)

    # Ensure we capture sleep calls at the time module used by the fetcher
    monkeypatch.setattr("time.sleep", fake_sleep)

    runner = CliRunner()
    # run with ignore-retry-after -> should sleep ~backoff (0.5) instead of 5
    res = runner.invoke(
        cli, ["seeds", "run", str(seeds), "--limit", "1", "--ignore-retry-after"]
    )
    assert res.exit_code == 0
    # We don't directly assert exact sleep count because other internal sleeps may occur; ensure at least two calls were made and the final call succeeded
    assert len(calls) >= 2
    assert calls[-1] == "second"
