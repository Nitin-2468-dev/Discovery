import os
import shutil
import sys

import pytest
from click.testing import CliRunner

from cli import cli
from probe.core.map import Map
from probe.visualization.graph_viz import GraphVisualizer


def test_plot_interactive_creates_html(tmp_path, sample_db):
    # Copy session DB to a test-local file
    db = shutil.copy(sample_db, str(tmp_path / "probe.db"))
    m = Map(db)
    viz = GraphVisualizer(m)
    viz.build_graph(entity_name="PT6A-52", depth=1)

    out = str(tmp_path / "graph_test.html")
    viz.plot_interactive(out)
    assert os.path.exists(out)
    content = open(out, "r", encoding="utf-8").read()
    assert "PT6A-52" in content or "PT6A-52 Maintenance Manual" in content
    m.close()


def test_export_image_uses_kaleido(tmp_path, sample_db):
    db = shutil.copy(sample_db, str(tmp_path / "probe.db"))
    m = Map(db)
    viz = GraphVisualizer(m)
    viz.build_graph(entity_name="PT6A-52", depth=1)

    # Ensure _last_fig exists
    class FakeFig:
        def write_image(self, path):
            with open(path, "wb") as fh:
                fh.write(b"PNGDATA")

    viz._last_fig = FakeFig()

    # Fake kaleido module presence
    sys.modules["kaleido"] = type("K", (), {})()

    out_png = str(tmp_path / "plot.png")
    res = viz.export_image(out_png)
    assert res == out_png
    assert os.path.exists(out_png)

    # cleanup
    del sys.modules["kaleido"]
    m.close()


def test_cli_export_flags(tmp_path, sample_db, monkeypatch):
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
    assert res.exit_code == 0
    assert os.path.exists(out_html)
    assert os.path.exists(out_png)


@pytest.mark.slow
def test_visualize_run_integration(tmp_path, sample_db):
    # Simulates running visualize_run on a small run directory
    run_dir = tmp_path / "run1"
    run_dir.mkdir()
    # copy db into run dir
    shutil.copy(sample_db, str(run_dir / "probe.db"))

    # create a tiny analysis.json with suggestions
    analysis = {"suggested_entities": [{"name": "PT6A-52"}]}
    with open(run_dir / "analysis.json", "w", encoding="utf-8") as fh:
        import json

        json.dump(analysis, fh)

    outdir = run_dir / "visualizations"
    outdir.mkdir()

    # run the script
    from scripts.visualize_run import main as vr_main

    # emulate CLI args
    argv = sys.argv
    try:
        sys.argv = [
            "scripts/visualize_run.py",
            "--run",
            str(run_dir),
            "--top",
            "1",
            "--outdir",
            str(outdir),
        ]
        vr_main()
    finally:
        sys.argv = argv

    # expect a file created
    files = list(outdir.glob("*.html"))
    assert len(files) >= 1
