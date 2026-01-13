from datetime import datetime, timezone
from probe.core.map import Map, Entity, Document, Edge
from probe.analysis.gaps import GapDetector


def test_normalization_per_page_prefers_low_pages_high_density(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    # Entity
    e = Entity(id=None, name="E1", type="device", confidence_score=0.6)
    e_id = m.add_entity(e)
    d = Document(id=None, title="Manual", doc_type="manual", hash="h1", url="https://ex/manual.pdf", domain="low.example.com")
    m.add_document(d)
    m.add_edge(Edge(id=None, from_type="entity", from_id=e_id, to_type="document", to_id=1, relation="has_document"))

    now = datetime.now(timezone.utc).isoformat()
    # Domain A: many docs but many pages => lower per-page density
    m.conn.execute("INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?,?,?,?,?,?)", ("a.example.com", 200, 100, 0.2, 0.5, now))
    for i in range(100):
        m.add_document(Document(id=None, title=f"A{i}", doc_type="datasheet", hash=f"ad{i}", url=f"https://a/{i}.pdf", domain="a.example.com"))

    # Domain B: fewer docs but few pages => higher per-page density
    m.conn.execute("INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?,?,?,?,?,?)", ("b.example.com", 2, 5, 0.9, 0.9, now))
    for i in range(5):
        m.add_document(Document(id=None, title=f"B{i}", doc_type="datasheet", hash=f"bd{i}", url=f"https://b/{i}.pdf", domain="b.example.com"))

    m.conn.commit()

    # Force domain-specific lookup not to be used (simulate empty) so fallback uses get_high_yield or candidates built
    # Here we exercise the normal flow that reads document counts; use default behavior
    gd = GapDetector(m, normalize='per_page')
    out = gd.analyze_entity_gaps("E1", ["manual", "datasheet"])  # datasheet missing

    assert isinstance(out.get("suggested_domains"), list)
    assert out["suggested_domains"], "No suggested domains returned"
    # Top suggestion should be b.example.com due to per-page normalization favoring higher density
    assert out["suggested_domains"][0] == "b.example.com"

    m.close()


def test_normalization_log_reduces_skew(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    # Entity and manual doc
    e = Entity(id=None, name="E2", type="device", confidence_score=0.6)
    e_id = m.add_entity(e)
    d = Document(id=None, title="Manual", doc_type="manual", hash="h1", url="https://ex/manual.pdf", domain="low.example.com")
    m.add_document(d)
    m.add_edge(Edge(id=None, from_type="entity", from_id=e_id, to_type="document", to_id=1, relation="has_document"))

    now = datetime.now(timezone.utc).isoformat()
    # Domain X: huge number of datasheets
    m.conn.execute("INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?,?,?,?,?,?)", ("x.example.com", 10, 1000, 0.4, 0.4, now))
    for i in range(1000):
        m.add_document(Document(id=None, title=f"X{i}", doc_type="datasheet", hash=f"xd{i}", url=f"https://x/{i}.pdf", domain="x.example.com"))

    # Domain Y: moderate number of datasheets but higher yield/trust
    m.conn.execute("INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?,?,?,?,?,?)", ("y.example.com", 10, 40, 0.9, 0.9, now))
    for i in range(40):
        m.add_document(Document(id=None, title=f"Y{i}", doc_type="datasheet", hash=f"yd{i}", url=f"https://y/{i}.pdf", domain="y.example.com"))

    m.conn.commit()

    # With raw counts, x.example.com likely wins; with log normalization, the gap is reduced and yield/trust can push y to top
    gd_raw = GapDetector(m, normalize='none', weights={"count": 2.0, "yield": 1.0, "trust": 0.5, "recent": 0.5})
    out_raw = gd_raw.analyze_entity_gaps("E2", ["manual", "datasheet"], include_scores=True)

    gd_log = GapDetector(m, normalize='log', weights={"count": 2.0, "yield": 1.0, "trust": 2.0, "recent": 0.5})
    out_log = gd_log.analyze_entity_gaps("E2", ["manual", "datasheet"], include_scores=True)

    assert out_raw["suggested_domains"][0] == "x.example.com"
    # With log normalization and stronger trust weight the advantage of X should shrink; ensure the score gap reduces
    assert "domain_scores" in out_raw and "domain_scores" in out_log
    raw_scores = {d["domain"]: d["composite_score"] for d in out_raw["domain_scores"]}
    log_scores = {d["domain"]: d["composite_score"] for d in out_log["domain_scores"]}
    gap_raw = raw_scores.get("x.example.com", 0.0) - raw_scores.get("y.example.com", 0.0)
    gap_log = log_scores.get("x.example.com", 0.0) - log_scores.get("y.example.com", 0.0)
    assert gap_log < gap_raw, f"Expected log normalization to reduce score gap, got raw {gap_raw} vs log {gap_log}"

    m.close()
