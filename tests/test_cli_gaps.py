from click.testing import CliRunner
import json

import pytest

from cli import cli


class FakeDomain:
    def __init__(self, domain_name):
        self.domain_name = domain_name


class FakeMapForCLI:
    def __init__(self, db=None, entity_present=True, doc_types=None, confidence=0.0, doc_count=0):
        self._entity_present = entity_present
        self._doc_types = doc_types or []
        self._confidence = confidence
        self._doc_count = doc_count

    def get_entity(self, name):
        if not self._entity_present:
            return None
        return type("E", (), {"confidence_score": self._confidence})()

    def get_entity_document_types(self, name):
        return list(self._doc_types)

    def get_high_yield_domains(self, limit=5):
        return [FakeDomain("example.com")]

    def get_entity_document_count(self, name):
        return self._doc_count


def test_gaps_cli_entity_missing(monkeypatch):
    runner = CliRunner()

    def fake_map(db):
        return FakeMapForCLI(entity_present=False)

    monkeypatch.setattr("cli.Map", fake_map)

    res = runner.invoke(cli, ["gaps", "missing-entity"])
    assert res.exit_code == 0
    assert "not found" in res.output
    assert "Would need" in res.output


def test_gaps_cli_shows_missing_types_and_domains(monkeypatch):
    runner = CliRunner()

    def fake_map(db):
        return FakeMapForCLI(entity_present=True, doc_types=["manual"], confidence=0.8, doc_count=2)

    monkeypatch.setattr("cli.Map", fake_map)

    res = runner.invoke(cli, ["gaps", "exists", "--types", "manual,datasheet"])
    assert res.exit_code == 0
    assert "Gap Analysis: exists" in res.output
    assert "Missing Document Types" in res.output
    assert "datasheet" in res.output
    assert "Suggested Sources" in res.output


def test_gaps_cli_json_output(monkeypatch):
    runner = CliRunner()

    def fake_map(db):
        return FakeMapForCLI(entity_present=True, doc_types=["manual"], confidence=0.6, doc_count=1)

    monkeypatch.setattr("cli.Map", fake_map)

    res = runner.invoke(cli, ["gaps", "exists", "--json", "--types", "manual,datasheet"])
    assert res.exit_code == 0

    parsed = json.loads(res.output)
    assert parsed["entity"] == "exists"
    assert parsed["missing_types"] == ["datasheet"]
