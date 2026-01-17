from probe.analysis.seed_generator import SeedGenerator
from probe.core.map import Map


def test_generate_seeds_high_yield_domains(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    # Populate domain stats: simulate a higher-yield domain (hi1) vs a slightly lower-yield one (hi2).
    # The exact counts are not important; only their relative frequency matters for the test.
    for _ in range(5):
        m.update_domain_stats("hi1.example", found_document=True)
    for _ in range(4):
        m.update_domain_stats("hi2.example", found_document=True)

    sg = SeedGenerator(m)
    seeds = sg.generate_seeds("PT6A-52", "manual", max_seeds=5)

    assert any("hi1.example" in s for s in seeds)
    assert any("hi2.example" in s for s in seeds)
    assert any("google.com" in s for s in seeds)

    # Respect max_seeds
    assert len(seeds) <= 5

    m.close()


def test_generate_seeds_related_entities_and_dedup(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    # Add entity and a related entity via edges
    from probe.core.map import Edge, Entity

    e1_id = m.add_entity(Entity(id=None, name="E1"))
    e2_id = m.add_entity(Entity(id=None, name="E2"))

    # Create an entity-to-entity edge (relation 'related')
    edge = Edge(
        id=None,
        from_type="entity",
        from_id=e1_id,
        to_type="entity",
        to_id=e2_id,
        relation="related",
    )
    m.add_edge(edge)

    sg = SeedGenerator(m)
    seeds = sg.generate_seeds("E1", "spec", max_seeds=10)

    # should include a google search for the related entity (E2)
    assert any("E2+spec" in s or "E2%20spec" in s for s in seeds)

    m.close()
