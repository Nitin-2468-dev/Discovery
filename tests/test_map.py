from probe.core.map import Entity, Map


def test_add_and_get_entity(tmp_path):
    db = str(tmp_path / "probe.db")

    m = Map(db)

    entity = Entity(id=None, name="PT6A-52", type="engine")
    entity_id = m.add_entity(entity)

    assert isinstance(entity_id, int) and entity_id > 0

    fetched = m.get_entity("PT6A-52")
    assert fetched is not None
    assert fetched.id == entity_id
    assert fetched.name == "PT6A-52"
    assert fetched.type == "engine"

    m.close()
