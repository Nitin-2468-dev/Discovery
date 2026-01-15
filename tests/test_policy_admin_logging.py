import logging

from probe.policy import Mode, PolicyEngine


def test_educational_mode_requires_admin_opt_in(caplog):
    caplog.set_level(logging.WARNING)
    engine = PolicyEngine(mode=Mode.educational_open, admin_enabled=False)

    allowed = engine.domain_allowed("malicious.example")
    assert allowed is False

    assert any("Educational mode requested" in rec.message for rec in caplog.records)


def test_evaluate_query_logs_denial(caplog):
    caplog.set_level(logging.WARNING)
    engine = PolicyEngine(mode=Mode.PUBLIC_GUARDED)

    decision = engine.evaluate_query("fetch", context={"domain": "malicious.example"})
    assert decision["allowed"] is False

    assert any("Policy decision denied" in rec.message for rec in caplog.records)
