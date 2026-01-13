import types
from probe.core.map import Map, Entity, Document, Edge
from probe.analysis.gaps import GapDetector


def test_integration_suggests_domain_based_on_docs_and_stats(tmp_path):
    db = tmp_path / "test.db"
    m = Map(str(db))

    # Create entity
    entity = Entity(id=None, name="ACME-PT6A", type="engine", confidence_score=0.6)
    eid = m.add_entity(entity)

    # Domain setup: low and high
    # Add documents and update domain stats to create different yield scores
    doc1 = Document(id=None, title="Doc1", doc_type="datasheet", hash="h1", url="https://low.example.com/d1", domain="low.example.com")
    dlow_id = m.add_document(doc1)
    m.add_edge(Edge(id=None, from_type="entity", from_id=eid, to_type="document", to_id=dlow_id, relation="has_document", confidence=1.0))
    # low has many pages crawled but low document yield
    for _ in range(10):
        m.update_domain_stats("low.example.com", found_document=False)

    # high domain
    doc2 = Document(id=None, title="Doc2", doc_type="manual", hash="h2", url="https://high.example.com/d2", domain="high.example.com")
    dhigh_id = m.add_document(doc2)
    m.add_edge(Edge(id=None, from_type="entity", from_id=eid, to_type="document", to_id=dhigh_id, relation="has_document", confidence=1.0))
    # high has fewer pages but more documents found
    for _ in range(2):
        m.update_domain_stats("high.example.com", found_document=True)

    # Missing desired type is 'datasheet' and 'manual' both present, but assume missing 'spec'
    gd = GapDetector(m)

    out = gd.analyze_entity_gaps("ACME-PT6A", ["manual", "datasheet", "spec"]) 

    # suggested domains should include 'high.example.com' (better yield/trust)
    assert isinstance(out.get("suggested_domains"), list)
    assert "high.example.com" in out.get("suggested_domains")

    m.close()