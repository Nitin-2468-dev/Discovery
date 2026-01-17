from probe.crawl.scorer import (BoilerplateDetector, KeywordDensityScorer,
                                RelevanceScorer)


def test_keyword_density_and_boilerplate_combination():
    text = "This is a maintenance manual. The manual explains maintenance steps for the device."
    page = {
        "text": text,
        "boilerplate_ratio": 0.0,
        "metadata": {"keywords": ["manual", "maintenance"]},
    }

    kws = KeywordDensityScorer(keywords=["manual", "maintenance"], weight=1.0)
    bp = BoilerplateDetector(weight=1.0)
    scorer = RelevanceScorer(components=[kws, bp])

    comps = scorer.score_components(page)
    total = scorer.score(page)

    assert "KeywordDensityScorer" in comps
    assert "BoilerplateDetector" in comps
    assert 0.0 <= comps["KeywordDensityScorer"] <= 1.0
    assert 0.0 <= comps["BoilerplateDetector"] <= 1.0
    assert 0.0 <= total <= 1.0


def test_empty_text_scores_low():
    page = {"text": "", "boilerplate_ratio": 0.6}
    kws = KeywordDensityScorer(keywords=["manual"], weight=1.0)
    bp = BoilerplateDetector(weight=1.0)
    scorer = RelevanceScorer(components=[kws, bp])

    total = scorer.score(page)
    assert 0.0 <= total <= 1.0
    # with high boilerplate and no text, score should be low
    assert total < 0.6
