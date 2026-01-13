from datetime import datetime, timedelta, timezone
from probe.core.map import Map, Entity, Document, Edge
from probe.analysis.gaps import GapDetector


def test_recency_clamp_future_and_old(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    e = Entity(id=None, name="ER", type="device", confidence_score=0.6)
    e_id = m.add_entity(e)
    m.add_document(Document(id=None, title="Manual", doc_type="manual", hash="h1", url="https://ex/manual.pdf", domain="low.example.com"))
    m.add_edge(Edge(id=None, from_type="entity", from_id=e_id, to_type="document", to_id=1, relation="has_document"))

    # Future date (now + 5 days) should clamp recent_score to 1.0
    future = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    m.conn.execute("INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?,?,?,?,?,?)", ("future.example.com", 10, 1, 0.5, 0.5, future))

    # Old date (now - 365 days) should give recent_score 0.0
    old = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()
    m.conn.execute("INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?,?,?,?,?,?)", ("old.example.com", 10, 1, 0.5, 0.5, old))

    m.conn.commit()

    gd = GapDetector(m)
    out = gd.analyze_entity_gaps("ER", ["manual", "datasheet"], include_scores=True)
    ds = {d['domain']: d for d in out['domain_scores']}

    assert ds['future.example.com']['recent_score'] == 1.0
    assert ds['old.example.com']['recent_score'] == 0.0

    m.close()
