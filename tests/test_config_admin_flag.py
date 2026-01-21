import json
import os

from click.testing import CliRunner

from cli import cli
from probe.config import load_config


def test_config_default_has_admin_flag():
    cfg = load_config()
    assert "admin_enabled" in cfg
    assert cfg["admin_enabled"] is False


def test_config_set_admin_writes_file(tmp_path):
    runner = CliRunner()
    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        # Ensure no config file exists initially
        r = runner.invoke(cli, ["config", "set-admin", "enable"])
        assert r.exit_code == 0
        p = tmp_path / "probe.config.json"
        assert p.exists()
        data = json.loads(p.read_text(encoding="utf-8"))
        assert data.get("admin_enabled") is True

        # Show command should reflect the value
        r2 = runner.invoke(cli, ["config", "show"])
        assert r2.exit_code == 0
        shown = json.loads(r2.output)
        assert shown.get("admin_enabled") is True
    finally:
        os.chdir(cwd)
