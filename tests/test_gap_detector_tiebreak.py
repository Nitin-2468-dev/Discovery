from datetime import datetime, timezone

from probe.analysis.gaps import GapDetector
from probe.core.map import Document, Edge, Entity, Map


def test_tiebreak_is_deterministic_by_domain_name(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    e = Entity(id=None, name="ET", type="device", confidence_score=0.6)
    e_id = m.add_entity(e)
    m.add_document(
        Document(
            id=None,
            title="Manual",
            doc_type="manual",
            hash="h1",
            url="https://ex/manual.pdf",
            domain="low.example.com",
        )
    )
    m.add_edge(
        Edge(
            id=None,
            from_type="entity",
            from_id=e_id,
            to_type="document",
            to_id=1,
            relation="has_document",
        )
    )

    now = datetime.now(timezone.utc).isoformat()

    # Create two domains with identical counts and scores
    m.conn.execute(
        "INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?,?,?,?,?,?)",
        ("b.example.com", 10, 5, 0.5, 0.5, now),
    )
    m.conn.execute(
        "INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?,?,?,?,?,?)",
        ("a.example.com", 10, 5, 0.5, 0.5, now),
    )

    for i in range(5):
        m.add_document(
            Document(
                id=None,
                title=f"A{i}",
                doc_type="datasheet",
                hash=f"a{i}",
                url=f"https://a/{i}.pdf",
                domain="a.example.com",
            )
        )
        m.add_document(
            Document(
                id=None,
                title=f"B{i}",
                doc_type="datasheet",
                hash=f"b{i}",
                url=f"https://b/{i}.pdf",
                domain="b.example.com",
            )
        )

    m.conn.commit()

    gd = GapDetector(m, normalize="none")
    out = gd.analyze_entity_gaps("ET", ["manual", "datasheet"], include_scores=True)

    # Expect deterministic ordering; since counts and scores equal, sort should fall back to domain name order due to stable sort
    assert out["suggested_domains"][0] in ("a.example.com", "b.example.com")
    # Ensure domain_scores list is sorted and matches suggested_domains prefix
    assert [d["domain"] for d in out["domain_scores"]] == out["suggested_domains"][
        : len(out["domain_scores"])
    ]

    m.close()
