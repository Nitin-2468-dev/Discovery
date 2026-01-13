import pytest
from probe.core.map import Map, Entity, Document, Edge
from probe.analysis.gaps import GapDetector
from datetime import datetime, timedelta, timezone


def test_gap_detector_with_real_map(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    # Add entity and a "manual" doc
    e = Entity(id=None, name="E1", type="device", confidence_score=0.6)
    e_id = m.add_entity(e)
    d = Document(id=None, title="Manual", doc_type="manual", hash="h1", url="https://ex/manual.pdf", domain="low.example.com")
    d_id = m.add_document(d)
    # Link doc to entity
    m.add_edge(Edge(id=None, from_type="entity", from_id=e_id, to_type="document", to_id=d_id, relation="has_document"))

    # Add two domains with different yields/trusts and recency
    now = datetime.now(timezone.utc).isoformat()
    old = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()

    m.conn.execute("INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?, ?, ?, ?, ?, ?)", ("low.example.com", 10, 1, 0.1, 0.2, old))
    m.conn.execute("INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?, ?, ?, ?, ?, ?)", ("high.example.com", 10, 5, 0.9, 0.9, now))
    m.conn.commit()

    gd = GapDetector(m)
    out = gd.analyze_entity_gaps("E1", ["manual", "datasheet"], include_scores=True)

    # missing types should include datasheet
    assert "datasheet" in out["missing_types"]
    # should have a domain_scores list
    assert "domain_scores" in out
    # top suggested domain should be high.example.com due to higher yield/trust/recency
    assert out["suggested_domains"][0] == "high.example.com"

    m.close()
