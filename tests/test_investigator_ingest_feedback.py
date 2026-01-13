from datetime import datetime, timezone
from probe.core.map import Map, Entity, Document, Edge
from probe.analysis.investigator import Investigator


def test_investigator_ingest_increments_domain_docs(tmp_path, monkeypatch):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    # Create entity with manual doc
    e = Entity(id=None, name="E1", type="device", confidence_score=0.6)
    e_id = m.add_entity(e)
    m.add_document(Document(id=None, title="Manual", doc_type="manual", hash="h1", url="https://ex/manual.pdf", domain="low.example.com"))
    m.add_edge(Edge(id=None, from_type="entity", from_id=e_id, to_type="document", to_id=1, relation="has_document"))

    now = datetime.now(timezone.utc).isoformat()
    # Add a domain with some datasheets
    m.conn.execute("INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?,?,?,?,?,?)", ("high.example.com", 10, 0, 0.9, 0.9, now))
    for i in range(3):
        m.add_document(Document(id=None, title=f"H{i}", doc_type="datasheet", hash=f"h{i}", url=f"https://high/{i}.pdf", domain="high.example.com"))
    m.conn.commit()

    # Check initial documents_found
    dom_before = m.get_domain("high.example.com")
    before = dom_before.documents_found

    # Monkeypatch fetch and ingest to avoid network
    def fake_fetch(url, timeout, max_retries, backoff_factor):
        return {"status_code": 200, "error": None}

    def fake_ingest(map_obj, fetch_result):
        return {"document_id": 123, "edges_created": 1, "outgoing_links": []}

    monkeypatch.setattr('probe.crawl.fetcher.fetch', fake_fetch)
    monkeypatch.setattr('probe.crawl.ingest.ingest_fetch_result', fake_ingest)

    inv = Investigator(m, ingest_on_fetch=True)
    # limit to 1 seed so we increment documents_found by exactly 1
    res = inv.investigate("E1", ["manual", "datasheet"], max_seeds=1, dry_run=False)

    dom_after = m.get_domain("high.example.com")
    assert dom_after.documents_found == before + 1

    m.close()
