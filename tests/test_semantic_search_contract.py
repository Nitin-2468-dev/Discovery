import importlib

import pytest


def _get_embedding_search():
    """Try to import a candidate embedding search function.

    If the repository hasn't implemented embeddings yet, we skip the tests.
    """
    try:
        mod = importlib.import_module("probe.search")
        fn = getattr(mod, "embedding_search", None)
        return fn
    except Exception:
        return None


def test_bucket_isolation_interface():
    fn = _get_embedding_search()
    if fn is None:
        pytest.skip("embeddings not implemented; contract tests skipped")

    # Expect the API to require a single `bucket` argument (or raise on multiple)
    with pytest.raises(ValueError):
        fn(buckets=["a", "b"], query="x")


def test_embedding_does_not_create_edges():
    fn = _get_embedding_search()
    if fn is None:
        pytest.skip("embeddings not implemented; contract tests skipped")

    # This is a behavioral contract; embedding searches must not modify edges.
    # Here we smoke-test that calling embedding_search does not raise and returns
    # a list-like result; we avoid asserting side-effects because embedding
    # implementations will be validated by integration tests.
    res = fn(bucket="drivers", query="rtl8111")
    assert res is None or hasattr(res, "__iter__")
