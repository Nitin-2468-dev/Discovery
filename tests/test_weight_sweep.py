import csv
import subprocess
import sys
from pathlib import Path


def test_weight_sweep_cli(tmp_path):
    out = tmp_path / "out.csv"
    seeds = tmp_path / "seeds.txt"
    seeds.write_text("TEST-ENT\n")

    proc = subprocess.run(
        [sys.executable, "scripts/weight_sweep.py", "--seeds", str(seeds), "--types", "manual", "--out", str(out), "--weight-count", "1.0", "--weight-yield", "1.0", "--weight-trust", "0.5", "--weight-recent", "0.5", "--db", str(tmp_path / 'sweep.db')],
        check=False,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0
    assert out.exists()

    with open(out, newline='', encoding='utf-8') as fh:
        r = csv.DictReader(fh)
        rows = list(r)
    assert len(rows) >= 1
    # basic sanity check columns
    assert "entity" in rows[0]
    assert "top_domain" in rows[0]


def test_weight_sweep_normalization_prefers_density(tmp_path):
    # Create a small DB and use run_sweep programmatically to validate normalization effect
    from probe.core.map import Map, Document
    from scripts.weight_sweep import run_sweep

    db = str(tmp_path / "probe.db")
    m = Map(db)

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    # Create an entity and link a manual doc so GapDetector sees an existing entity
    from probe.core.map import Entity, Edge
    e = Entity(id=None, name="E1", type="device", confidence_score=0.6)
    e_id = m.add_entity(e)
    m.add_document(Document(id=None, title="Manual", doc_type="manual", hash="hm", url="https://ex/manual.pdf", domain="low.example.com"))
    m.add_edge(Edge(id=None, from_type="entity", from_id=e_id, to_type="document", to_id=1, relation="has_document"))

    # Domain A: many docs, many pages
    m.conn.execute("INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?,?,?,?,?,?)", ("a.example.com", 200, 100, 0.2, 0.5, now))
    for i in range(100):
        m.add_document(Document(id=None, title=f"A{i}", doc_type="datasheet", hash=f"ad{i}", url=f"https://a/{i}.pdf", domain="a.example.com"))

    # Domain B: few docs, few pages
    m.conn.execute("INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score, trust_score, last_crawled_at) VALUES (?,?,?,?,?,?)", ("b.example.com", 2, 5, 0.9, 0.9, now))
    for i in range(5):
        m.add_document(Document(id=None, title=f"B{i}", doc_type="datasheet", hash=f"bd{i}", url=f"https://b/{i}.pdf", domain="b.example.com"))

    m.conn.commit()

    out = tmp_path / "sweep2.csv"

    run_sweep(["E1"], ["datasheet"], db, str(out), counts=[1.0], yields=[0.0], trusts=[0.0], recents=[0.0], normalizes=["none", "per_page"])

    rows = list(csv.DictReader(open(out, newline='', encoding='utf-8')))
    norms = {r['normalize']: r for r in rows}
    assert 'none' in norms and 'per_page' in norms
    # For none: top domain might be a.example.com (higher raw counts)
    # For per_page: b.example.com should be favored due to higher density per page
    assert norms['per_page']['top_domain'] == 'b.example.com'

    m.close()
