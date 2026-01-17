import os

import pytest

from probe.core.map import Map


@pytest.mark.slow
def test_investigator_integration_real_network(tmp_path):
    if os.environ.get("RUN_REAL_NET_TESTS", "") != "true":
        pytest.skip("Real network tests are opt-in via RUN_REAL_NET_TESTS=true")

    # Small smoke: run investigation for a known domain/entity and ensure function returns structure.
    db = str(tmp_path / "probe.db")
    m = Map(db)
    inv = None
    try:
        from probe.analysis.investigator import Investigator

        inv = Investigator(m)
        res = inv.investigate("Example", ["manual"], max_seeds=5, dry_run=False)
        assert isinstance(res, dict)
        assert "seeds" in res
    finally:
        m.close()
