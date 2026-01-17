import json

from click.testing import CliRunner

from cli import cli
from probe.core.map import Entity, Map


def test_cli_investigate_policy_denies(tmp_path, monkeypatch):
    db_path = str(tmp_path / "probe.db")
    m = Map(db_path)
    m.add_entity(Entity(id=None, name="TestEnt"))
    m.close()

    # make seed generator produce deny-listed domain
    def fake_generate_seeds(self, domains, types, per_domain=1):
        return ["http://malicious.example/doc.pdf"]

    monkeypatch.setattr(
        "probe.analysis.seed_generator.SeedGenerator.generate_seeds",
        fake_generate_seeds,
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "investigate",
            "TestEnt",
            "--types",
            "manual",
            "--max-seeds",
            "1",
            "--no-dry-run",
            "--json",
            "--db",
            db_path,
            "--mode",
            "public_guarded",
        ],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["error"] == "policy_denied"


def test_cli_investigate_policy_allows_with_admin_flag(tmp_path, monkeypatch):
    db_path = str(tmp_path / "probe.db")
    m = Map(db_path)
    m.add_entity(Entity(id=None, name="TestEnt"))
    m.close()

    def fake_generate_seeds(self, domains, types, per_domain=1):
        return ["http://malicious.example/doc.pdf"]

    monkeypatch.setattr(
        "probe.analysis.seed_generator.SeedGenerator.generate_seeds",
        fake_generate_seeds,
    )

    # mock fetch to succeed
    def fake_fetch(url, timeout=5, max_retries=1, backoff_factor=0.0):
        return {"status_code": 200, "error": None}

    import probe.crawl.fetcher as fetchmod

    monkeypatch.setattr(fetchmod, "fetch", fake_fetch)

    runner = CliRunner()
    # pass --admin-enabled before subcommand
    result = runner.invoke(
        cli,
        [
            "--admin-enabled",
            "investigate",
            "TestEnt",
            "--types",
            "manual",
            "--max-seeds",
            "1",
            "--no-dry-run",
            "--json",
            "--db",
            db_path,
            "--mode",
            "educational_open",
        ],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0].get("status_code") == 200
