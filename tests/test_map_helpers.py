from probe.core.map import Document, Edge, Entity, Map


def test_get_entity_document_types_and_count(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    e = Entity(id=None, name="PT6A-52", type="engine")
    e_id = m.add_entity(e)

    d1 = Document(
        id=None,
        title="Manual",
        doc_type="manual",
        hash="h1",
        url="https://ex/a.pdf",
        domain="ex.com",
    )
    d2 = Document(
        id=None,
        title="Spec",
        doc_type="spec",
        hash="h2",
        url="https://ex/b.pdf",
        domain="ex.com",
    )
    id1 = m.add_document(d1)
    id2 = m.add_document(d2)

    # Link documents to entity
    m.add_edge(
        Edge(
            id=None,
            from_type="entity",
            from_id=e_id,
            to_type="document",
            to_id=id1,
            relation="has_document",
        )
    )
    m.add_edge(
        Edge(
            id=None,
            from_type="entity",
            from_id=e_id,
            to_type="document",
            to_id=id2,
            relation="has_document",
        )
    )

    types = m.get_entity_document_types("PT6A-52")
    assert set(types) == {"manual", "spec"}

    count_all = m.get_entity_document_count("PT6A-52")
    assert count_all == 2

    count_manual = m.get_entity_document_count("PT6A-52", doc_type="manual")
    assert count_manual == 1

    m.close()
