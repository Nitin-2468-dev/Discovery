import shutil
import os
import pytest
from probe.core.map import Map, Entity, Document, Page, Edge


@pytest.fixture(scope="session")
def sample_db(tmp_path_factory):
    """Create a small sample DB once per test session and return its path.

    Tests that need a writable DB should copy this file using the
    `copy_db_for_test` helper below so workers don't contend on a single DB file.
    """
    d = tmp_path_factory.mktemp("visual_db")
    db_path = d / "probe.db"
    m = Map(str(db_path))

    # add minimal sample data
    e = Entity(id=None, name="PT6A-52", type="engine")
    e_id = m.add_entity(e)
    d1 = Document(id=None, title="PT6A-52 Maintenance Manual", doc_type="manual", hash="h1", url="https://example.com/manual.pdf", domain="example.com")
    d_id = m.add_document(d1)
    p = Page(id=None, url="https://example.com/manual.html", domain="example.com", title="Manual page")
    p_id = m.add_page(p)
    m.add_edge(Edge(id=None, from_type="entity", from_id=e_id, to_type="document", to_id=d_id, relation="has_document"))
    m.add_edge(Edge(id=None, from_type="page", from_id=p_id, to_type="entity", to_id=e_id, relation="mentions"))
    m.update_domain_stats("example.com", found_document=True)
    m.close()

    return str(db_path)


def copy_db_for_test(sample_db, tmp_path):
    """Copy the session DB into a test-local writable file and return its path.

    If running under pytest-xdist, include the worker id in the filename to avoid clashes.
    """
    base = tmp_path / "probe.db"
    # If running under xdist, use the worker id to create per-worker file
    worker = os.environ.get("PYTEST_XDIST_WORKER", None)
    if worker:
        base = tmp_path / f"probe_{worker}.db"
    shutil.copy(sample_db, str(base))
    return str(base)
