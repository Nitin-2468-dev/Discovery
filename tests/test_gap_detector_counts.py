from probe.core.map import Map, Entity, Document, Edge
from probe.analysis.gaps import GapDetector


def test_counts_accumulate_across_missing_types(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    e = Entity(id=None, name="EC", type="device", confidence_score=0.6)
    e_id = m.add_entity(e)
    m.add_document(Document(id=None, title="Manual", doc_type="manual", hash="h1", url="https://ex/manual.pdf", domain="low.example.com"))
    m.add_edge(Edge(id=None, from_type="entity", from_id=e_id, to_type="document", to_id=1, relation="has_document"))

    # Domain D1 has 3 datasheets and 2 reports -> total count for missing types should be 5
    for i in range(3):
        m.add_document(Document(id=None, title=f"D1_ds_{i}", doc_type="datasheet", hash=f"d1ds{i}", url=f"https://d1/ds/{i}.pdf", domain="d1.example.com"))
    for i in range(2):
        m.add_document(Document(id=None, title=f"D1_r_{i}", doc_type="report", hash=f"d1r{i}", url=f"https://d1/report/{i}.pdf", domain="d1.example.com"))

    # Domain D2 has 1 datasheet
    m.add_document(Document(id=None, title="D2_ds", doc_type="datasheet", hash="d2ds0", url="https://d2/ds/0.pdf", domain="d2.example.com"))

    m.conn.commit()

    # Missing types: datasheet and report
    gd = GapDetector(m, normalize='none')
    out = gd.analyze_entity_gaps("EC", ["manual", "datasheet", "report"], include_scores=True)
    ds = {d['domain']: d for d in out['domain_scores']}

    assert ds['d1.example.com']['count'] == 5
    assert ds['d2.example.com']['count'] == 1

    m.close()
