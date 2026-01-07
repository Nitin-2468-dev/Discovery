from click.testing import CliRunner
from cli import cli


def test_cli_init_add_show_summary(tmp_path):
    db = str(tmp_path / "probe.db")
    runner = CliRunner()

    # Initialize
    res = runner.invoke(cli, ["init", "--db", db])
    assert res.exit_code == 0
    assert "Database initialized successfully" in res.output

    # Add entity
    res = runner.invoke(cli, ["add-entity", "PT6A-52", "--type", "engine", "--db", db])
    assert res.exit_code == 0
    assert "Added entity 'PT6A-52'" in res.output
    assert "Type: engine" in res.output or "Type: engine)" in res.output

    # Show entity
    res = runner.invoke(cli, ["show", "PT6A-52", "--db", db])
    assert res.exit_code == 0
    assert "Entity: PT6A-52" in res.output

    # Summary
    res = runner.invoke(cli, ["summary", "--db", db])
    assert res.exit_code == 0
    assert "Entities:" in res.output
    assert "1" in res.output
