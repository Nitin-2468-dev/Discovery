from click.testing import CliRunner
import httpx
from cli import cli


def test_cli_min_delay_flag_respected(monkeypatch, tmp_path):
    seeds = tmp_path / "s.txt"
    seeds.write_text("https://example.com/a\nhttps://example.com/b\n")

    sleeps = []

    def fake_sleep(sec):
        sleeps.append(sec)

    # simple handler
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

    monkeypatch.setattr("time.sleep", fake_sleep)

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
            "--min-delay",
            "0.5",
        ],
    )
    assert res.exit_code == 0
    assert len(sleeps) >= 1
    # allow a small timing leeway for thread scheduling; expect at least ~min_delay * 0.4
    assert sleeps[0] >= 0.5 * 0.4
