import os
import pytest

# Opt-in real-network integration test: run only when RUN_REAL_NET_TESTS=true
pytestmark = pytest.mark.skipif(os.getenv("RUN_REAL_NET_TESTS", "false") != "true", reason="real-network tests are opt-in")

from probe.crawl.fetcher import fetch


def test_end_to_end_crawl_index_and_search_real():
    """Minimal real-network check: fetch example.org and make sure we get a 200 and text."""
    res = fetch("https://example.org", timeout=10)
    assert res["status_code"] == 200
    assert "text" in res and res["text"].strip()
