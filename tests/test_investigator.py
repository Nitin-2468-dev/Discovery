from probe.core.map import Map, Entity
from probe.analysis.investigator import Investigator


def test_investigator_dry_run_gathers_seeds(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    # create entity with no docs
    ent_id = m.add_entity(Entity(id=None, name="PT6A-52"))

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


def test_investigator_runs_fetches_when_not_dry(tmp_path, monkeypatch):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    ent_id = m.add_entity(Entity(id=None, name="PT6A-52"))

    # Add domain so seed generator makes seeds
    for _ in range(3):
        m.update_domain_stats("hi.example", found_document=True)

    # Mock fetch to avoid network
    def fake_fetch(url, timeout=5, max_retries=1, backoff_factor=0.0, min_delay=0.0):
        return {"status_code": 200, "content_type": "text/html; charset=utf-8", "error": None}

    # Patch the underlying fetch used by the Investigator (probe.crawl.fetcher.fetch)
    import probe.crawl.fetcher as fetchmod
    monkeypatch.setattr(fetchmod, 'fetch', fake_fetch)

    inv = Investigator(m)
    res = inv.investigate("PT6A-52", ["manual"], max_seeds=3, dry_run=False)

    assert "results" in res
    assert all(r.get("status_code") == 200 for r in res["results"])

    m.close()