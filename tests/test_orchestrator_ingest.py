from probe.core.map import Map
from probe.orchestrator import Orchestrator


def test_orchestrator_persists_findings(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    def fake_fetch(url):
        # single pdf page
        return {"status_code": 200, "content_type": "application/pdf", "links": []}

    def fake_score(page):
        return 1.0

    orch = Orchestrator(m, fake_fetch, fake_score)

    orch.run(["http://example.com/manual.pdf"], max_depth=0, max_pages=5)

    # Orchestrator should have persisted at least one page and one document
    summary = m.get_map_summary()
    assert summary["pages"] >= 1
    assert summary["documents"] >= 1

    d = m.get_domain("example.com")
    assert d is not None
    assert d.documents_found >= 1
