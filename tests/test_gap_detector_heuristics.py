from datetime import datetime, timedelta, timezone

from probe.analysis.gaps import GapDetector
from probe.core.map import Document, Edge, Entity, Map


def setup_two_domain_scenario(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    # Create entity and link a "manual" document
    e = Entity(id=None, name="E1", type="device", confidence_score=0.6)
    e_id = m.add_entity(e)
    d = Document(
        id=None,
        title="Manual",
        doc_type="manual",
        hash="h1",
        url="https://ex/manual.pdf",
        domain="low.example.com",
    )
    d_id = m.add_document(d)
    m.add_edge(
        Edge(
            id=None,
            from_type="entity",
            from_id=e_id,
            to_type="document",
            to_id=d_id,
            relation="has_document",
        )
    )

    # Setup timestamps
    now = datetime.now(timezone.utc).isoformat()
    old = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()

    # Domain A: higher count, lower yield
    m.conn.execute(
        "INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("a.example.com", 20, 5, 0.2, 0.5, old),
    )
    # Add two datasheets to domain A
    m.add_document(
        Document(
            id=None,
            title="A1",
            doc_type="datasheet",
            hash="ad1",
            url="https://a/1.pdf",
            domain="a.example.com",
        )
    )
    m.add_document(
        Document(
            id=None,
            title="A2",
            doc_type="datasheet",
            hash="ad2",
            url="https://a/2.pdf",
            domain="a.example.com",
        )
    )

    # Domain B: lower count, higher yield + recency
    m.conn.execute(
        "INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("b.example.com", 5, 3, 0.95, 0.9, now),
    )
    # Add one datasheet to domain B
    m.add_document(
        Document(
            id=None,
            title="B1",
            doc_type="datasheet",
            hash="bd1",
            url="https://b/1.pdf",
            domain="b.example.com",
        )
    )

    m.conn.commit()
    return m


def test_weight_configuration_changes_ordering(tmp_path):
    m = setup_two_domain_scenario(tmp_path)

    # Default weights: count dominates, so a.example.com should be top
    gd_default = GapDetector(m)
    out_default = gd_default.analyze_entity_gaps("E1", ["manual", "datasheet"])
    assert out_default["suggested_domains"][0] == "a.example.com"

    # Strongly prefer yield over count
    gd_yield = GapDetector(
        m, weights={"count": 0.2, "yield": 3.0, "trust": 0.5, "recent": 1.0}
    )
    out_yield = gd_yield.analyze_entity_gaps("E1", ["manual", "datasheet"])
    assert out_yield["suggested_domains"][0] == "b.example.com"

    m.close()


def test_include_scores_details_components(tmp_path):
    m = setup_two_domain_scenario(tmp_path)
    gd = GapDetector(m)
    out = gd.analyze_entity_gaps("E1", ["manual", "datasheet"], include_scores=True)

    assert "domain_scores" in out and isinstance(out["domain_scores"], list)
    # ensure scores contain component fields and composite_score
    for d in out["domain_scores"]:
        assert {
            "domain",
            "count",
            "yield_score",
            "trust_score",
            "recent_score",
            "composite_score",
        } <= set(d.keys())

    # the ordering of domain_scores should correspond to suggested_domains order
    ordered_domains = [d["domain"] for d in out["domain_scores"]]
    assert ordered_domains == out["suggested_domains"][: len(ordered_domains)]

    m.close()
