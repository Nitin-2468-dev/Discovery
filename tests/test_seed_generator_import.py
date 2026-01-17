def test_seed_generator_import_without_httpx(monkeypatch):
    """Ensure the seed_generator module imports cleanly even if `httpx` is not installed."""
    import sys

    # Simulate httpx not installed
    monkeypatch.setitem(sys.modules, "httpx", None)

    # Ensure a fresh import of the module under test
    if "probe.analysis.seed_generator" in sys.modules:
        del sys.modules["probe.analysis.seed_generator"]

    # Import should succeed and expose SeedGenerator
    import probe.analysis.seed_generator as sg

    assert hasattr(sg, "SeedGenerator")
