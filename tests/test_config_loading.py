from probe.config import load_config


def test_load_json_config(tmp_path):
    cfgp = tmp_path / "probe.config.json"
    cfgp.write_text(
        '{"concurrency": 3, "per_domain_delay": 0.5, "scorer_weights": {"keyword_density": 2.0}}'
    )

    cfg = load_config(str(cfgp))
    assert cfg["concurrency"] == 3
    assert cfg["per_domain_delay"] == 0.5
    assert cfg["scorer_weights"]["keyword_density"] == 2.0


def test_load_yaml_config(tmp_path, monkeypatch):
    # If PyYAML present, loader should read YAML. If absent, load_config should return defaults when path given.
    cfgp = tmp_path / "probe.config.yaml"
    cfgp.write_text(
        "concurrency: 4\nmin_delay: 0.1\nscorer_weights:\n  link_density: 0.5\n"
    )

    try:
        import yaml  # type: ignore  # noqa: F401

        cfg = load_config(str(cfgp))
        assert cfg["concurrency"] == 4
        assert cfg["min_delay"] == 0.1
        assert cfg["scorer_weights"]["link_density"] == 0.5
    except Exception:
        # PyYAML not installed: load_config should return defaults when YAML path is passed
        cfg = load_config(str(cfgp))
        assert cfg["concurrency"] == 1


def test_load_defaults_when_no_file():
    cfg = load_config(None)
    assert cfg["concurrency"] == 1
    assert "scorer_weights" in cfg
