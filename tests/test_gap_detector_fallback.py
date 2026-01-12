from datetime import datetime, timedelta
from probe.core.map import Map, Entity, Document, Edge
from probe.analysis.gaps import GapDetector


def test_gap_detector_falls_back_to_high_yield_domains_when_domain_lookup_empty(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    # Create an entity and link a "manual" document
    e = Entity(id=None, name="E1", type="device", confidence_score=0.6)
    e_id = m.add_entity(e)
    d = Document(id=None, title="Manual", doc_type="manual", hash="h1", url="https://ex/manual.pdf", domain="low.example.com")
    d_id = m.add_document(d)
    m.add_edge(Edge(id=None, from_type="entity", from_id=e_id, to_type="document", to_id=d_id, relation="has_document"))

    # Add two domains with different yields/trusts and recency
    now = datetime.utcnow().isoformat()
    old = (datetime.utcnow() - timedelta(days=60)).isoformat()

    m.conn.execute("INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?, ?, ?, ?, ?, ?)", ("low.example.com", 10, 1, 0.1, 0.2, old))
    m.conn.execute("INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?, ?, ?, ?, ?, ?)", ("high.example.com", 10, 5, 0.9, 0.9, now))

    # Add a datasheet document on the high domain (not linked to entity)
    d2 = Document(id=None, title="H1", doc_type="datasheet", hash="h2", url="https://high/1.pdf", domain="high.example.com")
    m.add_document(d2)

    m.conn.commit()

    # Force the domain-specific lookup to return no candidates to trigger fallback
    m.get_domains_with_doc_type = lambda doc_type, limit=8: []

    gd = GapDetector(m)
    out = gd.analyze_entity_gaps("E1", ["manual", "datasheet"])  # datasheet is missing

    assert "datasheet" in out["missing_types"]
    # Fallback should produce suggestions based on high-yield domains
    assert isinstance(out.get("suggested_domains"), list)
    assert "high.example.com" in out.get("suggested_domains")

    m.close()
