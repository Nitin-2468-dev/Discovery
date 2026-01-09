from click.testing import CliRunner
from cli import cli
from probe.core.map import Map, Document, Edge, Entity
from pathlib import Path


def test_export_entity_md_and_csv(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    # create entity and document and link
    ent = Entity(id=None, name="PT6A-52")
    ent_id = m.add_entity(ent)

    doc = Document(id=None, title="Manual", doc_type="manual", hash="h1", url="https://example.com/manual.pdf", domain="example.com")
    doc_id = m.add_document(doc)

    edge = Edge(id=None, from_type="entity", from_id=ent_id, to_type="document", to_id=doc_id, relation="mentions")
    m.add_edge(edge)

    # add a scoring report for the doc URL
    comps = {'KeywordDensityScorer': 1.0}
    m.add_scoring_report(None, doc.url, 0.85, comps, {'source':'seed-run'})

    runner = CliRunner()
    md_out = tmp_path / 'out.md'
    res = runner.invoke(cli, ["export", "PT6A-52", "--format", "md", "--out", str(md_out), "--db", db])
    assert res.exit_code == 0
    assert md_out.exists()
    txt = md_out.read_text(encoding='utf-8')
    assert 'Manual' in txt
    assert '0.85' in txt

    csv_out = tmp_path / 'out.csv'
    res2 = runner.invoke(cli, ["export", "PT6A-52", "--format", "csv", "--out", str(csv_out), "--db", db])
    assert res2.exit_code == 0
    assert csv_out.exists()
    csv_txt = csv_out.read_text(encoding='utf-8')
    assert 'Manual' in csv_txt
    assert '0.85' in csv_txt

    m.close()