from probe.core.map import Map, Entity, Document, Edge
from probe.analysis.gaps import GapDetector


def test_gap_detection_missing_types(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    # Add entity with only one document type
    ent = Entity(id=None, name="PT6A-52")
    ent_id = m.add_entity(ent)

    doc = Document(
        id=None,
        title="Manual",
        doc_type="manual",
        hash="h1",
        url="https://example.com/manual.pdf",
        domain="example.com",
    )
    doc_id = m.add_document(doc)

    edge = Edge(
        id=None,
        from_type="entity",
        from_id=ent_id,
        to_type="document",
        to_id=doc_id,
        relation="mentions",
    )
    m.add_edge(edge)

    # Analyze gaps
    detector = GapDetector(m)
    result = detector.analyze_entity_gaps("PT6A-52", ["manual", "bulletin", "spec"])

    assert result["exists"]
    assert "bulletin" in result["missing_types"]
    assert "spec" in result["missing_types"]
    assert "manual" not in result["missing_types"]

    m.close()
