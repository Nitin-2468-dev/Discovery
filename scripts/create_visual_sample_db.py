import os

from probe.core.map import Document, Edge, Entity, Map, Page

out_dir = "results/visualization-sample"
os.makedirs(out_dir, exist_ok=True)

db = os.path.join(out_dir, "probe.db")
print("Creating DB at:", db)

m = Map(db)

# Add entity
ent = Entity(id=None, name="PT6A-52", type="engine", confidence_score=0.75)
ent_id = m.add_entity(ent)
print("Added entity id", ent_id)

# Add a document
doc = Document(
    id=None,
    title="PT6A-52 Maintenance Manual",
    doc_type="manual",
    hash="hash1",
    url="https://example.com/manual.pdf",
    domain="example.com",
)
doc_id = m.add_document(doc)
print("Added doc id", doc_id)

# Add a page
page = Page(
    id=None,
    url="https://example.com/manual.html",
    domain="example.com",
    title="Manual page",
)
page_id = m.add_page(page)
print("Added page id", page_id)

# Add edges: entity -> document, page -> entity
edge1 = Edge(
    id=None,
    from_type="entity",
    from_id=ent_id,
    to_type="document",
    to_id=doc_id,
    relation="has_document",
)
edge2 = Edge(
    id=None,
    from_type="page",
    from_id=page_id,
    to_type="entity",
    to_id=ent_id,
    relation="mentions",
)

m.add_edge(edge1)
m.add_edge(edge2)

# Update domain stats to get domain entries
m.update_domain_stats("example.com", found_document=True)

m.close()
print("Sample DB ready")
