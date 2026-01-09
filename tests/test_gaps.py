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


def test_gap_entity_not_found(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    detector = GapDetector(m)
    res = detector.analyze_entity_gaps("UNKNOWN-1", ["manual", "spec"])

    assert not res["exists"]
    assert res["missing_types"] == ["manual", "spec"]

    m.close()


def test_weak_confidence_and_suggested_domains(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    # Create entity with low confidence
    ent = Entity(id=None, name="A-1", confidence_score=0.2)
    ent_id = m.add_entity(ent)

    # Add some domain stats so suggested_domains returns results
    for _ in range(4):
        m.update_domain_stats("highyield.example", found_document=True)
    for _ in range(3):
        m.update_domain_stats("other.example", found_document=False)

    detector = GapDetector(m)
    res = detector.analyze_entity_gaps("A-1", ["manual"])

    assert res["exists"]
    assert res["weak_confidence"] is True
    # suggested_domains should include at least 'highyield.example'
    assert any("highyield.example" in d for d in res["suggested_domains"])

    m.close()


def test_gaps_cli_output_and_json(tmp_path, monkeypatch):
    from click.testing import CliRunner
    runner = CliRunner()

    db = str(tmp_path / "probe.db")
    m = Map(db)

    # Add an entity and document
    ent = Entity(id=None, name="CLI-1", confidence_score=0.9)
    ent_id = m.add_entity(ent)

    doc = Document(
        id=None,
        title="Spec",
        doc_type="spec",
        hash="h2",
        url="https://example.com/spec.pdf",
        domain="example.com",
    )
    doc_id = m.add_document(doc)
    edge = Edge(id=None, from_type="entity", from_id=ent_id, to_type="document", to_id=doc_id, relation="mentions")
    m.add_edge(edge)

    # Run CLI command in plain text
    from cli import cli
    result = runner.invoke(cli, ["gaps", "CLI-1", "--db", db])
    assert result.exit_code == 0
    assert "Gap Analysis: CLI-1" in result.output

    # Run CLI command with JSON output
    result_json = runner.invoke(cli, ["gaps", "CLI-1", "--db", db, "--json"])
    assert result_json.exit_code == 0
    import json
    parsed = json.loads(result_json.output)
    assert parsed.get("entity") == "CLI-1"

    m.close()