import types

import httpx
from click.testing import CliRunner

from cli import cli


def test_seeds_run_no_progress(monkeypatch, tmp_path):
    # ensure --no-progress works and doesn't crash
    seeds = tmp_path / "s.txt"
    seeds.write_text("https://example.com/\n")

    def handler(request):
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=b"<html><head><title>One</title></head><body></body></html>",
        )

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client", lambda *args, **kwargs: original_client(transport=transport)
    )

    runner = CliRunner()
    res = runner.invoke(
        cli, ["seeds", "run", str(seeds), "--limit", "1", "--no-progress"]
    )
    assert res.exit_code == 0


def test_seeds_run_uses_tqdm_if_available(monkeypatch, tmp_path):
    # Mock tqdm to ensure it's invoked when not disabled
    called = {"invoked": False}

    def fake_tqdm(iterable, **kwargs):
        called["invoked"] = True
        # return the iterable unchanged but as a list to simulate wrapping
        return list(iterable)

    fake_mod = types.SimpleNamespace(tqdm=fake_tqdm)
    monkeypatch.setitem(__import__("sys").modules, "tqdm", fake_mod)

    seeds = tmp_path / "s2.txt"
    seeds.write_text("https://example.com/\nhttps://example.org/\n")

    def handler(request):
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=b"<html><head><title>One</title></head><body></body></html>",
        )

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client", lambda *args, **kwargs: original_client(transport=transport)
    )

    runner = CliRunner()
    res = runner.invoke(cli, ["seeds", "run", str(seeds), "--limit", "2"])
    assert res.exit_code == 0
    assert called["invoked"] is True
