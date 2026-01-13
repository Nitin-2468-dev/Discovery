"""Development helper: run a small reproducible scenario to exercise GapDetector and get_domains_with_doc_type.

Moved to `scripts/debug/` and intended for local debugging only.
"""

from datetime import datetime, timedelta, timezone

from probe.analysis.gaps import GapDetector
from probe.core.map import Document, Edge, Entity, Map

if __name__ == "__main__":
    db = "tmp_probe.db"
    m = Map(db)
    # Add entity and a manual doc
    m.conn.execute("DELETE FROM domains")
    m.conn.execute("DELETE FROM documents")
    m.conn.execute("DELETE FROM entities")
    m.conn.commit()

    e = Entity(id=None, name="E1", type="device", confidence_score=0.6)
    e_id = m.add_entity(e)

    # manual document
    from probe.core.map import Document

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

    # add domains
    now = datetime.now(timezone.utc).isoformat()
    old = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()

    m.conn.execute(
        "INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("low.example.com", 10, 1, 0.1, 0.2, old),
    )
    m.conn.execute(
        "INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("high.example.com", 10, 5, 0.9, 0.9, now),
    )

    # add datasheet docs on high domain for suggestion
    from probe.core.map import Document

    d2 = Document(
        id=None,
        title="H1",
        doc_type="datasheet",
        hash="h2",
        url="https://high/1.pdf",
        domain="high.example.com",
    )
    m.add_document(d2)

    m.conn.commit()

    print(
        "get_domains_with_doc_type(datasheet):",
        [d.domain_name for d in m.get_domains_with_doc_type("datasheet")],
    )

    gd = GapDetector(m)
    out = gd.analyze_entity_gaps("E1", ["manual", "datasheet"], include_scores=True)
    print("out:", out)

    m.close()
