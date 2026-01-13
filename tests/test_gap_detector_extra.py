from datetime import datetime, timezone
from probe.core.map import Map, Entity, Document, Edge
from probe.analysis.gaps import GapDetector


def test_include_scores_returns_sorted_domain_scores(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    e = Entity(id=None, name="E-IS", type="device", confidence_score=0.6)
    e_id = m.add_entity(e)
    # Add a manual to mark existence of one type
    m.add_document(Document(id=None, title="Manual", doc_type="manual", hash="h1", url="https://ex/manual.pdf", domain="ex.example.com"))
    m.add_edge(Edge(id=None, from_type="entity", from_id=e_id, to_type="document", to_id=1, relation="has_document"))

    now = datetime.now(timezone.utc).isoformat()
    # Two domains with different characteristics
    m.conn.execute("INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?,?,?,?,?,?)", ("d1.example.com", 10, 50, 0.2, 0.4, now))
    m.conn.execute("INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?,?,?,?,?,?)", ("d2.example.com", 5, 10, 0.9, 0.9, now))
    for i in range(10):
        m.add_document(Document(id=None, title=f"D2-{i}", doc_type="datasheet", hash=f"d2{i}", url=f"https://d2/{i}.pdf", domain="d2.example.com"))
    for i in range(50):
        m.add_document(Document(id=None, title=f"D1-{i}", doc_type="datasheet", hash=f"d1{i}", url=f"https://d1/{i}.pdf", domain="d1.example.com"))
    m.conn.commit()

    gd = GapDetector(m, normalize='none')
    out = gd.analyze_entity_gaps("E-IS", ["manual", "datasheet"], include_scores=True)

    assert "domain_scores" in out and isinstance(out["domain_scores"], list)
    scores = [d['composite_score'] for d in out['domain_scores']]
    # ensure sorted descending
    assert scores == sorted(scores, reverse=True)
    m.close()


def test_get_entity_document_types_exception_falls_back(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    e = Entity(id=None, name="E-EX", type="device", confidence_score=0.6)
    e_id = m.add_entity(e)
    m.add_document(Document(id=None, title="Manual", doc_type="manual", hash="h1", url="https://ex/manual.pdf", domain="ex.example.com"))
    m.add_edge(Edge(id=None, from_type="entity", from_id=e_id, to_type="document", to_id=1, relation="has_document"))

    # Insert a candidate domain
    now = datetime.now(timezone.utc).isoformat()
    m.conn.execute("INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?,?,?,?,?,?)", ("c.example.com", 3, 5, 0.8, 0.8, now))
    for i in range(5):
        m.add_document(Document(id=None, title=f"C{i}", doc_type="datasheet", hash=f"cd{i}", url=f"https://c/{i}.pdf", domain="c.example.com"))
    m.conn.commit()

    # Monkeypatch get_entity_document_types to raise
    def raising_get_entity_document_types(name):
        raise RuntimeError("boom")

    m.get_entity_document_types = raising_get_entity_document_types

    gd = GapDetector(m, normalize='none')
    out = gd.analyze_entity_gaps("E-EX", ["manual", "datasheet"])

    # Should still return suggested domains despite the exception
    assert isinstance(out.get("suggested_domains"), list)
    assert out["suggested_domains"]
    m.close()


def test_malformed_last_crawled_does_not_raise_and_sets_recent_zero(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    e = Entity(id=None, name="E-MAL", type="device", confidence_score=0.6)
    e_id = m.add_entity(e)
    m.add_document(Document(id=None, title="Manual", doc_type="manual", hash="h1", url="https://ex/manual.pdf", domain="ex.example.com"))
    m.add_edge(Edge(id=None, from_type="entity", from_id=e_id, to_type="document", to_id=1, relation="has_document"))

    # Insert a domain with malformed last_crawled_at
    m.conn.execute("INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?,?,?,?,?,?)", ("m.example.com", 10, 10, 0.5, 0.5, "not-a-date"))
    for i in range(10):
        m.add_document(Document(id=None, title=f"M{i}", doc_type="datasheet", hash=f"md{i}", url=f"https://m/{i}.pdf", domain="m.example.com"))
    m.conn.commit()

    gd = GapDetector(m, normalize='none')
    out = gd.analyze_entity_gaps("E-MAL", ["manual", "datasheet"], include_scores=True)

    assert "domain_scores" in out
    ds = {d['domain']: d for d in out['domain_scores']}
    assert 'm.example.com' in ds
    assert ds['m.example.com']['recent_score'] == 0.0
    m.close()


def test_per_page_log_reduces_skew(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    e = Entity(id=None, name="E-PL", type="device", confidence_score=0.6)
    e_id = m.add_entity(e)
    m.add_document(Document(id=None, title="Manual", doc_type="manual", hash="h1", url="https://ex/manual.pdf", domain="ex.example.com"))
    m.add_edge(Edge(id=None, from_type="entity", from_id=e_id, to_type="document", to_id=1, relation="has_document"))

    now = datetime.now(timezone.utc).isoformat()
    # X has many docs but many pages
    m.conn.execute("INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?,?,?,?,?,?)", ("x.example.com", 100, 1000, 0.4, 0.4, now))
    for i in range(1000):
        m.add_document(Document(id=None, title=f"X{i}", doc_type="datasheet", hash=f"xd{i}", url=f"https://x/{i}.pdf", domain="x.example.com"))

    # Y has fewer docs and few pages, higher yield/trust
    m.conn.execute("INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?,?,?,?,?,?)", ("y.example.com", 5, 40, 0.9, 0.9, now))
    for i in range(40):
        m.add_document(Document(id=None, title=f"Y{i}", doc_type="datasheet", hash=f"yd{i}", url=f"https://y/{i}.pdf", domain="y.example.com"))
    m.conn.commit()

    gd_none = GapDetector(m, normalize='none', weights={"count": 2.0, "yield": 1.0, "trust": 0.5, "recent": 0.0})
    out_none = gd_none.analyze_entity_gaps("E-PL", ["manual", "datasheet"], include_scores=True)

    gd_per_page_log = GapDetector(m, normalize='per_page_log', weights={"count": 2.0, "yield": 1.0, "trust": 2.0, "recent": 0.0})
    out_ppl = gd_per_page_log.analyze_entity_gaps("E-PL", ["manual", "datasheet"], include_scores=True)

    raw_scores = {d['domain']: d['composite_score'] for d in out_none['domain_scores']}
    ppl_scores = {d['domain']: d['composite_score'] for d in out_ppl['domain_scores']}

    gap_raw = raw_scores.get('x.example.com', 0.0) - raw_scores.get('y.example.com', 0.0)
    gap_ppl = ppl_scores.get('x.example.com', 0.0) - ppl_scores.get('y.example.com', 0.0)

    assert gap_ppl < gap_raw
    m.close()
