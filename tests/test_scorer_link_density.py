from probe.crawl.scorer import LinkDensityScorer


def test_link_density_internal_high():
    page = {
        'domain': 'example.com',
        'links': [
            {'url': 'https://example.com/a'},
            {'url': 'https://example.com/b'},
            {'url': 'https://external.com/x'},
        ]
    }
    s = LinkDensityScorer()
    score = s.score(page)
    assert 0.66 <= score <= 1.0  # 2/3 internal


def test_link_density_external_high():
    page = {
        'domain': 'example.com',
        'links': [
            {'url': 'https://external.com/a'},
            {'url': 'https://other.com/b'},
            {'url': 'https://external.com/x'},
        ]
    }
    s = LinkDensityScorer()
    score = s.score(page)
    assert 0.0 <= score <= 0.34  # 0/3 internal


def test_link_density_no_links():
    page = {'domain': 'example.com', 'links': []}
    s = LinkDensityScorer()
    assert s.score(page) == 0.0