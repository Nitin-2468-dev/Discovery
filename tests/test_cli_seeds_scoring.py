import httpx
from click.testing import CliRunner

from cli import cli


def test_seeds_run_score_and_persist(monkeypatch, tmp_path):
    seeds = tmp_path / "s.txt"
    url = "https://example.com/"
    seeds.write_text(url + "\n")

    def handler(request):
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=b'<html><head><title>One</title></head><body><p>maintenance manual</p><a href="/a">A</a></body></html>',
        )

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client", lambda *args, **kwargs: original_client(transport=transport)
    )

    db = str(tmp_path / "db.sqlite")
    csvp = tmp_path / "out.csv"

    runner = CliRunner()
    res = runner.invoke(
        cli,
        [
            "seeds",
            "run",
            str(seeds),
            "--limit",
            "1",
            "--score",
            "--persist-scores",
            "--db",
            db,
            "--summary-csv",
            str(csvp),
        ],
    )
    assert res.exit_code == 0
    assert "Persisted scoring report id" in res.output

    # verify DB has a report for this URL
    from probe.core.map import Map

    m = Map(db)
    rep = m.get_latest_scoring_report_for_url(url)
    assert rep is not None
    assert float(rep["score"]) >= 0.0

    # verify CSV content includes score and top_component
    import csv

    with open(csvp, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        rows = list(r)
        assert len(rows) == 1
        assert "score" in rows[0]
        assert rows[0]["score"] != ""

    m.close()


def test_seeds_run_score_to_csv_only(monkeypatch, tmp_path):
    seeds = tmp_path / "s2.txt"
    url = "https://example.org/"
    seeds.write_text(url + "\n")

    def handler(request):
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=b"<html><head><title>Two</title></head><body><p>manual</p></body></html>",
        )

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client", lambda *args, **kwargs: original_client(transport=transport)
    )

    csvp = tmp_path / "out2.csv"
    runner = CliRunner()
    res = runner.invoke(
        cli,
        [
            "seeds",
            "run",
            str(seeds),
            "--limit",
            "1",
            "--score",
            "--summary-csv",
            str(csvp),
        ],
    )
    assert res.exit_code == 0
    import csv

    with open(csvp, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        rows = list(r)
        assert len(rows) == 1
        assert "score" in rows[0]
        assert rows[0]["score"] != ""
