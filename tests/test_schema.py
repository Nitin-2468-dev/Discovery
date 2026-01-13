import sqlite3

from probe.core.schema import initialize_schema, validate_schema


def test_initialize_and_validate_schema(tmp_path):
    db = str(tmp_path / "probe.db")

    conn = initialize_schema(db)
    assert isinstance(conn, sqlite3.Connection)

    assert validate_schema(conn) is True

    conn.close()
