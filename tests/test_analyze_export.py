import json
from probe.core.map import Map
from probe.crawl.reporting import write_scoring_export
from pathlib import Path


def test_write_scoring_export_csv_and_md(tmp_path):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    # Create a page and two scoring reports
    from probe.core.map import Page
    p = Page(id=None, url='https://example.com/x', domain='example.com', title='X', content_hash='h', metadata={'text':'manual text'})
    pid = m.add_page(p)

    comps = {'KeywordDensityScorer': 1.0, 'BoilerplateDetector': 1.0}
    r1 = m.add_scoring_report(pid, 'https://example.com/x', 0.9, comps, {'keywords': ['manual']})
    r2 = m.add_scoring_report(pid, 'https://example.com/x', 0.6, comps, {'keywords': ['manual']})

    rows = m.get_scoring_reports(page_id=pid)
    assert len(rows) >= 2

    # Convert rows to dicts like the exporter expects
    out_rows = []
    for r in rows:
        out_rows.append({'id': r['id'], 'page_id': r['page_id'], 'url': r['url'], 'score': r['score'], 'components': json.loads(r['components']) if r['components'] else {}, 'metadata': r['metadata'], 'created_at': r['created_at'], 'top_component': ''})

    csvp = write_scoring_export(out_rows, file_path=Path(tmp_path / 'out.csv'), fmt='csv')
    assert csvp.exists()

    mdp = write_scoring_export(out_rows, file_path=Path(tmp_path / 'out.md'), fmt='md')
    assert mdp.exists()
    md = mdp.read_text(encoding='utf-8')
    assert 'Average score' in md

    m.close()