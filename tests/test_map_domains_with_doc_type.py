from probe.core.map import Document, Map


def test_get_domains_with_doc_type_orders_by_count_and_yield(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    # Add domains entries
    m.conn.execute(
        "INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score) VALUES (?, ?, ?, ?, ?)",
        ("a.example.com", 10, 2, 0.2, 0.5),
    )
    m.conn.execute(
        "INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score) VALUES (?, ?, ?, ?, ?)",
        ("b.example.com", 10, 1, 0.9, 0.9),
    )

    # Add documents: a has two datasheets, b has one datasheet
    d1 = Document(
        id=None,
        title="A1",
        doc_type="datasheet",
        hash="h1",
        url="https://a/1.pdf",
        domain="a.example.com",
    )
    d2 = Document(
        id=None,
        title="A2",
        doc_type="datasheet",
        hash="h2",
        url="https://a/2.pdf",
        domain="a.example.com",
    )
    d3 = Document(
        id=None,
        title="B1",
        doc_type="datasheet",
        hash="h3",
        url="https://b/1.pdf",
        domain="b.example.com",
    )
    m.add_document(d1)
    m.add_document(d2)
    m.add_document(d3)
    m.conn.commit()

    domains = m.get_domains_with_doc_type("datasheet", limit=5)
    assert domains[0].domain_name == "a.example.com"
    assert domains[1].domain_name == "b.example.com"

    m.close()
