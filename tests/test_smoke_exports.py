def test_smoke_exports():
    import importlib
    import inspect

    # gaps -> GapDetector
    try:
        gaps = importlib.import_module("probe.analysis.gaps")
    except Exception as e:
        raise AssertionError(f"Failed to import probe.analysis.gaps: {e}")
    assert hasattr(
        gaps, "GapDetector"
    ), f"GapDetector not found in probe.analysis.gaps: {dir(gaps)}"
    assert inspect.isclass(getattr(gaps, "GapDetector"))

    # seed_generator -> SeedGenerator
    try:
        sg = importlib.import_module("probe.analysis.seed_generator")
    except Exception as e:
        raise AssertionError(f"Failed to import probe.analysis.seed_generator: {e}")
    assert hasattr(sg, "SeedGenerator"), f"SeedGenerator not found: {dir(sg)}"
    assert inspect.isclass(getattr(sg, "SeedGenerator"))

    # investigator imports without raising
    try:
        inv = importlib.import_module("probe.analysis.investigator")
    except Exception as e:
        raise AssertionError(f"Failed to import probe.analysis.investigator: {e}")
    # Investigator should be a class in the module
    assert hasattr(inv, "Investigator") and inspect.isclass(
        getattr(inv, "Investigator")
    )
