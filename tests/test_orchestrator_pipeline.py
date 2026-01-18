from probe.orchestrator import Orchestrator, BreadthFirstCrawler


class DummyGapDetector:
    def analyze_entity_gaps(self, entity_name, desired_doc_types):
        return {"suggested_domains": ["example.com", "drivers.example.com"]}


class DummySeedGenerator:
    def generate_seeds(self, domains, doc_types, per_domain=3, max_seeds=None, **kwargs):
        out = []
        for d in domains:
            out.append(f"https://{d}/")
        return out


def fake_fetch(url):
    # simple fetcher that returns OK, no links
    return {"url": url, "status_code": 200, "text": "page", "links": [], "content_type": "text/html"}


def test_orchestrate_gap_seed_basic():
    # Orchestrator using a BreadthFirstCrawler with a fake fetcher
    orc = Orchestrator(map_obj=None, fetch_fn=fake_fetch, scorer_fn=lambda r: 1.0)
    gd = DummyGapDetector()
    sg = DummySeedGenerator()

    res = orc.orchestrate_gap_seed(
        entity_name="rtl8111",
        desired_doc_types=["driver"],
        gap_detector=gd,
        seed_generator=sg,
        max_seeds=10,
        max_depth=1,
        max_pages=10,
    )

    assert isinstance(res, dict)
    assert "seeds" in res and isinstance(res["seeds"], list)
    assert res["seeds"]
    assert res["crawl_result"]["pages_fetched"] >= 1
