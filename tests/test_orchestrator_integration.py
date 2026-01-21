from probe.analysis.gaps import GapDetector
from probe.analysis.seed_generator import SeedGenerator
from probe.core.map import Document, Map
from probe.orchestrator import Orchestrator


def fake_fetch(url):
    # Return a simple HTML page; include no links so crawl is bounded
    return {
        "url": url,
        "status_code": 200,
        "text": "page",
        "links": [],
        "content_type": "text/html",
    }


def test_orchestrator_integration(tmp_path):
    db = str(tmp_path / "orch.db")
    m = Map(db)

    # Seed the map with a document for drivers on drivers.example.com so GapDetector can suggest it
    doc = Document(
        id=None,
        title="RTL8111 Datasheet",
        doc_type="driver",
        hash="h1",
        url="https://drivers.example.com/rtl8111.pdf",
        domain="drivers.example.com",
    )
    m.add_document(doc)

    gd = GapDetector(m)
    sg = SeedGenerator(m, fetch_remote=False)

    orc = Orchestrator(map_obj=m, fetch_fn=fake_fetch, scorer_fn=lambda r: 1.0)

    res = orc.orchestrate_gap_seed(
        entity_name="rtl8111",
        desired_doc_types=["driver"],
        gap_detector=gd,
        seed_generator=sg,
        max_seeds=10,
        max_depth=1,
        max_pages=10,
    )

    # Ensure we produced seeds, crawl ran, and pages were persisted
    assert "seeds" in res and res["seeds"]
    assert res["crawl_result"]["pages_fetched"] >= 1

    # Check pages present for suggested domain
    pages = m.conn.execute(
        "SELECT url FROM pages WHERE domain = ?", ("drivers.example.com",)
    ).fetchall()
    assert pages and len(pages) >= 1

    # Check domain stats updated
    d = m.get_domain("drivers.example.com")
    assert d is not None
    assert d.pages_crawled >= 1

    m.close()
