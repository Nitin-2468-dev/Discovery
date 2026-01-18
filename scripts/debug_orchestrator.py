from probe.orchestrator import Orchestrator
from probe.analysis.gaps import GapDetector
from probe.analysis.seed_generator import SeedGenerator
from probe.core.map import Map, Document


def fake_fetch(url):
    return {"url": url, "status_code": 200, "text": "page", "links": [], "content_type": "text/html"}


def run_debug():
    m = Map(':memory:')
    # seed doc
    m.add_document(Document(id=None, title="RTL8111 Datasheet", doc_type="driver", hash="h1", url="https://drivers.example.com/rtl8111.pdf", domain="drivers.example.com"))

    gd = GapDetector(m)
    sg = SeedGenerator(m, fetch_remote=False)
    orc = Orchestrator(map_obj=m, fetch_fn=fake_fetch, scorer_fn=lambda r: 1.0)

    res = orc.orchestrate_gap_seed(entity_name="rtl8111", desired_doc_types=["driver"], gap_detector=gd, seed_generator=sg, max_seeds=10, max_depth=1, max_pages=10)

    print('res:', res)
    print('pages_fetched:', res['crawl_result']['pages_fetched'])
    print('pages rows:', list(m.conn.execute('SELECT url, domain FROM pages').fetchall()))
    print('documents rows:', list(m.conn.execute('SELECT url, domain FROM documents').fetchall()))
    print('domains rows:', list(m.conn.execute('SELECT domain_name, pages_crawled, documents_found FROM domains').fetchall()))


if __name__ == '__main__':
    run_debug()
