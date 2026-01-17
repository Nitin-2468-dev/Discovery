import os
import shutil
import sys

import pytest
from click.testing import CliRunner

from probe.visualization.graph_viz import GraphVisualizer
from probe.core.map import Map
from cli import cli


def test_plot_interactive_creates_html(tmp_path, sample_db):
    # Copy session DB to a test-local file
<<<<<<< HEAD
    db = shutil.copy(sample_db, str(tmp_path / "probe.db"))
=======
    db = shutil.copy(sample_db, str(tmp_path / 'probe.db'))
>>>>>>> ci/parallel-tests
    m = Map(db)
    viz = GraphVisualizer(m)
    viz.build_graph(entity_name="PT6A-52", depth=1)

    out = str(tmp_path / "graph_test.html")
    viz.plot_interactive(out)
    assert os.path.exists(out)
<<<<<<< HEAD
    content = open(out, "r", encoding="utf-8").read()
    assert "PT6A-52" in content or "PT6A-52 Maintenance Manual" in content
=======
    content = open(out, 'r', encoding='utf-8').read()
    assert 'PT6A-52' in content or 'PT6A-52 Maintenance Manual' in content
>>>>>>> ci/parallel-tests
    m.close()


def test_export_image_uses_kaleido(tmp_path, sample_db):
<<<<<<< HEAD
    db = shutil.copy(sample_db, str(tmp_path / "probe.db"))
=======
    db = shutil.copy(sample_db, str(tmp_path / 'probe.db'))
>>>>>>> ci/parallel-tests
    m = Map(db)
    viz = GraphVisualizer(m)
    viz.build_graph(entity_name="PT6A-52", depth=1)

    # Ensure _last_fig exists
    class FakeFig:
        def write_image(self, path):
<<<<<<< HEAD
            with open(path, "wb") as fh:
=======
            with open(path, 'wb') as fh:
>>>>>>> ci/parallel-tests
                fh.write(b"PNGDATA")

    viz._last_fig = FakeFig()

    # Fake kaleido module presence
<<<<<<< HEAD
    sys.modules["kaleido"] = type("K", (), {})()

    out_png = str(tmp_path / "plot.png")
=======
    sys.modules['kaleido'] = type('K', (), {})()

    out_png = str(tmp_path / 'plot.png')
>>>>>>> ci/parallel-tests
    res = viz.export_image(out_png)
    assert res == out_png
    assert os.path.exists(out_png)

    # cleanup
<<<<<<< HEAD
    del sys.modules["kaleido"]
=======
    del sys.modules['kaleido']
>>>>>>> ci/parallel-tests
    m.close()


def test_cli_export_flags(tmp_path, sample_db, monkeypatch):
<<<<<<< HEAD
    db = shutil.copy(sample_db, str(tmp_path / "probe.db"))

    # Fake GraphVisualizer.export_image to avoid needing kaleido in CI
    def fake_export(self, path):
        with open(path, "wb") as fh:
            fh.write(b"DUMMY")
        return path

    # Patch the concrete GraphVisualizer class used by the CLI
    monkeypatch.setattr(
        "probe.visualization.graph_viz.GraphVisualizer.export_image", fake_export
    )

    runner = CliRunner()
    out_html = tmp_path / "out.html"
    out_png = tmp_path / "out.png"
    res = runner.invoke(
        cli,
        [
            "visualize",
            "--entity",
            "PT6A-52",
            "--db",
            db,
            "--output",
            str(out_html),
            "--export-png",
            str(out_png),
        ],
    )
=======
    db = shutil.copy(sample_db, str(tmp_path / 'probe.db'))

    # Fake GraphVisualizer.export_image to avoid needing kaleido in CI
    def fake_export(self, path):
        with open(path, 'wb') as fh:
            fh.write(b'DUMMY')
        return path

    # Patch the concrete GraphVisualizer class used by the CLI
    monkeypatch.setattr('probe.visualization.graph_viz.GraphVisualizer.export_image', fake_export)

    runner = CliRunner()
    out_html = tmp_path / 'out.html'
    out_png = tmp_path / 'out.png'
    res = runner.invoke(cli, ['visualize', '--entity', 'PT6A-52', '--db', db, '--output', str(out_html), '--export-png', str(out_png)])
>>>>>>> ci/parallel-tests
    assert res.exit_code == 0
    assert os.path.exists(out_html)
    assert os.path.exists(out_png)


@pytest.mark.slow
def test_visualize_run_integration(tmp_path, sample_db):
    # Simulates running visualize_run on a small run directory
<<<<<<< HEAD
    run_dir = tmp_path / "run1"
    run_dir.mkdir()
    # copy db into run dir
    shutil.copy(sample_db, str(run_dir / "probe.db"))

    # create a tiny analysis.json with suggestions
    analysis = {"suggested_entities": [{"name": "PT6A-52"}]}
    with open(run_dir / "analysis.json", "w", encoding="utf-8") as fh:
=======
    run_dir = tmp_path / 'run1'
    run_dir.mkdir()
    # copy db into run dir
    shutil.copy(sample_db, str(run_dir / 'probe.db'))

    # create a tiny analysis.json with suggestions
    analysis = {'suggested_entities': [{'name': 'PT6A-52'}]}
    with open(run_dir / 'analysis.json', 'w', encoding='utf-8') as fh:
>>>>>>> ci/parallel-tests
        import json

        json.dump(analysis, fh)

<<<<<<< HEAD
    outdir = run_dir / "visualizations"
=======
    outdir = run_dir / 'visualizations'
>>>>>>> ci/parallel-tests
    outdir.mkdir()

    # run the script
    from scripts.visualize_run import main as vr_main

    # emulate CLI args
    argv = sys.argv
    try:
<<<<<<< HEAD
        sys.argv = [
            "scripts/visualize_run.py",
            "--run",
            str(run_dir),
            "--top",
            "1",
            "--outdir",
            str(outdir),
        ]
=======
        sys.argv = ['scripts/visualize_run.py', '--run', str(run_dir), '--top', '1', '--outdir', str(outdir)]
>>>>>>> ci/parallel-tests
        vr_main()
    finally:
        sys.argv = argv

    # expect a file created
<<<<<<< HEAD
    files = list(outdir.glob("*.html"))
=======
    files = list(outdir.glob('*.html'))
>>>>>>> ci/parallel-tests
    assert len(files) >= 1
