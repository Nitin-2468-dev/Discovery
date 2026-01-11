def test_investigator_imports():
    # Ensure importing the Investigator module does not raise an ImportError.
    from probe.analysis.investigator import Investigator
    assert Investigator is not None
