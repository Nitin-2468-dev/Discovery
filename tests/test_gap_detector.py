import types

import pytest

from probe.analysis.gaps import GapDetector


class FakeDomain:
    def __init__(self, domain_name):
        self.domain_name = domain_name


class FakeDoc:
    def __init__(self, doc_type):
        self.doc_type = doc_type


class FakeMap:
    def __init__(self, entity_present=True, doc_types=None, confidence=0.0, doc_count=0):
        self._entity_present = entity_present
        self._doc_types = doc_types or []
        self._confidence = confidence
        self._doc_count = doc_count

    def get_entity(self, name):
        if not self._entity_present:
            return None
        return types.SimpleNamespace(confidence_score=self._confidence)

    def get_entity_document_types(self, name):
        return list(self._doc_types)

    def get_high_yield_domains(self, limit=5):
        return [FakeDomain(f"example{i}.com") for i in range(min(limit, 3))]

    def get_entity_document_count(self, name):
        return self._doc_count

    def get_entity_documents(self, name):
        return [FakeDoc(t) for t in self._doc_types]


def test_analyze_entity_gaps_entity_missing():
    m = FakeMap(entity_present=False)
    gd = GapDetector(m)

    out = gd.analyze_entity_gaps("missing-entity", ["manual", "datasheet"])

    assert out["entity"] == "missing-entity"
    assert out["exists"] is False
    assert out["confidence"] == 0.0
    assert out["missing_types"] == ["manual", "datasheet"]
    assert out["has_documents"] == 0
    assert out["weak_confidence"] is True
    assert out["suggested_domains"] == []


def test_analyze_entity_gaps_detects_missing_types_and_confidence():
    m = FakeMap(entity_present=True, doc_types=["manual"], confidence=0.85, doc_count=3)
    gd = GapDetector(m)

    out = gd.analyze_entity_gaps("exists", ["manual", "datasheet"])

    assert out["entity"] == "exists"
    assert out["exists"] is True
    assert out["confidence"] == pytest.approx(0.85)
    assert out["missing_types"] == ["datasheet"]
    assert out["has_documents"] == 3
    assert out["weak_confidence"] is False
    assert out["suggested_domains"] == ["example0.com", "example1.com", "example2.com"]


def test_analyze_entity_gaps_fallback_to_documents():
    # Simulate an older Map implementation that only provides get_entity_documents
    class PartialMapNoTypes(FakeMap):
        def __init__(self):
            super().__init__(entity_present=True, doc_types=["report"], confidence=0.5, doc_count=1)

        # intentionally do NOT implement get_entity_document_types

    m = PartialMapNoTypes()
    gd = GapDetector(m)

    out = gd.analyze_entity_gaps("exists", ["report", "datasheet"])

    assert out["missing_types"] == ["datasheet"]
    assert out["weak_confidence"] is True
