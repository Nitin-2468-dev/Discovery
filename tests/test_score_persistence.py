import json
from probe.core.map import Map
from probe.crawl.scorer import RelevanceScorer, KeywordDensityScorer, BoilerplateDetector


def test_persist_scoring_report(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    # simulate a pre-existing page with metadata text
    page = {
        'url': 'https://example.com/test',
        'domain': 'example.com',
        'title': 'Test',
        'content_hash': 'abc',
        'metadata': {'text': 'manual maintenance manual', 'boilerplate_ratio': 0.0}
    }
    # add page (use Page dataclass)
    from probe.core.map import Page
    p = Page(id=None, url=page['url'], domain=page['domain'], title=page['title'], content_hash=page['content_hash'], metadata=page['metadata'])
    pid = m.add_page(p)

    # create components and score
    components = {'KeywordDensityScorer': 1.0, 'BoilerplateDetector': 1.0}
    total = 1.0

    report_id = m.add_scoring_report(pid, page['url'], total, components, {'keywords': ['manual']})
    assert isinstance(report_id, int)

    # fetch reports for page
    rows = m.get_scoring_reports_for_page(pid)
    assert len(rows) >= 1
    r = rows[0]
    assert r['page_id'] == pid
    assert float(r['score']) == total
    comps = json.loads(r['components'])
    assert 'KeywordDensityScorer' in comps

    # latest by url
    latest = m.get_latest_scoring_report_for_url(page['url'])
    assert latest is not None
    assert latest['url'] == page['url']

    m.close()