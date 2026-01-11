from click.testing import CliRunner
import httpx
from cli import cli


def test_seeds_writes_explicit_summary_csv(monkeypatch, tmp_path):
    seeds = tmp_path / "s.txt"
    seeds.write_text("https://example.com/a\n")

    transport = httpx.MockTransport(
        lambda req: httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=b"<html></html>",
        )
    )
    original_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client", lambda *args, **kwargs: original_client(transport=transport)
    )

    out = tmp_path / "explicit.csv"
    runner = CliRunner()
    res = runner.invoke(
        cli, ["seeds", "run", str(seeds), "--limit", "1", "--summary-csv", str(out)]
    )
    assert res.exit_code == 0
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    # header should contain timestamp and url columns
    assert "timestamp" in content.splitlines()[0]
    assert "url" in content.splitlines()[0]
