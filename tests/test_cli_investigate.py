import json
from click.testing import CliRunner
from cli import cli
from probe.core.map import Map, Document


def test_investigate_dry_run(tmp_path):
    db = str(tmp_path / "test.db")
    m = Map(db)
    # Seed with a known document domain so GapDetector will suggest it
    m.add_document(Document(id=None, title="RTL8111 Datasheet", doc_type="driver", hash="h1", url="https://drivers.example.com/rtl8111.pdf", domain="drivers.example.com"))
    m.close()

    runner = CliRunner()
    result = runner.invoke(cli, ["investigate", "rtl8111", "--types", "driver", "--db", db, "--json"])
    assert result.exit_code == 0
    out = json.loads(result.output)
    # Investigator returns keys: entity, gap, seeds, (optional) results
    assert out["entity"] == "rtl8111"
    assert "drivers.example.com" in out.get("gap", {}).get("suggested_domains", [])
    assert out.get("seeds") and len(out.get("seeds")) >= 1
