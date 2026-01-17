<<<<<<< HEAD
import json

from click.testing import CliRunner
=======
from click.testing import CliRunner
import json
>>>>>>> ci/parallel-tests

from cli import cli


class FakeDomain:
<<<<<<< HEAD
    def __init__(
        self, domain_name, yield_score=0.5, trust_score=0.5, last_crawled_at=None
    ):
=======
    def __init__(self, domain_name, yield_score=0.5, trust_score=0.5, last_crawled_at=None):
>>>>>>> ci/parallel-tests
        self.domain_name = domain_name
        self.yield_score = yield_score
        self.trust_score = trust_score
        self.last_crawled_at = last_crawled_at


class FakeMapForMetrics:
    def __init__(self):
        pass

    def get_entity(self, name):
        return type("E", (), {"confidence_score": 0.5})()

    def get_entity_document_types(self, name):
        return []

    def get_high_yield_domains(self, limit=5, min_pages=1):
<<<<<<< HEAD
        return [
            FakeDomain("a.example.com", yield_score=0.1),
            FakeDomain("b.example.com", yield_score=0.9),
        ]
=======
        return [FakeDomain("a.example.com", yield_score=0.1), FakeDomain("b.example.com", yield_score=0.9)]
>>>>>>> ci/parallel-tests

    def get_domain(self, name):
        if name == "a.example.com":
            return FakeDomain(name, yield_score=0.1, trust_score=0.2)
        return FakeDomain(name, yield_score=0.9, trust_score=0.9)

    def close(self):
        return None


def test_cli_metrics_json(monkeypatch):
    runner = CliRunner()

    def fake_map(db):
        return FakeMapForMetrics()

    monkeypatch.setattr("cli.Map", fake_map)

<<<<<<< HEAD
    res = runner.invoke(
        cli, ["gaps", "E", "--types", "manual,datasheet", "--json", "--metrics"]
    )
=======
    res = runner.invoke(cli, ["gaps", "E", "--types", "manual,datasheet", "--json", "--metrics"])
>>>>>>> ci/parallel-tests
    assert res.exit_code == 0

    parsed = json.loads(res.output)
    assert "domain_scores" in parsed
    assert isinstance(parsed["domain_scores"], list)
