from probe.analysis.investigator import Investigator
from probe.core.map import Entity, Map
from probe.policy import Mode, PolicyEngine


def test_investigator_skips_policy_denied_seed(tmp_path, monkeypatch):
    db = str(tmp_path / "probe.db")
    m = Map(db)
    m.add_entity(Entity(id=None, name="TestEnt"))

    # Force seed generator to produce a deny-listed domain seed
    def fake_generate_seeds(self, domains, types, per_domain=1):
        return ["http://malicious.example/doc.pdf"]

    monkeypatch.setattr(
        "probe.analysis.seed_generator.SeedGenerator.generate_seeds",
        fake_generate_seeds,
    )

    # Default PolicyEngine is PUBLIC_GUARDED and denies 'malicious.example'
    pe = PolicyEngine(mode=Mode.PUBLIC_GUARDED)
    inv = Investigator(m, policy_engine=pe)

    res = inv.investigate("TestEnt", ["manual"], max_seeds=1, dry_run=False)

    # Should have a results entry indicating policy denial
    assert "results" in res
    assert len(res["results"]) == 1
    r = res["results"][0]
    assert r["error"] == "policy_denied"
    assert "malicious.example" in r.get("reason", "")

    m.close()


def test_investigator_allows_in_educational_with_admin(tmp_path, monkeypatch):
    db = str(tmp_path / "probe.db")
    m = Map(db)
    m.add_entity(Entity(id=None, name="TestEnt"))

    def fake_generate_seeds(self, domains, types, per_domain=1):
        return ["http://malicious.example/doc.pdf"]

    monkeypatch.setattr(
        "probe.analysis.seed_generator.SeedGenerator.generate_seeds",
        fake_generate_seeds,
    )

    # PolicyEngine in educational mode with admin enabled allows the domain
    pe = PolicyEngine(mode=Mode.EDUCATIONAL_OPEN, admin_enabled=True)

    # Mock fetch to return a 200 payload
    def fake_fetch(url, timeout=5, max_retries=1, backoff_factor=0.0):
        return {"status_code": 200, "error": None}

    import probe.crawl.fetcher as fetchmod

    monkeypatch.setattr(fetchmod, "fetch", fake_fetch)

    inv = Investigator(m, ingest_on_fetch=False, policy_engine=pe)
    res = inv.investigate("TestEnt", ["manual"], max_seeds=1, dry_run=False)

    assert "results" in res
    assert len(res["results"]) == 1
    r = res["results"][0]
    assert r.get("status_code") == 200

    m.close()
