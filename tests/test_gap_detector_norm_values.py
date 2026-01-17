from datetime import datetime, timezone
from math import isclose

from probe.analysis.gaps import GapDetector
from probe.core.map import Document, Edge, Entity, Map


def insert_domain(
    m, domain_name, pages, docs, yield_score=0.5, trust_score=0.5, last=None
):
    last = last or datetime.now(timezone.utc).isoformat()
    m.conn.execute(
        "INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?,?,?,?,?,?)",
        (domain_name, pages, docs, yield_score, trust_score, last),
    )


def test_normalized_count_values(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    # Entity and manual doc
    e = Entity(id=None, name="EN", type="device", confidence_score=0.6)
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

    # Setup: domain A: pages=10, count=100; domain B: pages=1, count=10
    insert_domain(m, "a.example.com", 10, 100)
    for i in range(100):
        m.add_document(
            Document(
                id=None,
                title=f"A{i}",
                doc_type="datasheet",
                hash=f"ad{i}",
                url=f"https://a/{i}.pdf",
                domain="a.example.com",
            )
        )

    insert_domain(m, "b.example.com", 1, 10)
    for i in range(10):
        m.add_document(
            Document(
                id=None,
                title=f"B{i}",
                doc_type="datasheet",
                hash=f"bd{i}",
                url=f"https://b/{i}.pdf",
                domain="b.example.com",
            )
        )

    m.conn.commit()

    # None: normalized_count should equal raw count
    gd_none = GapDetector(m, normalize="none")
    out_none = gd_none.analyze_entity_gaps(
        "EN", ["manual", "datasheet"], include_scores=True
    )
    ds_none = {d["domain"]: d for d in out_none["domain_scores"]}
    assert ds_none["a.example.com"]["normalized_count"] == 100.0
    assert ds_none["b.example.com"]["normalized_count"] == 10.0

    # per_page: normalized_count should be count / pages (max(1,pages) enforced)
    gd_per = GapDetector(m, normalize="per_page")
    out_per = gd_per.analyze_entity_gaps(
        "EN", ["manual", "datasheet"], include_scores=True
    )
    ds_per = {d["domain"]: d for d in out_per["domain_scores"]}
    assert isclose(ds_per["a.example.com"]["normalized_count"], 100.0 / 10.0)
    assert isclose(ds_per["b.example.com"]["normalized_count"], 10.0 / 1.0)

    # log: normalized_count should be log1p(count)
    import math

    gd_log = GapDetector(m, normalize="log")
    out_log = gd_log.analyze_entity_gaps(
        "EN", ["manual", "datasheet"], include_scores=True
    )
    ds_log = {d["domain"]: d for d in out_log["domain_scores"]}
    assert isclose(ds_log["a.example.com"]["normalized_count"], math.log1p(100.0))
    assert isclose(ds_log["b.example.com"]["normalized_count"], math.log1p(10.0))

    # per_page_log: apply per_page then log1p
    gd_ppl = GapDetector(m, normalize="per_page_log")
    out_ppl = gd_ppl.analyze_entity_gaps(
        "EN", ["manual", "datasheet"], include_scores=True
    )
    ds_ppl = {d["domain"]: d for d in out_ppl["domain_scores"]}
    assert isclose(
        ds_ppl["a.example.com"]["normalized_count"], math.log1p(100.0 / 10.0)
    )
    assert isclose(ds_ppl["b.example.com"]["normalized_count"], math.log1p(10.0 / 1.0))

    m.close()
