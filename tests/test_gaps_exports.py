def test_gaps_exports():
    import importlib
    try:
        m = importlib.import_module('probe.analysis.gaps')
    except Exception as e:
        raise AssertionError(f"Failed to import probe.analysis.gaps: {e}")

    members = [n for n in dir(m) if not n.startswith('_')]
    assert 'GapDetector' in members, f"GapDetector not exported; module members: {members}"
