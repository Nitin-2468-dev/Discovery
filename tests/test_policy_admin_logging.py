import logging

from probe.policy import Mode, PolicyEngine


def test_educational_mode_permissive_by_default(caplog):
    caplog.set_level(logging.WARNING)
    engine = PolicyEngine(mode=Mode.educational_open, admin_enabled=False)

    allowed = engine.domain_allowed("malicious.example")
    assert allowed is True

    # No warning should be emitted for permissive EDUCATIONAL_OPEN domain checks
    assert not any(
        "Educational mode requested" in rec.message for rec in caplog.records
    )


def test_evaluate_query_logs_denial(caplog):
    caplog.set_level(logging.WARNING)
    engine = PolicyEngine(mode=Mode.PUBLIC_GUARDED)

    decision = engine.evaluate_query("fetch", context={"domain": "malicious.example"})
    assert decision["allowed"] is False

    assert any("Policy decision denied" in rec.message for rec in caplog.records)
