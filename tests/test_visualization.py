<<<<<<< HEAD
import os

from click.testing import CliRunner

from cli import cli
from probe.core.map import Entity, Map
=======
from click.testing import CliRunner
import os
from cli import cli
from probe.core.map import Map, Entity
>>>>>>> ci/parallel-tests


def test_cli_visualize_writes_html(tmp_path, monkeypatch):
    db = str(tmp_path / "probe.db")
    m = Map(db)

    # Add an entity to the database
    e = Entity(id=None, name="PT6A-52", type="engine")
    m.add_entity(e)
    m.close()

    runner = CliRunner()

    # Fake visualizer to avoid heavy plotting dependencies
    class FakeVisualizer:
        def __init__(self, map_obj):
            self.map = map_obj
            self._built = False

        def build_graph(self, entity_name=None, depth=2):
            self._built = True

        def get_stats(self):
            return {"nodes": 1, "edges": 0}

        def plot_interactive(self, output_path="graph.html"):
            # write a minimal HTML file to simulate output
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write("<html><body>fake graph</body></html>")
            return output_path

    monkeypatch.setattr("cli.GraphVisualizer", FakeVisualizer)

    out_file = tmp_path / "out.html"
<<<<<<< HEAD
    res = runner.invoke(
        cli, ["visualize", "--entity", "PT6A-52", "--db", db, "--output", str(out_file)]
    )
=======
    res = runner.invoke(cli, ["visualize", "--entity", "PT6A-52", "--db", db, "--output", str(out_file)])
>>>>>>> ci/parallel-tests
    assert res.exit_code == 0
    assert "Visualization saved to" in res.output
    assert os.path.exists(out_file)
