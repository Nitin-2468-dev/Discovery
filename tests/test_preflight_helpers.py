def test_map_helper_attached_on_import():
    # Simple smoke test to ensure the compatibility helper is attached when importing probe.core
    from probe.core.map import Map

    # The Map class should expose `get_domains_with_doc_type` (either directly or via attached helper)
    assert hasattr(Map, "get_domains_with_doc_type")
