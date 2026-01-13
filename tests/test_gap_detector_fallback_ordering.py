from datetime import datetime, timedelta, timezone
from probe.core.map import Map, Entity, Document, Edge
from probe.analysis.gaps import GapDetector


def test_fallback_prefers_high_yield_domain(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    # Entity with one manual doc
    e = Entity(id=None, name="E1", type="device", confidence_score=0.6)
    e_id = m.add_entity(e)
    d = Document(id=None, title="Manual", doc_type="manual", hash="h1", url="https://ex/manual.pdf", domain="low.example.com")
    d_id = m.add_document(d)
    m.add_edge(Edge(id=None, from_type="entity", from_id=e_id, to_type="document", to_id=d_id, relation="has_document"))

    # Domains: low (low yield) and high (high yield)
    now = datetime.now(timezone.utc).isoformat()
    old = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()

    m.conn.execute("INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?, ?, ?, ?, ?, ?)", ("low.example.com", 20, 2, 0.1, 0.3, old))
    m.conn.execute("INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?, ?, ?, ?, ?, ?)", ("high.example.com", 5, 3, 0.95, 0.9, now))

    # Add a datasheet to high domain to make it relevant
    d2 = Document(id=None, title="H1", doc_type="datasheet", hash="h2", url="https://high/1.pdf", domain="high.example.com")
    m.add_document(d2)
    m.conn.commit()

    # Force domain-specific lookup to return empty, to activate fallback
    m.get_domains_with_doc_type = lambda doc_type, limit=8: []

    gd = GapDetector(m)
    out = gd.analyze_entity_gaps("E1", ["manual", "datasheet"])  # datasheet missing

    assert isinstance(out.get("suggested_domains"), list)
    assert out["suggested_domains"], "No suggested domains returned"
    # Top suggestion should be the high-yield domain
    assert out["suggested_domains"][0] == "high.example.com"

    m.close()
