from probe.crawl.scorer import EntityRegexScorer, RelevanceScorer, KeywordDensityScorer


def test_entity_regex_single_pattern():
    text = "This manual mentions the PT6A-52 engine in detail."
    page = {"text": text}
    s = EntityRegexScorer(patterns=[r"PT6A-52"], weight=1.0)
    assert s.score(page) == 1.0


def test_entity_regex_no_match():
    page = {"text": "No relevant content here."}
    s = EntityRegexScorer(patterns=[r"PT6A-52"], weight=1.0)
    assert s.score(page) == 0.0


def test_entity_regex_multiple_patterns_ratio():
    text = "The manual mentions PT6A-52 and also maintenance procedures."
    page = {"text": text}
    s = EntityRegexScorer(
        patterns=[r"PT6A-52", r"maintenance", r"nonexistent"], weight=1.0
    )
    # 2 of 3 patterns -> score ~0.666...
    score = s.score(page)
    assert 0.65 <= score <= 0.68


def test_entity_regex_in_composite_scorer():
    text = "PT6A-52 maintenance manual"
    page = {"text": text, "boilerplate_ratio": 0.0}
    entity = EntityRegexScorer(patterns=[r"PT6A-52"], weight=1.0)
    kw = KeywordDensityScorer(keywords=["manual"], weight=1.0)
    scorer = RelevanceScorer(components=[entity, kw])
    comps = scorer.score_components(page)
    total = scorer.score(page)
    assert "EntityRegexScorer" in comps
    assert 0.0 <= total <= 1.0
