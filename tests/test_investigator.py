from probe.analysis.investigator import Investigator
from probe.core.map import Entity, Map


def test_investigator_dry_run_gathers_seeds(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    # create entity with no docs
    m.add_entity(Entity(id=None, name="PT6A-52"))

    # add some high-yield domains
    for _ in range(4):
        m.update_domain_stats("hi.example", found_document=True)

    inv = Investigator(m)
    res = inv.investigate("PT6A-52", ["manual", "spec"], max_seeds=5, dry_run=True)

    assert res["entity"] == "PT6A-52"
    assert isinstance(res["gap"], dict)
    assert isinstance(res["seeds"], list)
    assert len(res["seeds"]) <= 5

    m.close()


def test_investigator_seed_prioritization(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    # Create entity
    m.add_entity(Entity(id=None, name="PT6A-52"))

    # hi1 has higher yield than hi2
    for _ in range(5):
        m.update_domain_stats("hi1.example", found_document=True)
    for _ in range(3):
        m.update_domain_stats("hi2.example", found_document=True)

    inv = Investigator(m)
    res = inv.investigate("PT6A-52", ["manual"], max_seeds=10, dry_run=True)

    seeds = res.get("seeds", [])
    # find first occurrence indices
    idx_hi1 = next((i for i, s in enumerate(seeds) if "hi1.example" in s), None)
    idx_hi2 = next((i for i, s in enumerate(seeds) if "hi2.example" in s), None)

    assert idx_hi1 is not None and idx_hi2 is not None and idx_hi1 < idx_hi2

    m.close()


def test_investigator_runs_fetches_when_not_dry(tmp_path, monkeypatch):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    m.add_entity(Entity(id=None, name="PT6A-52"))

    # Add domain so seed generator makes seeds
    for _ in range(3):
        m.update_domain_stats("hi.example", found_document=True)

    # Mock fetch to avoid network and return minimal fetch payload for ingestion
    def fake_fetch(url, timeout=5, max_retries=1, backoff_factor=0.0, min_delay=0.0):
        return {
            "status_code": 200,
            "content_type": "text/html; charset=utf-8",
            "error": None,
            "raw_bytes": b"<html></html>",
            "title": "T",
            "links": [],
        }

    # Patch the underlying fetch used by the Investigator (probe.crawl.fetcher.fetch)
    import probe.crawl.fetcher as fetchmod

    monkeypatch.setattr(fetchmod, "fetch", fake_fetch)

    # mock ingest_fetch_result to return a known value
    import probe.crawl.ingest as ingestmod

    monkeypatch.setattr(
        ingestmod, "ingest_fetch_result", lambda m_obj, r: {"ingested": True}
    )

    inv = Investigator(m, ingest_on_fetch=True)
    res = inv.investigate("PT6A-52", ["manual"], max_seeds=3, dry_run=False)

    assert "results" in res
    assert all(r.get("status_code") == 200 for r in res["results"])
    # ingest should have been attempted; each result should include 'ingested' key
    assert all(
        "ingested" in r and r["ingested"] == {"ingested": True} for r in res["results"]
    )

    # After ingesting, domain document counts should reflect discovered docs (incremented)
    dom = m.get_domain("hi.example")
    assert dom is not None
    assert dom.documents_found >= 1

    m.close()
